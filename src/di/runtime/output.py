"""Envelope output layer.

Writes :class:`Envelope` to stdout and :class:`ErrorEnvelope` to stderr.
Stdout is data; stderr is everything else (progress, hints, errors).
Mixing the two corrupts pipe chains, so commands must always go through
:func:`emit_success` / :func:`emit_error` rather than ``print``.

The ``_notice`` channel (spec § ``_notice`` channel) is injected here.
v1 uses a no-op provider; T6 (``di update``) wires it to the real update
checker. Commands that set ``Envelope.notice`` explicitly win — the
provider only fills in when no explicit notice is set.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, TextIO

from di.contracts import Envelope, ErrorEnvelope, ExitCode

LOCAL_IDENTITY: str = "local"
"""Identity echoed by infrastructure commands that touch no backing service
(``--manifest``, ``version``, ``install``, ``update``, ``doctor``). Real
service-touching commands resolve identity through the credential layer."""

NoticeProvider = Callable[[], dict[str, Any]]


def default_notice_provider() -> dict[str, Any]:
    """No-op notice provider — returns no pending notices.

    Exposed so callers (and tests) can reset the global to the default
    without re-creating an anonymous ``lambda: {}``.
    """
    return {}


_notice_provider: NoticeProvider = default_notice_provider


def set_notice_provider(provider: NoticeProvider) -> None:
    """Replace the global notice provider.

    T3 ships a no-op provider. T6 (di update) and any other producer that
    surfaces out-of-band signals replaces it during CLI bootstrap.
    """
    global _notice_provider
    _notice_provider = provider


def collect_notices() -> dict[str, Any]:
    """Return the current pending notices (may be empty)."""
    return _notice_provider()


def emit_success(
    env: Envelope,
    fmt: str = "json",
    *,
    stdout: TextIO | None = None,
) -> int:
    """Write a success envelope to stdout and return :data:`ExitCode.OK`."""
    stream = stdout if stdout is not None else sys.stdout
    payload = env.to_dict()
    _maybe_inject_notice(payload)
    _write(payload, fmt, stream)
    return int(ExitCode.OK)


def emit_error(
    err: ErrorEnvelope,
    code: ExitCode = ExitCode.API,
    fmt: str = "json",
    *,
    stderr: TextIO | None = None,
) -> int:
    """Write an error envelope to stderr and return the exit code."""
    stream = stderr if stderr is not None else sys.stderr
    payload = err.to_dict()
    _maybe_inject_notice(payload)
    _write(payload, fmt, stream)
    return int(code)


def _maybe_inject_notice(payload: dict[str, Any]) -> None:
    """Fill in ``_notice`` from the provider if the envelope did not set one."""
    if "_notice" in payload:
        return
    pending = collect_notices()
    if pending:
        payload["_notice"] = pending


def _write(payload: dict[str, Any], fmt: str, stream: TextIO) -> None:
    """Serialize ``payload`` to ``stream``.

    ``pretty`` uses indent=2 for human reading. ``table|ndjson|csv`` are
    accepted by the parser but render as compact json in v1 — AI agents
    still parse successfully, and full implementations can land later
    without a contract change.
    """
    if fmt == "pretty":
        stream.write(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        stream.write(json.dumps(payload, ensure_ascii=False))
    stream.write("\n")
    stream.flush()
