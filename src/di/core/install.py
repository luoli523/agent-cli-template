"""``di install`` — symlink skills into Claude Code and Codex.

Walks ``<repo>/skills/di-*/`` and creates one symlink per skill into each
target tool's skills directory (``~/.claude/skills/<name>`` and
``~/.codex/skills/<name>``).

Conflict policy — read these together:

* If a target path is already a symlink resolving into our source skills
  tree, install treats it as ours (idempotent skip, or rewrite when the
  symlink points at a stale source).
* If a target path is a real directory, a regular file, or a symlink
  pointing outside our source tree, it is *not* ours; install refuses to
  touch it and reports a conflict.
* When any conflict exists, install aborts the whole run without touching
  the filesystem. There is no partial-success mode — agents read a single
  exit code, and "some succeeded, some didn't" needs a per-target story
  the envelope cannot currently express. Re-running after the user fixes
  the conflict is the supported path.

The source location resolves in this order: ``DI_SKILLS_DIR`` env var →
walk up from ``di.__file__`` looking for a ``pyproject.toml`` sibling
with a ``skills/`` directory (editable / repo install). Wheel-bundled
skills are not handled here; that arrives with the packaging story in
T11/T12.

See docs/specs/2026-05-15-di-cli-architecture.md § Commands (install).
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from di.contracts import (
    ErrDetail,
    ErrorEnvelope,
    ErrorType,
    Envelope,
    ExitCode,
    RiskClass,
)
from di.manifest import CommandSpec, register
from di.runtime import LOCAL_IDENTITY, emit_error, emit_success

NAME = "install"
SUMMARY = "Install di-cli skills into Claude Code and Codex"

SKILL_PREFIX = "di-"
SKILL_MANIFEST = "SKILL.md"

# Targets supported by v1. Keys are the user-facing --target choices;
# values are the home-relative skill directories. Order matters for
# deterministic envelope output.
TARGETS: dict[str, Path] = {
    "claude": Path(".claude") / "skills",
    "codex": Path(".codex") / "skills",
}


@dataclass(frozen=True)
class Action:
    """One classified install action for a (skill, target) pair.

    ``kind`` decides the envelope bucket: ``install`` / ``skip`` / ``update``
    are applied; ``conflict`` aborts the whole run when any are present.
    """

    name: str  # skill directory name, e.g. "di-shared"
    target: str  # "claude" | "codex"
    source: Path  # absolute path to <repo>/skills/<name>
    link_path: Path  # absolute path to ~/.<tool>/skills/<name>
    kind: str  # "install" | "skip" | "update" | "conflict"
    reason: str | None = None  # filled for skip/update/conflict
    previous_target: str | None = None  # filled for "update" (old symlink target)


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach the install subparser and register its manifest entry."""
    parser = subparsers.add_parser(
        NAME,
        parents=[parent],
        help=SUMMARY,
        description=SUMMARY,
    )
    parser.add_argument(
        "--target",
        choices=("all", *TARGETS.keys()),
        default="all",
        help="which tool's skills directory to install into (default: all)",
    )
    parser.set_defaults(handler=_handle)
    register(
        CommandSpec(
            name=NAME,
            summary=SUMMARY,
            # Refuses to overwrite real directories, so this never
            # destroys user data; the higher tier is not warranted.
            risk=RiskClass.WRITE,
        )
    )


def _handle(args: argparse.Namespace) -> int:
    home = Path(os.path.expanduser("~"))
    source = _resolve_source()
    targets = _select_targets(args.target, home)

    skills = _discover_skills(source) if source is not None else []
    actions = _classify_all(skills, source, targets)

    conflicts = [a for a in actions if a.kind == "conflict"]
    if conflicts:
        return _emit_conflict_error(conflicts, source, targets, fmt=args.format)

    if not args.dry_run:
        _apply(actions)

    return _emit_success(
        actions, source, targets, dry_run=bool(args.dry_run), fmt=args.format
    )


# --- source / target resolution -------------------------------------------------


def _resolve_source() -> Path | None:
    """Locate the source ``skills/`` directory.

    ``DI_SKILLS_DIR`` short-circuits everything (useful for tests and
    advanced users with checkout layouts the walk-up cannot reach).
    Otherwise climb the package's filesystem path until we find a sibling
    ``skills/`` next to a ``pyproject.toml`` — the editable / repo case.
    Returns ``None`` when no source is found; the command still succeeds
    with an empty installed list so agents calling install during early
    repo bootstrap (no skills yet — T9/T10 land them later) don't see a
    confusing failure.
    """
    override = os.environ.get("DI_SKILLS_DIR")
    if override:
        path = Path(override).resolve()
        return path if path.is_dir() else None

    import di

    pkg_file = getattr(di, "__file__", None)
    if not pkg_file:
        return None
    here = Path(pkg_file).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "skills").is_dir():
            return (parent / "skills").resolve()
    return None


def _select_targets(choice: str, home: Path) -> dict[str, Path]:
    """Resolve target choice to absolute skills directories.

    ``--target all`` expands to every entry in :data:`TARGETS`. Parent
    directories (``~/.claude``, ``~/.codex``) are created on first install
    so AI agents bootstrapping a fresh machine don't get blocked on
    "config dir doesn't exist yet" errors.
    """
    keys = list(TARGETS) if choice == "all" else [choice]
    return {key: (home / TARGETS[key]).resolve() for key in keys}


# --- skill discovery & classification -------------------------------------------


