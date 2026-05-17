"""ErrorType catalogue + ErrDetail serialization (omit-None convention)."""

from __future__ import annotations

from di.contracts.error_type import ErrDetail, ErrorType
from di.contracts.risk import RiskClass, RiskDetail


def test_error_type_values_match_spec() -> None:
    assert ErrorType.VALIDATION.value == "validation"
    assert ErrorType.PERMISSION.value == "permission"
    assert ErrorType.AUTH.value == "auth"
    assert ErrorType.API.value == "api"
    assert ErrorType.NETWORK.value == "network"
    assert ErrorType.INTERNAL.value == "internal"
    assert ErrorType.COST_GATE.value == "cost_gate"
    assert ErrorType.CONFIRMATION_REQUIRED.value == "confirmation_required"
    assert ErrorType.DEADLINE.value == "deadline"


def test_error_type_count_is_exactly_nine() -> None:
    assert len(list(ErrorType)) == 9


def test_err_detail_minimal_only_required_fields() -> None:
    err = ErrDetail(type=ErrorType.INTERNAL, message="unexpected condition")
    assert err.to_dict() == {"type": "internal", "message": "unexpected condition"}


def test_err_detail_omits_none_fields() -> None:
    # The omit-None convention: optional fields disappear from JSON when
    # not set. The spec's "<int|null>" annotation is a type hint, not a
    # contract that the field must always appear.
    err = ErrDetail(
        type=ErrorType.NETWORK,
        message="connection reset",
        retry_after_ms=None,
        code=None,
    )
    assert err.to_dict() == {"type": "network", "message": "connection reset"}


def test_err_detail_full_permission_error() -> None:
    err = ErrDetail(
        type=ErrorType.PERMISSION,
        message="Permission denied [403]",
        code=403,
        hint="run `di ram request --scope datamap:read`",
        console_url="https://ram.example.com/scopes",
        permission_violations=["datamap:read"],
        detail={"service": "datamap"},
    )
    assert err.to_dict() == {
        "type": "permission",
        "message": "Permission denied [403]",
        "code": 403,
        "hint": "run `di ram request --scope datamap:read`",
        "console_url": "https://ram.example.com/scopes",
        "permission_violations": ["datamap:read"],
        "detail": {"service": "datamap"},
    }


def test_err_detail_confirmation_required_includes_risk() -> None:
    err = ErrDetail(
        type=ErrorType.CONFIRMATION_REQUIRED,
        message="datamap +delete requires confirmation",
        hint="add --yes to confirm",
        risk=RiskDetail(level=RiskClass.HIGH_RISK_WRITE, action="datamap +delete"),
    )
    assert err.to_dict() == {
        "type": "confirmation_required",
        "message": "datamap +delete requires confirmation",
        "hint": "add --yes to confirm",
        "risk": {"level": "high-risk-write", "action": "datamap +delete"},
    }


def test_err_detail_network_with_retry() -> None:
    err = ErrDetail(
        type=ErrorType.NETWORK,
        message="rate limited",
        retry_after_ms=500,
    )
    assert err.to_dict() == {
        "type": "network",
        "message": "rate limited",
        "retry_after_ms": 500,
    }


