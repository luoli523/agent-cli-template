"""``mycli hello`` — demo command showing envelope/--format/exit-code in action.

Delete this file and its test once you've added your first real service
command. It exists only to prove the scaffold works out of the box.
"""

from __future__ import annotations

import argparse

from mycli.contracts import ErrDetail, ErrorEnvelope, ErrorType, ExitCode, Envelope, RiskClass
from mycli.manifest import CommandSpec, register
from mycli.runtime import LOCAL_IDENTITY, emit_error, emit_success

NAME = "hello"
SUMMARY = "Greet a name — demo command showing envelope/--format/exit-code"


def register_subparser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser(
        NAME,
        parents=[parent],
        help=SUMMARY,
        description=SUMMARY,
    )
    parser.add_argument(
        "--name",
        metavar="<name>",
        required=True,
        help="name to greet",
    )
    parser.set_defaults(handler=_handle)
    register(CommandSpec(name=NAME, summary=SUMMARY, risk=RiskClass.READ))


def _handle(args: argparse.Namespace) -> int:
    name: str = args.name.strip()
    if not name:
        return emit_error(
            ErrorEnvelope(
                identity=LOCAL_IDENTITY,
                error=ErrDetail(
                    type=ErrorType.VALIDATION,
                    message="--name must not be blank",
                    hint="pass a non-empty string: mycli hello --name Alice",
                ),
            ),
            code=ExitCode.VALIDATION,
            fmt=args.format,
        )
    env = Envelope(identity=LOCAL_IDENTITY, data={"greeting": f"Hello, {name}!"})
    return emit_success(env, fmt=args.format)
