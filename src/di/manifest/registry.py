"""Command registry.

Each command module registers a :class:`CommandSpec` at import time. The
``di --manifest`` flag walks the registry to emit a machine-readable map
of the entire CLI surface — what AI agents call to discover capabilities
without parsing ``--help`` text.

The registry is a module-level singleton. Tests reset it via
:func:`clear`; production code never calls clear.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from di.contracts import RiskClass


@dataclass(frozen=True)
class CommandSpec:
    """Metadata describing a registered di-cli command.

    Populated by each command module at import time. Used by
    ``di --manifest`` to produce the surface map AI agents index.
    """

    name: str
    summary: str
    risk: RiskClass
    identity_required: bool = False
    supports_watch: bool = False
    supports_follow: bool = False
    supports_async_handle: bool = False
    scopes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "risk": self.risk.value,
            "identity_required": self.identity_required,
            "supports_watch": self.supports_watch,
            "supports_follow": self.supports_follow,
            "supports_async_handle": self.supports_async_handle,
            "scopes": list(self.scopes),
        }


_registry: dict[str, CommandSpec] = {}


def register(spec: CommandSpec) -> None:
    """Register a command spec. Last write wins.

    The last-write-wins policy keeps tests flexible (a test can override a
    spec by re-registering) without requiring every test to clear state.
    """
    _registry[spec.name] = spec


def get(name: str) -> CommandSpec | None:
    return _registry.get(name)


def all_specs() -> list[CommandSpec]:
    """Return all registered specs sorted by name (deterministic output)."""
    return sorted(_registry.values(), key=lambda s: s.name)


def clear() -> None:
    """Reset the registry. Test helper; production code must not call this."""
    _registry.clear()


def as_manifest_data() -> dict[str, Any]:
    """Build the ``data`` payload for the ``di --manifest`` envelope.

    Returns a dict with the running CLI version and the list of registered
    commands. Goes inside :class:`Envelope.data`.
    """
    from di import __version__

    return {
        "version": __version__,
        "commands": [s.to_dict() for s in all_specs()],
    }
