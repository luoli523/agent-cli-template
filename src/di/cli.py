"""di-cli entry point.

``pyproject.toml`` declares ``di = "di.cli:main"``. This module is also
runnable via ``python -m di`` (see :mod:`di.__main__`).

Standard flags live on a parent parser shared with every subparser, so
``di version --format pretty`` works (flags after the subcommand —
matches git, kubectl, terraform). The reverse order — ``di --format
pretty version`` — is not supported; AI agents and humans should pass
flags after the subcommand. Top-level flags like ``--manifest`` and
``--version`` are exceptions (they're not subcommands).
"""

from __future__ import annotations

import argparse
import sys

from di import __version__, core
from di.contracts import Envelope
from di.manifest.registry import as_manifest_data
from di.runtime.flags import add_standard_flags
from di.runtime.output import LOCAL_IDENTITY, emit_success


def _make_common_parent() -> argparse.ArgumentParser:
    """Build a help-less parent parser carrying the standard flags.

    Reused by both the root parser and every subparser via ``parents=``
    so the same flags are recognized at both levels without duplication.
    """
    common = argparse.ArgumentParser(add_help=False)
    add_standard_flags(common)
    return common


def build_parser() -> argparse.ArgumentParser:
    """Construct the root argparse parser."""
    common = _make_common_parent()
    parser = argparse.ArgumentParser(
        prog="di",
        description=(
            "DI 操作层 for AI Agents. See `di --manifest` for the full surface."
        ),
        parents=[common],
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
    subparsers = parser.add_subparsers(
        dest="command", title="commands", metavar="<command>"
    )
    core.register_subparsers(subparsers, common)
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

    handler = getattr(args, "handler", None)
    if handler is None:
        # No subcommand selected — print help and exit cleanly.
        parser.print_help()
        return 0

    result = handler(args)
    return int(result)


if __name__ == "__main__":
    sys.exit(main())
