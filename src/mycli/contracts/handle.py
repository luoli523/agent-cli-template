"""Handle envelope for async / long-running operations.

A command that initiates a long-running operation (Spark job submission,
Flink stream, Presto query, Livy session) returns a ``Handle`` wrapped
inside :class:`Envelope.data` as ``{"handle": handle.to_dict()}``. The
``actions`` map spells out the exact follow-up commands the AI agent
should invoke, so it does not have to infer them.

Conventional action keys: ``poll``, ``follow``, ``logs``, ``cancel``.
Services may include only the subset they support.

See docs/specs/2026-05-15-mycli-cli-architecture.md § Handle envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STANDARD_ACTIONS: tuple[str, ...] = ("poll", "follow", "logs", "cancel")
"""Convention for ``actions`` keys. Services include only what they support."""


@dataclass(frozen=True)
class Handle:
    """Handle returned by commands that start async operations."""

    kind: str
    id: str
    status: str
    actions: dict[str, str]
    deadline: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": self.kind,
            "id": self.id,
            "status": self.status,
            "actions": dict(self.actions),
        }
        if self.deadline is not None:
            out["deadline"] = self.deadline
        return out
