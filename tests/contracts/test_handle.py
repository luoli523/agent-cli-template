"""Handle serialization and the standard-actions convention."""

from __future__ import annotations

from di.contracts.envelope import Envelope
from di.contracts.handle import STANDARD_ACTIONS, Handle


def test_standard_actions_match_spec() -> None:
    # Convention from spec § Handle envelope; services include only the
    # subset they support.
    assert STANDARD_ACTIONS == ("poll", "follow", "logs", "cancel")


def test_handle_serialization_matches_spec_example() -> None:
    handle = Handle(
        kind="spark.job",
        id="application_1735200000_0042",
        status="submitted",
        actions={
            "poll": "di spark jobs status --id application_1735200000_0042",
            "follow": "di spark jobs status --id application_1735200000_0042 --follow",
            "logs": "di spark jobs logs --id application_1735200000_0042 --follow",
            "cancel": "di spark jobs cancel --id application_1735200000_0042",
        },
        deadline="2026-05-15T16:30:00Z",
    )
    assert handle.to_dict() == {
        "kind": "spark.job",
        "id": "application_1735200000_0042",
        "status": "submitted",
        "actions": {
            "poll": "di spark jobs status --id application_1735200000_0042",
            "follow": "di spark jobs status --id application_1735200000_0042 --follow",
            "logs": "di spark jobs logs --id application_1735200000_0042 --follow",
            "cancel": "di spark jobs cancel --id application_1735200000_0042",
        },
        "deadline": "2026-05-15T16:30:00Z",
    }


def test_handle_without_deadline_omits_field() -> None:
    handle = Handle(
        kind="presto.query",
        id="q-001",
        status="running",
        actions={"poll": "di presto query status --id q-001"},
    )
    out = handle.to_dict()
    assert "deadline" not in out
    assert out == {
        "kind": "presto.query",
        "id": "q-001",
        "status": "running",
        "actions": {"poll": "di presto query status --id q-001"},
    }


def test_handle_wrapped_in_envelope_data() -> None:
    # Spec § Handle envelope: handle lives inside data["handle"]; the
    # outer Envelope still echoes identity and ok.
    handle = Handle(
        kind="flink.job",
        id="job-42",
        status="submitted",
        actions={
            "poll": "di flink jobs status --id job-42",
            "cancel": "di flink jobs cancel --id job-42",
        },
    )
    env = Envelope(identity="user", data={"handle": handle.to_dict()})
    assert env.to_dict() == {
        "ok": True,
        "identity": "user",
        "data": {
            "handle": {
                "kind": "flink.job",
                "id": "job-42",
                "status": "submitted",
                "actions": {
                    "poll": "di flink jobs status --id job-42",
                    "cancel": "di flink jobs cancel --id job-42",
                },
            },
        },
    }


