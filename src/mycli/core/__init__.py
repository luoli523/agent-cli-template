"""Core mycli commands: hello / install / update / doctor / validate / version.

This package owns infrastructure commands — operations on the local
machine with no backing service. Service-touching commands live in
``shortcuts`` or ``commands``.

``register_subparsers`` is the single hook ``mycli.cli`` calls to attach
every core command to the root argparse parser.
"""

from __future__ import annotations

import argparse

from mycli.core import doctor, hello, install, update, validate, version


def register_subparsers(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach all core subparsers to the root parser."""
    doctor.register_subparser(subparsers, parent)
    hello.register_subparser(subparsers, parent)
    install.register_subparser(subparsers, parent)
    update.register_subparser(subparsers, parent)
    validate.register_subparser(subparsers, parent)
    version.register_subparser(subparsers, parent)
