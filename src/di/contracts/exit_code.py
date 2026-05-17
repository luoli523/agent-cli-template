"""Standard exit codes returned by di-cli commands.

Fine-grained error categories live in `error_type.py` (carried in the JSON
error envelope's ``type`` field). The exit code is a coarser signal that
shell consumers, CI, and AI agents react to without parsing JSON.

See docs/specs/2026-05-15-di-cli-architecture.md § Exit codes.
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes communicated by every di-cli command."""

    OK = 0
    API = 1
    VALIDATION = 2
    AUTH = 3
    NETWORK = 4
    INTERNAL = 5
    COST_GATE = 6
    CONFIRMATION_REQUIRED = 10
    DEADLINE = 11
