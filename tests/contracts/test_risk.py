"""RiskClass catalogue + RiskDetail serialization."""

from __future__ import annotations

from di.contracts.risk import RiskClass, RiskDetail


def test_risk_class_values_match_spec() -> None:
    # Spec § Risk classification.
    assert RiskClass.READ.value == "read"
    assert RiskClass.WRITE.value == "write"
    assert RiskClass.HIGH_RISK_WRITE.value == "high-risk-write"
    assert RiskClass.DESTRUCTIVE_COST.value == "destructive-cost"


def test_risk_class_count_is_exactly_four() -> None:
    assert len(list(RiskClass)) == 4


def test_risk_detail_serialization() -> None:
    risk = RiskDetail(level=RiskClass.HIGH_RISK_WRITE, action="datamap +delete")
    assert risk.to_dict() == {"level": "high-risk-write", "action": "datamap +delete"}


def test_risk_detail_with_destructive_cost() -> None:
    risk = RiskDetail(level=RiskClass.DESTRUCTIVE_COST, action="spark jobs submit")
    assert risk.to_dict() == {"level": "destructive-cost", "action": "spark jobs submit"}
