"""Shared skill-symlink machinery for ``mycli install`` and ``mycli update``.

Both commands operate on the same model: a source ``skills/`` directory
in the repo / installed wheel and one or more target directories under
``~/.<tool>/skills/``. They share source discovery, target selection,
classification of existing target entries, the apply step (with the
``remove`` branch only update uses), and envelope emission. Keeping
those in one place means the ownership rules live in exactly one file.

Internal module — nothing here is part of the public ``mycli.*`` API; both
``install`` and ``update`` re-export only what their handlers need.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mycli.contracts import (
    ErrDetail,
    Envelope,
    ErrorEnvelope,
    ErrorType,
    ExitCode,
)
from mycli.runtime import LOCAL_IDENTITY, emit_error, emit_success

SKILL_PREFIX = "mycli-"
SKILL_MANIFEST = "SKILL.md"

# Skills that live under ``skills/`` for reference but are NOT meant to
# be installed into AI tool directories. Currently only
# ``mycli-skill-template`` — it's a fork starting point, not a runtime
# teaching aid. Excluded names are filtered out by both forward sync
# (install / update never link them) and reverse sync (update never
# treats them as orphans, even if a user manually symlinked one).
EXCLUDED_FROM_INSTALL: frozenset[str] = frozenset({"mycli-skill-template"})

# Keys are user-facing ``--target`` choices; values are home-relative
# skill directories. Order is deterministic for envelope output.
TARGETS: dict[str, Path] = {
    "claude": Path(".claude") / "skills",
    "codex": Path(".codex") / "skills",
}

# Bucket names used in the success envelope. ``remove`` only appears in
# ``di update`` output; ``install`` never produces it.
ACTION_KINDS = ("install", "skip", "update", "remove", "conflict")


@dataclass(frozen=True)
class Action:
    """One classified action for a (skill, target) pair.

    ``kind`` decides the envelope bucket. ``install`` / ``skip`` /
    ``update`` / ``remove`` are applied; ``conflict`` aborts the run.

    ``source`` is ``None`` only for ``remove`` actions (orphaned
    symlinks whose source no longer exists). For every other kind,
    ``source`` points at the current source skill directory.
    """

    name: str
    target: str
    link_path: Path
    kind: str
    source: Path | None = None
    reason: str | None = None
    previous_target: str | None = None


# --- argparse helper ------------------------------------------------------------


def add_target_flag(parser: argparse.ArgumentParser) -> None:
    """Attach ``--target`` to a subparser. Shared between install and update."""
    parser.add_argument(
        "--target",
        choices=("all", *TARGETS.keys()),
        default="all",
        help="which tool's skills directory to act on (default: all)",
    )


# --- source / target resolution -------------------------------------------------


def resolve_source() -> Path | None:
    """Locate the source ``skills/`` directory.

    ``MYCLI_SKILLS_DIR`` short-circuits everything (useful for tests and
    advanced users with checkout layouts the walk-up cannot reach).
    Otherwise climb the package's filesystem path until a ``pyproject.toml``
    sibling with a ``skills/`` directory is found — the editable / repo
    case. Returns ``None`` when no source is found; callers should treat
    that as "no skills to install" rather than an error so AI agents
    bootstrapping a fresh repo (no skills yet — T9/T10 land them later)
    don't see a confusing failure.
    """
    override = os.environ.get("MYCLI_SKILLS_DIR")
    if override:
        path = Path(override).resolve()
        return path if path.is_dir() else None

    import mycli

    pkg_file = getattr(mycli, "__file__", None)
    if not pkg_file:
        return None
    here = Path(pkg_file).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "skills").is_dir():
            return (parent / "skills").resolve()
    return None


def select_targets(choice: str, home: Path) -> dict[str, Path]:
    """Resolve ``--target`` to absolute skills directories.

    ``--target all`` expands to every entry in :data:`TARGETS`. Parents
    are created lazily by :func:`apply_actions` so this is just a name
    resolution, with no side effects on the filesystem.
    """
    keys = list(TARGETS) if choice == "all" else [choice]
    return {key: (home / TARGETS[key]).resolve() for key in keys}


# --- skill discovery ------------------------------------------------------------


def discover_skills(source: Path) -> list[Path]:
    """Absolute paths of valid skill directories under ``source``.

    Valid = directory whose name starts with the ``di-`` prefix and
    which contains a ``SKILL.md``. Anything else (READMEs, malformed
    skill candidates) is ignored — the validator (T8) is what eventually
    fails the build on malformed entries; sync's job is to be permissive
    and predictable.

    Names in :data:`EXCLUDED_FROM_INSTALL` are filtered here so they
    never enter the forward-sync pipeline. The validator still walks
    them (they must self-validate) — installation is the orthogonal
    decision.
    """
    out: list[Path] = []
    for entry in sorted(source.iterdir()):
        if not entry.is_dir():
            continue
        if not entry.name.startswith(SKILL_PREFIX):
            continue
        if entry.name in EXCLUDED_FROM_INSTALL:
            continue
        if not (entry / SKILL_MANIFEST).is_file():
            continue
        out.append(entry.resolve())
    return out


# --- classification (forward sync) ----------------------------------------------


def classify_forward(
    skills: list[Path],
    source: Path | None,
    targets: dict[str, Path],
) -> list[Action]:
    """One :class:`Action` per (skill × target). Deterministic order."""
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
        return Action(skill.name, target_name, link_path, "install", source=skill)

    if link_path.is_symlink():
        return _classify_symlink(skill, target_name, link_path, source)

    return Action(
        skill.name,
        target_name,
        link_path,
        "conflict",
        source=skill,
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
        # dead link makes sync seem stuck for no real reason.
        return Action(
            skill.name,
            target_name,
            link_path,
            "update",
            source=skill,
            reason="broken-symlink",
            previous_target=os.readlink(link_path),
        )

    if resolved == skill:
        return Action(
            skill.name, target_name, link_path, "skip",
            source=skill, reason="already-linked",
        )

    if source is not None and is_within(resolved, source):
        return Action(
            skill.name,
            target_name,
            link_path,
            "update",
            source=skill,
            reason="stale-source",
            previous_target=str(resolved),
        )

    return Action(
        skill.name,
        target_name,
        link_path,
        "conflict",
        source=skill,
        reason="foreign-symlink",
        previous_target=str(resolved),
    )


# --- orphan discovery (update only) ---------------------------------------------


def discover_orphans(
    source: Path | None,
    targets: dict[str, Path],
    current_skill_names: set[str],
) -> list[Action]:
    """Find symlinks managed by di whose source skill no longer exists.

    An entry is an orphan iff:

    1. It is a symlink (not a real directory or file).
    2. Resolves into the current source skills tree.
    3. Its name starts with the ``di-`` prefix.
    4. There is no source skill with the same name today.
    5. Its name is not in :data:`EXCLUDED_FROM_INSTALL` — skills the
       project ships but does not auto-install (e.g. the skill
       template). If a user manually symlinked one of these, update
       leaves it alone; they put it there for a reason.

    Foreign symlinks (pointing outside our source tree) and real
    directories are not ours and never enter the orphan list — they
    would have been classified as conflicts had a same-named source
    skill existed.
    """
    if source is None:
        return []

    orphans: list[Action] = []
    for target_name, target_root in targets.items():
        if not target_root.is_dir():
            continue
        for entry in sorted(target_root.iterdir()):
            if not entry.is_symlink():
                continue
            if not entry.name.startswith(SKILL_PREFIX):
                continue
            if entry.name in current_skill_names:
                continue
            if entry.name in EXCLUDED_FROM_INSTALL:
                continue
            try:
                resolved = entry.resolve(strict=True)
            except (FileNotFoundError, OSError):
                # Broken symlink with no source counterpart — still ours
                # if readlink target sits under source. Use readlink
                # without strict resolve to make the call.
                raw = Path(os.readlink(entry))
                candidate = (entry.parent / raw).resolve() if not raw.is_absolute() else raw
                if not is_within(candidate, source):
                    continue
                orphans.append(
                    Action(
                        entry.name,
                        target_name,
                        entry,
                        "remove",
                        source=None,
                        reason="orphan-broken",
                        previous_target=str(raw),
                    )
                )
                continue
            if not is_within(resolved, source):
                continue
            orphans.append(
                Action(
                    entry.name,
                    target_name,
                    entry,
                    "remove",
                    source=None,
                    reason="orphan",
                    previous_target=str(resolved),
                )
            )
    return orphans


def is_within(child: Path, parent: Path) -> bool:
    """True if ``child`` is the same as or nested under ``parent``."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# --- apply ----------------------------------------------------------------------


