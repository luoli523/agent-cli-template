"""``di version`` — show mycli-cli version and runtime info.

The first real subcommand. Its job is small: emit a stable JSON envelope
with the running version, Python interpreter, and host platform. Larger
purpose: prove the manifest-registration + envelope-emission flow works
end-to-end before the more complex install / update / doctor commands
land in T5–T7.
"""

from __future__ import annotations

import argparse
import platform
import sys
from typing import Any

from mycli import __version__
from mycli.contracts import Envelope, RiskClass
from mycli.manifest import CommandSpec, register
from mycli.runtime import LOCAL_IDENTITY, emit_success

NAME = "version"
SUMMARY = "Show mycli-cli version and runtime info"


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach the version subparser and register its manifest entry."""
    parser = subparsers.add_parser(
        NAME,
        parents=[parent],
        help=SUMMARY,
        description=SUMMARY,
    )
    parser.set_defaults(handler=_handle)
    register(
        CommandSpec(
            name=NAME,
            summary=SUMMARY,
            risk=RiskClass.READ,
        )
    )


def _handle(args: argparse.Namespace) -> int:
    data: dict[str, Any] = {
        "version": __version__,
        "python": ".".join(str(p) for p in sys.version_info[:3]),
        "platform": platform.system().lower(),
    }
    env = Envelope(identity=LOCAL_IDENTITY, data=data)
    return emit_success(env, fmt=args.format)
