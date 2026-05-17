"""Envelope writers, stdout/stderr split, and _notice injection."""

from __future__ import annotations

import io
import json

from di.contracts import Envelope, ErrDetail, ErrorEnvelope, ErrorType, ExitCode
from di.runtime.output import (
    LOCAL_IDENTITY,
    collect_notices,
    emit_error,
    emit_success,
    set_notice_provider,
)


def test_local_identity_value() -> None:
    assert LOCAL_IDENTITY == "local"


def test_emit_success_writes_compact_json_to_stdout() -> None:
    buf = io.StringIO()
    env = Envelope(identity="user", data={"x": 1})
    code = emit_success(env, stdout=buf)
    assert code == ExitCode.OK
    text = buf.getvalue()
    assert text.endswith("\n")
    payload = json.loads(text)
    assert payload == {"ok": True, "identity": "user", "data": {"x": 1}}


def test_emit_success_pretty_indents_two_spaces() -> None:
    buf = io.StringIO()
    env = Envelope(identity="user", data={"x": 1})
    emit_success(env, fmt="pretty", stdout=buf)
    text = buf.getvalue()
    assert "\n  " in text  # indent=2
    payload = json.loads(text)
    assert payload["ok"] is True


def test_emit_success_unknown_format_falls_back_to_compact_json() -> None:
    buf = io.StringIO()
    env = Envelope(identity="user", data={"x": 1})
    emit_success(env, fmt="csv", stdout=buf)
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True


def test_emit_success_unicode_preserves_cjk_without_escapes() -> None:
    # ensure_ascii=False so 中文 and similar appear literally.
    buf = io.StringIO()
    env = Envelope(identity="user", data={"label": "数据地图"})
    emit_success(env, stdout=buf)
    assert "数据地图" in buf.getvalue()


def test_emit_error_writes_to_stderr_and_returns_code() -> None:
    buf = io.StringIO()
    err = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.VALIDATION, message="bad input"),
    )
    code = emit_error(err, code=ExitCode.VALIDATION, stderr=buf)
    assert code == ExitCode.VALIDATION
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is False
    assert payload["error"]["type"] == "validation"


def test_emit_error_default_code_is_api() -> None:
    buf = io.StringIO()
    err = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.API, message="upstream said no"),
    )
    code = emit_error(err, stderr=buf)
    assert code == ExitCode.API


def test_set_notice_provider_swaps_global_state() -> None:
    assert collect_notices() == {}
    set_notice_provider(lambda: {"update": {"current": "0.2.0", "latest": "0.3.0"}})
    assert collect_notices() == {"update": {"current": "0.2.0", "latest": "0.3.0"}}


def test_notice_provider_payload_injected_into_success_envelope() -> None:
    set_notice_provider(lambda: {"update": {"current": "0.2.0"}})
    buf = io.StringIO()
    env = Envelope(identity="user", data={"x": 1})
    emit_success(env, stdout=buf)
    payload = json.loads(buf.getvalue())
    assert payload["_notice"] == {"update": {"current": "0.2.0"}}


def test_notice_provider_payload_injected_into_error_envelope() -> None:
    set_notice_provider(lambda: {"update": {"current": "0.2.0"}})
    buf = io.StringIO()
    err = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.NETWORK, message="timeout"),
    )
    emit_error(err, code=ExitCode.NETWORK, stderr=buf)
    payload = json.loads(buf.getvalue())
    assert payload["_notice"] == {"update": {"current": "0.2.0"}}


def test_no_notice_field_when_provider_returns_empty() -> None:
    buf = io.StringIO()
    env = Envelope(identity="user", data={"x": 1})
    emit_success(env, stdout=buf)
    payload = json.loads(buf.getvalue())
    assert "_notice" not in payload


def test_explicit_envelope_notice_wins_over_provider() -> None:
    # If a command sets Envelope.notice explicitly, the provider must not
    # overwrite that value. Explicit beats implicit.
    set_notice_provider(lambda: {"update": {"from": "provider"}})
    buf = io.StringIO()
    env = Envelope(
        identity="user",
        data={"x": 1},
        notice={"deprecation": {"from": "explicit"}},
    )
    emit_success(env, stdout=buf)
    payload = json.loads(buf.getvalue())
    assert payload["_notice"] == {"deprecation": {"from": "explicit"}}
