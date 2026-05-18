"""CLI runtime: standard flag plumbing, output layer, notice hook.

See docs/specs/2026-05-15-di-cli-architecture.md § Standard flags
and § Output envelope.
"""

from di.runtime.checks import (
    DEGRADED,
    FAIL,
    HEALTHY,
    OK,
    UNHEALTHY,
    WARN,
    Check,
)
from di.runtime.flags import VALID_FORMATS, add_standard_flags
from di.runtime.output import (
    LOCAL_IDENTITY,
    collect_notices,
    default_notice_provider,
    emit_error,
    emit_success,
    set_notice_provider,
)

__all__ = [
    "Check",
    "DEGRADED",
    "FAIL",
    "HEALTHY",
    "LOCAL_IDENTITY",
    "OK",
    "UNHEALTHY",
    "VALID_FORMATS",
    "WARN",
    "add_standard_flags",
    "collect_notices",
    "default_notice_provider",
    "emit_error",
    "emit_success",
    "set_notice_provider",
]