def _discover_skills(source: Path) -> list[Path]:
    """Return absolute paths of valid skill directories under ``source``.

    A "valid skill" is a directory whose name starts with the ``di-``
    prefix and which contains a ``SKILL.md``. Anything else (READMEs,
    templates without manifest, hidden directories) is ignored — the
    validator (T8) will eventually fail on malformed entries; install's
    job is to be permissive and predictable.
    """
    out: list[Path] = []
    for entry in sorted(source.iterdir()):
        if not entry.is_dir():
            continue
        if not entry.name.startswith(SKILL_PREFIX):
            continue
        if not (entry / SKILL_MANIFEST).is_file():
            continue
        out.append(entry.resolve())
    return out


def _classify_all(
    skills: list[Path],
    source: Path | None,
    targets: dict[str, Path],
) -> list[Action]:
    """Compute one :class:`Action` per (skill × target). Deterministic order."""
    actions: list[Action] = []
    for skill in skills:
        for target_name, target_root in targets.items():
            link_path = target_root / skill.name
            actions.append(_classify_one(skill, target_name, link_path, source))
    return actions


def _classify_one(
    skill: Path,
    target_name: str,
    link_path: Path,
    source: Path | None,
) -> Action:
    """Decide what kind of action this (skill, target) needs.

    Order of checks matters:

    1. Nothing at the path → fresh install.
    2. Symlink → resolve and check ownership: ours-current (skip),
       ours-stale (update), broken (update — dead links are ours to fix),
       foreign (conflict).
    3. Real directory or other file → conflict.
    """
    if not link_path.exists() and not link_path.is_symlink():
        return Action(skill.name, target_name, skill, link_path, "install")

    if link_path.is_symlink():
        return _classify_symlink(skill, target_name, link_path, source)

    return Action(
        skill.name,
        target_name,
        skill,
        link_path,
        "conflict",
        reason="real-directory" if link_path.is_dir() else "real-file",
    )


def _classify_symlink(
    skill: Path,
    target_name: str,
    link_path: Path,
    source: Path | None,
) -> Action:
    """Sub-policy for an existing symlink at the target path."""
    try:
        resolved = link_path.resolve(strict=True)
    except (FileNotFoundError, OSError):
        # Broken symlink. Treat as ours-to-replace — refusing to fix a
        # dead link makes install seem stuck for no real reason.
        return Action(
            skill.name,
            target_name,
            skill,
            link_path,
            "update",
            reason="broken-symlink",
            previous_target=os.readlink(link_path),
        )

    if resolved == skill:
        return Action(skill.name, target_name, skill, link_path, "skip", reason="already-linked")

    if source is not None and _is_within(resolved, source):
        # Points elsewhere inside our source tree — stale install, repo
        # moved, or skill renamed. Safe to rewrite.
        return Action(
            skill.name,
            target_name,
            skill,
            link_path,
            "update",
            reason="stale-source",
            previous_target=str(resolved),
        )

    return Action(
        skill.name,
        target_name,
        skill,
        link_path,
        "conflict",
        reason="foreign-symlink",
        previous_target=str(resolved),
    )


def _is_within(child: Path, parent: Path) -> bool:
    """Return True if ``child`` is the same as or nested under ``parent``."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# --- apply ----------------------------------------------------------------------


def _apply(actions: list[Action]) -> None:
    """Perform filesystem mutations for the install/update actions.

    ``skip`` actions are no-ops. ``install`` and ``update`` both end with
    a symlink pointing at the source — the difference is only whether a
    prior link is being replaced.
    """
    for action in actions:
        if action.kind == "skip":
            continue
        action.link_path.parent.mkdir(parents=True, exist_ok=True)
        if action.link_path.is_symlink() or action.link_path.exists():
            # update path: remove the existing (broken/stale) symlink.
            # is_symlink() catches dead links that .exists() misses.
            action.link_path.unlink()
        action.link_path.symlink_to(action.source, target_is_directory=True)


# --- envelope emission ----------------------------------------------------------


def _emit_success(
    actions: list[Action],
    source: Path | None,
    targets: dict[str, Path],
    *,
    dry_run: bool,
    fmt: str,
) -> int:
    """Bucket actions by kind and write the success envelope."""
    data: dict[str, Any] = {
        "source": str(source) if source else None,
        "targets": {name: str(path) for name, path in targets.items()},
        "installed": [_action_row(a) for a in actions if a.kind == "install"],
        "skipped": [_action_row(a) for a in actions if a.kind == "skip"],
        "updated": [_action_row(a) for a in actions if a.kind == "update"],
        "dry_run": dry_run,
    }
    return emit_success(Envelope(identity=LOCAL_IDENTITY, data=data), fmt=fmt)


def _emit_conflict_error(
    conflicts: list[Action],
    source: Path | None,
    targets: dict[str, Path],
    *,
    fmt: str,
) -> int:
    """Single-shot error for the conflict-aborts-everything policy."""
    err = ErrDetail(
        type=ErrorType.VALIDATION,
        message=f"install aborted: {len(conflicts)} conflict(s) not managed by di",
        hint=(
            "remove or rename the conflicting entry, then re-run `di install`. "
            "files under .claude/skills or .codex/skills that are not symlinks "
            "managed by di are left untouched."
        ),
        detail={
            "source": str(source) if source else None,
            "targets": {name: str(path) for name, path in targets.items()},
            "conflicts": [_action_row(a) for a in conflicts],
        },
    )
    return emit_error(
        ErrorEnvelope(identity=LOCAL_IDENTITY, error=err),
        code=ExitCode.VALIDATION,
        fmt=fmt,
    )


def _action_row(action: Action) -> dict[str, Any]:
    """JSON row describing a single action. Fields omitted when irrelevant."""
    row: dict[str, Any] = {
        "name": action.name,
        "target": action.target,
        "path": str(action.link_path),
    }
    if action.reason is not None:
        row["reason"] = action.reason
    if action.previous_target is not None:
        row["previous_target"] = action.previous_target
    return row
