"""Standard success and error envelopes written by every di-cli command.

Successful commands write :class:`Envelope` to stdout. Failures write
:class:`ErrorEnvelope` to stderr and exit with a code from
:mod:`di.contracts.exit_code`. The two envelope shapes are the protocol
surface AI agents parse on every call.

See docs/specs/2026-05-15-di-cli-architecture.md § Output envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from di.contracts.error_type import ErrDetail


@dataclass(frozen=True)
class Meta:
    """Optional metadata carried in envelope responses.

    ``count`` is intended for list-style ``data`` payloads. ``rollback``
    is intended for write operations that produce an undo command.
    Fields are omitted from JSON when ``None``.
    """

    count: int | None = None
    rollback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.count is not None:
            out["count"] = self.count
        if self.rollback is not None:
            out["rollback"] = self.rollback
        return out


@dataclass(frozen=True)
class Envelope:
    """Standard success envelope written to stdout.

    ``identity`` always echoes the role the command ran under so AI agents
    can confirm they got the lens they expected.

    ``notice`` is serialized under the JSON key ``_notice``; the leading
    underscore marks it as an out-of-band signal not tied to the request.
    Empty notice maps are omitted entirely.
    """

    identity: str
    data: dict[str, Any] | list[Any] | None = None
    meta: Meta | None = None
    notice: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"ok": True, "identity": self.identity}
        if self.data is not None:
            out["data"] = self.data
        if self.meta is not None:
            meta_dict = self.meta.to_dict()
            if meta_dict:
                out["meta"] = meta_dict
        if self.notice:
            out["_notice"] = self.notice
        return out


@dataclass(frozen=True)
class ErrorEnvelope:
    """Standard error envelope written to stderr."""

    identity: str
    error: ErrDetail
    meta: Meta | None = None
    notice: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ok": False,
            "identity": self.identity,
            "error": self.error.to_dict(),
        }
        if self.meta is not None:
            meta_dict = self.meta.to_dict()
            if meta_dict:
                out["meta"] = meta_dict
        if self.notice:
            out["_notice"] = self.notice
        return out
