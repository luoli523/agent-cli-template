"""``di doctor`` — health check for the local skill-sync state.

doctor is the read-only mirror of ``install`` / ``update``: it reuses
the same source / target / classification machinery from :mod:`_sync`,
but reports differences instead of fixing them. Output is structured
so an AI agent can branch directly on the per-check ``status`` field
and choose the right repair command from ``hint``.

Health grades
-------------

Each check returns ``ok`` / ``warn`` / ``fail``. The envelope's
``overall`` field is the worst of all checks:

* any ``fail`` → ``unhealthy`` (exit 5; error envelope on stderr)
* only ``warn`` → ``degraded`` (exit 0; success envelope; ``_notice``-style
  signal — agents address it after finishing the current task)
* all ``ok`` → ``healthy`` (exit 0)

The degraded → exit 0 choice is deliberate: degraded means "works, but
worth fixing" (e.g. ``~/.codex/skills`` missing because the user has
not installed Codex). Failing the shell pipeline for those would be
noise. Only unhealthy means "something is broken enough that running
commands will likely misbehave" — that's when exit 5 is warranted.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Commands (doctor).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from mycli.contracts import ErrDetail, Envelope, ErrorEnvelope, ErrorType, ExitCode, RiskClass
from mycli.core import _sync
from mycli.manifest import CommandSpec, register
from mycli.runtime import (
    DEGRADED,
    FAIL,
    HEALTHY,
    LOCAL_IDENTITY,
    OK,
    UNHEALTHY,
    WARN,
    Check,
    emit_error,
    emit_success,
)

NAME = "doctor"
SUMMARY = "Diagnose mycli-cli setup and skill-sync state"

MIN_PYTHON: tuple[int, int] = (3, 9)


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach the doctor subparser and register its manifest entry."""
    parser = subparsers.add_parser(
        NAME,
        parents=[parent],
        help=SUMMARY,
        description=SUMMARY,
    )
    _sync.add_target_flag(parser)
    parser.set_defaults(handler=_handle)
    register(
        CommandSpec(
            name=NAME,
            summary=SUMMARY,
            risk=RiskClass.READ,  # pure read-only; no --yes needed
        )
    )


def _handle(args: argparse.Namespace) -> int:
    home = Path(os.path.expanduser("~"))
    source = _sync.resolve_source()
    targets = _sync.select_targets(args.target, home)

    checks: list[Check] = [
        _check_python(),
        _check_source(source),
        _check_target_dirs(targets),
        _check_sync(source, targets),
    ]

    overall = _grade(checks)
    payload = {
        "overall": overall,
        "checks": [c.to_dict() for c in checks],
    }

    if overall == UNHEALTHY:
        # Surface the same payload via error envelope so AI agents see
        # the checks list in both success and failure paths — same key,
        # same shape, just routed through error.detail when broken.
        return emit_error(
            ErrorEnvelope(
                identity=LOCAL_IDENTITY,
                error=ErrDetail(
                    type=ErrorType.VALIDATION,
                    message=_unhealthy_summary(checks),
                    hint=_aggregate_hint(checks),
                    detail=payload,
                ),
            ),
            code=ExitCode.INTERNAL,
            fmt=args.format,
        )

    return emit_success(
        Envelope(identity=LOCAL_IDENTITY, data=payload), fmt=args.format
    )


# --- individual checks ----------------------------------------------------------


def _check_python() -> Check:
    """Confirm the running interpreter satisfies the spec floor."""
    actual = sys.version_info[:3]
    actual_str = ".".join(str(p) for p in actual)
    required_str = ".".join(str(p) for p in MIN_PYTHON)
    if actual[:2] >= MIN_PYTHON:
        return Check(
            "python",
            OK,
            f"Python {actual_str} satisfies >= {required_str}",
            detail={"required": required_str, "actual": actual_str},
        )
    return Check(
        "python",
        FAIL,
        f"Python {actual_str} is below required {required_str}",
        detail={"required": required_str, "actual": actual_str},
        hint=f"install Python {required_str}+ and re-create the venv",
    )


def _check_source(source: Path | None) -> Check:
    """Confirm a source ``skills/`` directory was discovered."""
    if source is None:
        return Check(
            "source",
            FAIL,
            "source skills/ directory not found",
            detail={"path": None},
            hint=(
                "install mycli-cli in editable mode (`pipx install -e /path/to/mycli-cli`) "
                "or set MYCLI_SKILLS_DIR to a valid skills/ directory"
            ),
        )
    return Check(
        "source",
        OK,
        "source skills/ resolved",
        detail={"path": str(source)},
    )