def apply_actions(actions: list[Action]) -> None:
    """Mutate the filesystem for install/update/remove actions.

    ``skip`` actions are no-ops. ``install`` and ``update`` end with a
    symlink pointing at the source — the difference is only whether a
    prior link is being replaced. ``remove`` unlinks the orphan symlink.
    """
    for action in actions:
        if action.kind == "skip":
            continue
        if action.kind == "remove":
            if action.link_path.is_symlink() or action.link_path.exists():
                action.link_path.unlink()
            continue
        # install / update — always end pointing at the (non-None) source
        assert action.source is not None  # narrows type for mypy
        action.link_path.parent.mkdir(parents=True, exist_ok=True)
        if action.link_path.is_symlink() or action.link_path.exists():
            # update path: remove the existing (broken/stale) symlink.
            # is_symlink() catches dead links that .exists() misses.
            action.link_path.unlink()
        action.link_path.symlink_to(action.source, target_is_directory=True)


# --- envelope emission ----------------------------------------------------------


def emit_sync_success(
    actions: list[Action],
    source: Path | None,
    targets: dict[str, Path],
    *,
    dry_run: bool,
    fmt: str,
) -> int:
    """Write the success envelope, bucketed by action kind.

    The same shape is produced by install and update; install never
    populates ``removed`` (it has no orphan-discovery step), so that
    bucket is always empty for install runs. Both commands keep the
    same field set so AI agents see a stable envelope.
    """
    data: dict[str, Any] = {
        "source": str(source) if source else None,
        "targets": {name: str(path) for name, path in targets.items()},
        "installed": [action_row(a) for a in actions if a.kind == "install"],
        "skipped": [action_row(a) for a in actions if a.kind == "skip"],
        "updated": [action_row(a) for a in actions if a.kind == "update"],
        "removed": [action_row(a) for a in actions if a.kind == "remove"],
        "dry_run": dry_run,
    }
    return emit_success(Envelope(identity=LOCAL_IDENTITY, data=data), fmt=fmt)


def emit_conflict_error(
    conflicts: list[Action],
    source: Path | None,
    targets: dict[str, Path],
    *,
    fmt: str,
) -> int:
    """Single-shot error for the atomic-abort-on-conflict policy."""
    err = ErrDetail(
        type=ErrorType.VALIDATION,
        message=f"sync aborted: {len(conflicts)} conflict(s) not managed by di",
        hint=(
            "remove or rename the conflicting entry, then re-run the command. "
            "files under .claude/skills or .codex/skills that are not symlinks "
            "managed by di are left untouched."
        ),
        detail={
            "source": str(source) if source else None,
            "targets": {name: str(path) for name, path in targets.items()},
            "conflicts": [action_row(a) for a in conflicts],
        },
    )
    return emit_error(
        ErrorEnvelope(identity=LOCAL_IDENTITY, error=err),
        code=ExitCode.VALIDATION,
        fmt=fmt,
    )


def action_row(action: Action) -> dict[str, Any]:
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
