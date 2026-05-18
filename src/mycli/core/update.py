"""``di update`` — full re-sync of skills into Claude Code and Codex.

``install`` is forward-only: it adds missing symlinks and refreshes
stale ones. ``update`` adds the reverse direction: any symlink we
previously planted whose source skill no longer exists upstream gets
removed. Together the two commands implement:

    install = add + refresh
    update  = add + refresh + remove-orphans

An "orphan" is a target entry that is (a) a symlink, (b) resolves into
the current source skills tree, (c) has the ``di-`` prefix, and
(d) has no matching skill name in the current source. Foreign symlinks
and real directories are never orphans — they were never ours to begin
with, and would be classified as conflicts had a same-named source
skill existed.

This command does not upgrade mycli-cli itself. Users run
``pipx upgrade mycli-cli`` (or the equivalent in their package manager)
to receive new code and skills, then ``di update`` to re-sync the
filesystem.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Commands (update).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mycli.contracts import RiskClass
from mycli.core import _sync
from mycli.manifest import CommandSpec, register

NAME = "update"
SUMMARY = "Re-sync skills, including removal of orphaned symlinks"


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach the update subparser and register its manifest entry."""
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
            # Same risk class as install: we only ever unlink symlinks
            # we created. Real user data is never touched.
            risk=RiskClass.WRITE,
        )
    )


def _handle(args: argparse.Namespace) -> int:
    home = Path(os.path.expanduser("~"))
    source = _sync.resolve_source()
    targets = _sync.select_targets(args.target, home)

    skills = _sync.discover_skills(source) if source is not None else []
    forward = _sync.classify_forward(skills, source, targets)

    # Orphans only meaningful when we have a source root to compare
    # against. discover_orphans returns [] when source is None.
    current_names = {s.name for s in skills}
    orphans = _sync.discover_orphans(source, targets, current_names)

    actions = forward + orphans

    conflicts = [a for a in actions if a.kind == "conflict"]
    if conflicts:
        # Atomic abort: no forward actions, no orphan removals. The
        # user fixes the conflict and re-runs.
        return _sync.emit_conflict_error(conflicts, source, targets, fmt=args.format)

    if not args.dry_run:
        _sync.apply_actions(actions)

    return _sync.emit_sync_success(
        actions, source, targets, dry_run=bool(args.dry_run), fmt=args.format
    )
