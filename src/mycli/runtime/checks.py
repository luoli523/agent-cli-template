"""Shared :class:`Check` dataclass and status constants.

A ``Check`` is a single named diagnostic with an ``ok | warn | fail``
status, a one-line message, optional structured detail, and an
optional repair hint. Used by both ``di doctor`` (runtime state) and
``di validate`` (authoring conventions) — keeping them in one place
means AI agents see the same envelope shape across diagnostics.

Lives in :mod:`di.runtime` rather than :mod:`di.core` so validator
modules can import it without triggering ``di.core.__init__`` (which
in turn imports validate, which imports validators — that path is a
circular import waiting to happen).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OK = "ok"
WARN = "warn"
FAIL = "fail"

HEALTHY = "healthy"
DEGRADED = "degraded"
UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class Check:
    """One named diagnostic.

    ``status`` is ``ok | warn | fail``. The caller is responsible for
    reducing a list of checks to an overall grade via worst-status-wins
    (any ``fail`` → unhealthy; only ``warn`` → degraded; all ``ok`` →
    healthy). Fields omitted from JSON when ``None``.
    """

    name: str
    status: str
    message: str
    detail: dict[str, Any] | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name, "status": self.status, "message": self.message}
        if self.detail is not None:
            out["detail"] = self.detail
        if self.hint is not None:
            out["hint"] = self.hint
        return out
