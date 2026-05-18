"""``di install`` — symlink skills into Claude Code and Codex.

Walks ``<repo>/skills/di-*/`` and creates one symlink per skill into
each target tool's skills directory (``~/.claude/skills/<name>`` and
``~/.codex/skills/<name>``).

Conflict policy — read these together:

* If a target path is already a symlink resolving into our source skills
  tree, install treats it as ours (idempotent skip, or rewrite when the
  symlink points at a stale source).
* If a target path is a real directory, a regular file, or a symlink
  pointing outside our source tree, it is *not* ours; install refuses to
  touch it and reports a conflict.
* When any conflict exists, install aborts the whole run without touching
  the filesystem. There is no partial-success mode — agents read a
  single exit code, and re-running after the user fixes the conflict is
  the supported recovery path.

install is forward-only: it never removes existing symlinks even when
their source skill no longer exists. ``di update`` (T6) adds the
orphan-removal step on top of this command's logic.

The actual classification / apply / emit code lives in :mod:`_sync` so
``di update`` can reuse it. This module is just the install entry point.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Commands (install).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mycli.contracts import RiskClass
from mycli.core import _sync
from mycli.manifest import CommandSpec, register

NAME = "install"
SUMMARY = "Install mycli-cli skills into Claude Code and Codex"


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
    _sync.add_target_flag(parser)
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
    source = _sync.resolve_source()
    targets = _sync.select_targets(args.target, home)

    skills = _sync.discover_skills(source) if source is not None else []
    actions = _sync.classify_forward(skills, source, targets)

    conflicts = [a for a in actions if a.kind == "conflict"]
    if conflicts:
        return _sync.emit_conflict_error(conflicts, source, targets, fmt=args.format)

    if not args.dry_run:
        _sync.apply_actions(actions)

    return _sync.emit_sync_success(
        actions, source, targets, dry_run=bool(args.dry_run), fmt=args.format
    )