def _check_target_dirs(targets: dict[str, Path]) -> Check:
    """Confirm each requested tool's skills directory exists.

    Missing target dirs are a warning, not a failure: a user may have
    Claude Code installed but not Codex, or vice versa. ``di install``
    creates the parent on first run, so this only matters when doctor
    runs against a brand-new machine.
    """
    missing: list[dict[str, str]] = []
    for name, path in targets.items():
        if not path.is_dir():
            missing.append({"target": name, "path": str(path)})
    if not missing:
        return Check(
            "target_dirs",
            OK,
            "all target skill directories exist",
            detail={"targets": [{"target": n, "path": str(p)} for n, p in targets.items()]},
        )
    return Check(
        "target_dirs",
        WARN,
        f"{len(missing)} target directory missing",
        detail={"missing": missing},
        hint=(
            "install the AI tool (Claude Code / Codex) that owns the directory, "
            "or pass --target to scope doctor to the tools you actually use"
        ),
    )


def _check_sync(source: Path | None, targets: dict[str, Path]) -> Check:
    """Compare classified actions and report sync drift.

    Reuses :func:`_sync.classify_forward` + :func:`_sync.discover_orphans`
    so doctor and install/update see the same view of the world. The
    classification is bucketed here for read-only reporting:

    * conflicts → fail (will block install/update)
    * needs_install / needs_update / orphans → warn (fixable by `di update`)
    * everything skipped → ok
    """
    if source is None:
        # Source itself failed; the sync check is moot. Return ok so the
        # source-level fail dominates the overall grade without double-
        # reporting the same root cause.
        return Check(
            "sync_status",
            OK,
            "skipped: source unresolved",
            detail={"reason": "source unresolved; see source check"},
        )

    skills = _sync.discover_skills(source)
    forward = _sync.classify_forward(skills, source, targets)
    current_names = {s.name for s in skills}
    orphans = _sync.discover_orphans(source, targets, current_names)

    needs_install = [_sync.action_row(a) for a in forward if a.kind == "install"]
    needs_update = [_sync.action_row(a) for a in forward if a.kind == "update"]
    in_sync = [a for a in forward if a.kind == "skip"]
    conflicts = [_sync.action_row(a) for a in forward if a.kind == "conflict"]
    orphan_rows = [_sync.action_row(a) for a in orphans]

    detail: dict[str, Any] = {
        "in_sync": len(in_sync),
        "needs_install": needs_install,
        "needs_update": needs_update,
        "orphans": orphan_rows,
        "conflicts": conflicts,
    }

    if conflicts:
        return Check(
            "sync_status",
            FAIL,
            f"{len(conflicts)} conflict(s) blocking install/update",
            detail=detail,
            hint=(
                "remove or rename the conflicting target entries (see conflicts list), "
                "then run `di update`"
            ),
        )
    drift = len(needs_install) + len(needs_update) + len(orphan_rows)
    if drift > 0:
        return Check(
            "sync_status",
            WARN,
            f"{drift} skill(s) out of sync",
            detail=detail,
            hint="run `di update` to re-sync",
        )
    return Check("sync_status", OK, "all skills in sync", detail=detail)


# --- aggregation ----------------------------------------------------------------


def _grade(checks: list[Check]) -> str:
    """Worst-status-wins reduction."""
    statuses = {c.status for c in checks}
    if FAIL in statuses:
        return UNHEALTHY
    if WARN in statuses:
        return DEGRADED
    return HEALTHY


def _unhealthy_summary(checks: list[Check]) -> str:
    failing = [c.name for c in checks if c.status == FAIL]
    return f"di doctor: {len(failing)} check(s) failed: {', '.join(failing)}"


def _aggregate_hint(checks: list[Check]) -> str | None:
    """Concatenate non-empty hints from failing checks.

    AI agents prefer one envelope-level hint over scraping per-check
    detail. The full per-check hints remain available under
    ``error.detail.checks[*].hint`` for agents that want them.
    """
    hints = [c.hint for c in checks if c.status == FAIL and c.hint]
    if not hints:
        return None
    return "; ".join(hints)
