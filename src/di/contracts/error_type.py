"""Error type catalogue and the structured error payload.

``ErrorType`` is the coarse classification AI agents branch on. ``ErrDetail``
is the full payload carried inside :class:`ErrorEnvelope.error`.

See docs/specs/2026-05-15-di-cli-architecture.md § Output envelope (error).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from di.contracts.risk import RiskDetail


class ErrorType(str, Enum):
    """Categorizes a structured error for AI consumption."""

    VALIDATION = "validation"
    PERMISSION = "permission"
    AUTH = "auth"
    API = "api"
    NETWORK = "network"
    INTERNAL = "internal"
    COST_GATE = "cost_gate"
    CONFIRMATION_REQUIRED = "confirmation_required"
    DEADLINE = "deadline"


@dataclass(frozen=True)
class ErrDetail:
    """Detailed error payload carried inside an error envelope.

    Optional fields are omitted from JSON when ``None`` (instead of being
    serialized as ``null``); the spec's "<int|null>" notation is a type
    hint, not a contract that the field must always appear.
    """

    type: ErrorType
    message: str
    code: int | None = None
    hint: str | None = None
    console_url: str | None = None
    permission_violations: list[str] | None = None
    retry_after_ms: int | None = None
    risk: RiskDetail | None = None
    detail: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"type": self.type.value, "message": self.message}
        if self.code is not None:
            out["code"] = self.code
        if self.hint is not None:
            out["hint"] = self.hint
        if self.console_url is not None:
            out["console_url"] = self.console_url
        if self.permission_violations is not None:
            out["permission_violations"] = list(self.permission_violations)
        if self.retry_after_ms is not None:
            out["retry_after_ms"] = self.retry_after_ms
        if self.risk is not None:
            out["risk"] = self.risk.to_dict()
        if self.detail is not None:
            out["detail"] = self.detail
        return out
