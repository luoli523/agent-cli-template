"""Standard exit codes returned by mycli-cli commands.

Fine-grained error categories live in `error_type.py` (carried in the JSON
error envelope's ``type`` field). The exit code is a coarser signal that
shell consumers, CI, and AI agents react to without parsing JSON.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Exit codes.
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes communicated by every mycli-cli command."""

    OK = 0
    API = 1
    VALIDATION = 2
    AUTH = 3
    NETWORK = 4
    INTERNAL = 5
    COST_GATE = 6
    CONFIRMATION_REQUIRED = 10
    DEADLINE = 11
