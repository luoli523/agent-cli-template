"""``di validate`` — enforce skill authoring + repo-shape conventions.

The convention companion to ``di doctor``. Doctor diagnoses the
*installed* state (symlinks, target dirs); validate diagnoses the
*authored* state (skills/ directory contents, repo shape) so CI can
block PRs that ship malformed skills before they hit anyone's
``~/.claude/skills/``.

Output reuses doctor's :class:`Check` schema. ``overall`` is reduced
worst-status-wins (any ``fail`` → unhealthy; only ``warn`` → degraded;
all ``ok`` → healthy). Unhealthy returns exit 5; degraded and healthy
return exit 0. The reasoning is the same as doctor's: CI pipelines
should pass on cosmetic warnings (line length, optional metadata typo)
but fail on contract-breaking issues (missing description trigger
markers, mismatched name).

Scope:

* ``--scope skills`` — only walk skills/ (CI's per-skill checks)
* ``--scope repo`` — only repo-shape (CI's structural audit)
* ``--scope all`` (default) — both
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from di.contracts import ErrDetail, Envelope, ErrorEnvelope, ErrorType, ExitCode, RiskClass
from di.manifest import CommandSpec, register
from di.runtime import (
    DEGRADED,
    FAIL,
    HEALTHY,
    LOCAL_IDENTITY,
    UNHEALTHY,
    WARN,
    Check,
    emit_error,
    emit_success,
)
from di.validators import validate_repo, validate_skills_root

NAME = "validate"
SUMMARY = "Validate skill authoring conventions and repo shape"


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach the validate subparser and register its manifest entry."""
    parser = subparsers.add_parser(
        NAME,
        parents=[parent],
        help=SUMMARY,
        description=SUMMARY,
    )
    parser.add_argument(
        "--scope",
        choices=("all", "skills", "repo"),
        default="all",
        help="which audit to run (default: all)",
    )
    parser.add_argument(
        "--skills-dir",
        metavar="<path>",
        help=(
            "explicit skills/ directory to validate; defaults to "
            "DI_SKILLS_DIR or the walk-up source resolution"
        ),
    )
    parser.set_defaults(handler=_handle)
    register(
        CommandSpec(name=NAME, summary=SUMMARY, risk=RiskClass.READ),
    )


def _handle(args: argparse.Namespace) -> int:
    skills_root = _resolve_skills_root(args.skills_dir)
    repo_root = _resolve_repo_root(skills_root)

    checks: list[Check] = []
    if args.scope in ("all", "repo"):
        if repo_root is None:
            checks.append(
                Check(
                    "repo/root",
                    FAIL,
                    "could not locate repo root (pyproject.toml not found above skills/)",
                    hint="run `di validate` from inside the repo or pass --skills-dir",
                )
            )
        else:
            checks.extend(validate_repo(repo_root))
    if args.scope in ("all", "skills"):
        if skills_root is None:
            checks.append(
                Check(
                    "skills_root",
                    FAIL,
                    "skills/ directory not found",
                    hint=(
                        "pass --skills-dir, set DI_SKILLS_DIR, or run from a "
                        "checkout that ships skills/"
                    ),
                )
            )
        else:
            checks.extend(validate_skills_root(skills_root))

    overall = _grade(checks)
    payload: dict[str, Any] = {
        "overall": overall,
        "scope": args.scope,
        "skills_dir": str(skills_root) if skills_root else None,
        "repo_root": str(repo_root) if repo_root else None,
        "checks": [c.to_dict() for c in checks],
    }

    if overall == UNHEALTHY:
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


# --- helpers -----------------------------------------------------------------


def _resolve_skills_root(explicit: str | None) -> Path | None:
    """Resolve which skills/ to validate.

    Priority: explicit ``--skills-dir`` > ``DI_SKILLS_DIR`` env >
    walk-up from ``di.__file__`` for a sibling ``skills/``. The walk-up
    matches install/update's own source resolution so ``di validate``
    and ``di install`` see the same skills.
    """
    if explicit:
        p = Path(explicit).resolve()
        return p if p.is_dir() else None

    env = os.environ.get("DI_SKILLS_DIR")
    if env:
        p = Path(env).resolve()
        return p if p.is_dir() else None

    import di

    pkg_file = getattr(di, "__file__", None)
    if not pkg_file:
        return None
    here = Path(pkg_file).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "skills").is_dir():
            return (parent / "skills").resolve()
    return None


def _resolve_repo_root(skills_root: Path | None) -> Path | None:
    """The repo root is the parent of skills/ that owns ``pyproject.toml``.

    Falls back to walking up from the package install location when no
    skills_root is found (e.g. ``--scope repo`` against an empty repo).
    """
    if skills_root and (skills_root.parent / "pyproject.toml").is_file():
        return skills_root.parent

    import di

    pkg_file = getattr(di, "__file__", None)
    if not pkg_file:
        return None
    here = Path(pkg_file).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def _grade(checks: list[Check]) -> str:
    statuses = {c.status for c in checks}
    if FAIL in statuses:
        return UNHEALTHY
    if WARN in statuses:
        return DEGRADED
    return HEALTHY


def _unhealthy_summary(checks: list[Check]) -> str:
    failing = [c.name for c in checks if c.status == FAIL]
    return f"di validate: {len(failing)} check(s) failed"


def _aggregate_hint(checks: list[Check]) -> str | None:
    hints = [c.hint for c in checks if c.status == FAIL and c.hint]
    if not hints:
        return None
    return "; ".join(hints)
