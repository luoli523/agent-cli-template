"""di-cli entry point.

``pyproject.toml`` declares ``di = "di.cli:main"``. This module is also
runnable via ``python -m di`` (see :mod:`di.__main__`).

T3 ships the root parser and the ``--manifest`` flag. Subcommands
(``version``, ``install``, ``update``, ``doctor``) land in T4–T7.
"""

from __future__ import annotations

import argparse
import sys

from di import __version__
from di.contracts import Envelope
from di.manifest.registry import as_manifest_data
from di.runtime.flags import add_standard_flags
from di.runtime.output import LOCAL_IDENTITY, emit_success


def build_parser() -> argparse.ArgumentParser:
    """Construct the root argparse parser."""
    parser = argparse.ArgumentParser(
        prog="di",
        description=(
            "DI 操作层 for AI Agents. See `di --manifest` for the full surface."
        ),
        add_help=True,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"di {__version__}",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="emit a machine-readable map of the entire CLI surface",
    )
    add_standard_flags(parser)
    # Subcommands are added in T4+ via parser.add_subparsers(...) on this
    # parser. T3 leaves the slot present so dispatch logic in main() works
    # without per-task plumbing changes.
    parser.add_subparsers(dest="command", title="commands", metavar="<command>")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns the process exit code. Callers wrap with :func:`sys.exit`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.manifest:
        env = Envelope(
            identity=LOCAL_IDENTITY,
            data=as_manifest_data(),
        )
        return emit_success(env, fmt=args.format)

    if args.command is None:
        # No subcommand and no top-level action — print help and exit cleanly.
        parser.print_help()
        return 0

    # No subcommand handlers are registered yet (T4+). Reaching this branch
    # means argparse accepted a value that has no implementation.
    parser.error(f"unknown command: {args.command}")
    return 2  # parser.error raises SystemExit(2); kept for type checkers


if __name__ == "__main__":
    sys.exit(main())
