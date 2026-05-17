"""Envelope and ErrorEnvelope serialization against spec § Output envelope."""

from __future__ import annotations

import json

from di.contracts.envelope import Envelope, ErrorEnvelope, Meta
from di.contracts.error_type import ErrDetail, ErrorType


def test_envelope_minimal_only_identity() -> None:
    env = Envelope(identity="user")
    assert env.to_dict() == {"ok": True, "identity": "user"}


def test_envelope_with_data_dict() -> None:
    env = Envelope(identity="user", data={"foo": "bar"})
    assert env.to_dict() == {"ok": True, "identity": "user", "data": {"foo": "bar"}}


def test_envelope_with_data_list_and_meta_count() -> None:
    env = Envelope(
        identity="user",
        data=[{"id": 1}, {"id": 2}],
        meta=Meta(count=2),
    )
    assert env.to_dict() == {
        "ok": True,
        "identity": "user",
        "data": [{"id": 1}, {"id": 2}],
        "meta": {"count": 2},
    }


def test_envelope_with_notice_uses_underscore_prefix_key() -> None:
    # Python attr is ``notice``; JSON key is ``_notice`` (out-of-band marker).
    env = Envelope(
        identity="user",
        data={"foo": "bar"},
        notice={"update": {"current": "0.2.0", "latest": "0.3.0"}},
    )
    out = env.to_dict()
    assert "_notice" in out
    assert "notice" not in out
    assert out["_notice"] == {"update": {"current": "0.2.0", "latest": "0.3.0"}}


def test_envelope_empty_notice_dict_is_omitted() -> None:
    env = Envelope(identity="user", data={}, notice={})
    assert "_notice" not in env.to_dict()


def test_envelope_empty_meta_is_omitted() -> None:
    env = Envelope(identity="user", data={}, meta=Meta())
    assert "meta" not in env.to_dict()


def test_envelope_serializes_to_valid_json() -> None:
    # Round-trip via json.dumps + loads to catch any non-JSON-encodable values.
    env = Envelope(
        identity="service",
        data={"items": [1, 2, 3]},
        meta=Meta(count=3, rollback="di datamap rollback --id 42"),
        notice={"deprecation": {"service": "datamap-v1", "after": "2026-12-31"}},
    )
    serialized = json.dumps(env.to_dict())
    parsed = json.loads(serialized)
    assert parsed["ok"] is True
    assert parsed["identity"] == "service"
    assert parsed["meta"] == {"count": 3, "rollback": "di datamap rollback --id 42"}


def test_error_envelope_minimal() -> None:
    env = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.INTERNAL, message="unexpected"),
    )
    assert env.to_dict() == {
        "ok": False,
        "identity": "user",
        "error": {"type": "internal", "message": "unexpected"},
    }


def test_error_envelope_with_full_permission_error() -> None:
    env = ErrorEnvelope(
        identity="user",
        error=ErrDetail(
            type=ErrorType.PERMISSION,
            message="Permission denied [403]",
            code=403,
            hint="run `di ram request --scope datamap:read`",
            console_url="https://ram.example.com/scopes",
            permission_violations=["datamap:read"],
        ),
    )
    assert env.to_dict() == {
        "ok": False,
        "identity": "user",
        "error": {
            "type": "permission",
            "message": "Permission denied [403]",
            "code": 403,
            "hint": "run `di ram request --scope datamap:read`",
            "console_url": "https://ram.example.com/scopes",
            "permission_violations": ["datamap:read"],
        },
    }


def test_error_envelope_carries_notice_during_failure() -> None:
    # Even when the request fails, the CLI still nudges the agent toward
    # pending out-of-band actions like updating itself.
    env = ErrorEnvelope(
        identity="service",
        error=ErrDetail(type=ErrorType.NETWORK, message="timeout"),
        notice={"update": {"current": "0.2.0", "latest": "0.3.0"}},
    )
    out = env.to_dict()
    assert out["_notice"] == {"update": {"current": "0.2.0", "latest": "0.3.0"}}


def test_error_envelope_ok_field_is_false() -> None:
    env = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.VALIDATION, message="bad input"),
    )
    assert env.to_dict()["ok"] is False


def test_error_envelope_with_meta_rollback() -> None:
    # Error responses can still describe a rollback path when one applies
    # (e.g. a partial write that succeeded before the failure).
    env = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.API, message="partial failure"),
        meta=Meta(rollback="di datamap rollback --id 42"),
    )
    assert env.to_dict() == {
        "ok": False,
        "identity": "user",
        "error": {"type": "api", "message": "partial failure"},
        "meta": {"rollback": "di datamap rollback --id 42"},
    }


def test_error_envelope_empty_meta_is_omitted() -> None:
    env = ErrorEnvelope(
        identity="user",
        error=ErrDetail(type=ErrorType.NETWORK, message="timeout"),
        meta=Meta(),
    )
    assert "meta" not in env.to_dict()
