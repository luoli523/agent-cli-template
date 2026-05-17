"""Risk classification for commands.

Every command declares a ``risk`` in its schema. The CLI reads this at
invocation time to decide whether to enforce the ``--yes`` confirmation
gate (``high-risk-write`` and ``destructive-cost``).

``RiskDetail`` is attached to ``ErrDetail`` when an error of type
``confirmation_required`` is raised so the AI agent knows which action it
must obtain user consent for before re-invoking with ``--yes``.

See docs/specs/2026-05-15-di-cli-architecture.md § Risk classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RiskClass(str, Enum):
    """Risk level declared by every command in its schema."""

    READ = "read"
    WRITE = "write"
    HIGH_RISK_WRITE = "high-risk-write"
    DESTRUCTIVE_COST = "destructive-cost"


@dataclass(frozen=True)
class RiskDetail:
    """Risk metadata carried alongside ``confirmation_required`` errors.

    ``action`` is a human-identifiable name for the operation, e.g.
    ``"datamap +delete"`` or ``"spark jobs submit"``. AI agents echo this
    back to the user when asking for ``--yes`` consent.
    """

    level: RiskClass
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {"level": self.level.value, "action": self.action}
