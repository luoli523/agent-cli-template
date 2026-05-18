"""Core di-cli commands: install / update / doctor / version.

This package owns infrastructure commands — operations on the local
machine and on di-cli itself, with no backing service. Service-touching
commands live in ``shortcuts`` or ``commands``.

``register_subparsers`` is the single hook ``di.cli`` calls to attach
every core command to the root argparse parser. New core commands add
themselves here.
"""

from __future__ import annotations

import argparse

from di.core import doctor, install, update, validate, version


def register_subparsers(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    parent: argparse.ArgumentParser,
) -> None:
    """Attach all core subparsers to the root parser.

    ``parent`` carries the standard flags so every subcommand inherits
    them (``--format``, ``--dry-run``, ``--yes``, etc.). This is what
    lets ``di version --format pretty`` and ``di --format pretty version``
    both work — AI agents shouldn't have to learn flag ordering.
    """
    doctor.register_subparser(subparsers, parent)
    install.register_subparser(subparsers, parent)
    update.register_subparser(subparsers, parent)
    validate.register_subparser(subparsers, parent)
    version.register_subparser(subparsers, parent)
