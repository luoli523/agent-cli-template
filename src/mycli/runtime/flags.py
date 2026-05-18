"""Standard flag plumbing for every mycli-cli command.

Spec § Standard flags lists nine cross-cutting flags. v1 parses all of them
on the root parser so every command sees a consistent surface. Not every
flag has a runtime behavior yet: ``--watch`` / ``--follow`` / ``--timeout``
and ``--page-*`` are placeholders until commands return :class:`Handle`
envelopes or paginate.

The ``--as`` flag accepts an arbitrary string. The set of valid role names
is defined by RAM (resolved through the credential provider chain), not by
mycli-cli core — see spec § Identity.
"""

from __future__ import annotations

import argparse

VALID_FORMATS: tuple[str, ...] = ("json", "pretty", "table", "ndjson", "csv")
"""Output format choices. v1 renders ``json`` and ``pretty``; the other
three are accepted at parse time and fall back to ``json`` at render time
so the spec's surface is honored without lying about capabilities."""


def add_standard_flags(parser: argparse.ArgumentParser) -> None:
    """Attach the cross-cutting flags every command must accept."""
    parser.add_argument(
        "--as",
        dest="identity_as",
        metavar="<role>",
        help="identity override; pass-through to credential layer (RAM-defined roles)",
    )
    parser.add_argument(
        "--profile",
        metavar="<name>",
        help="switch between configured profiles",
    )
    parser.add_argument(
        "--format",
        choices=VALID_FORMATS,
        default="json",
        help=(
            "output format (default: json). v1 implements json|pretty; "
            "table|ndjson|csv accepted but currently render as json."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview the request, do not execute",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm a high-risk-write or destructive-cost operation",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="repeat the command on an interval (read-side polling)",
    )
    parser.add_argument(
        "--follow",
        action="store_true",
        help="stream output (long-running ops; logs, status, results)",
    )
    parser.add_argument(
        "--timeout",
        metavar="<duration>",
        help="client-side deadline; exits with code 11 on overrun",
    )
    parser.add_argument(
        "--page-all",
        action="store_true",
        help="auto-paginate through all pages",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        metavar="<N>",
        help="page size (0 = use API default)",
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        metavar="<N>",
        help="max pages to fetch with --page-all",
    )
