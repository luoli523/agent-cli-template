"""Command registry: register / get / all_specs / clear / as_manifest_data."""

from __future__ import annotations

from mycli import __version__
from mycli.contracts import RiskClass
from mycli.manifest import registry


def test_register_then_get() -> None:
    spec = registry.CommandSpec(name="ping", summary="echo back", risk=RiskClass.READ)
    registry.register(spec)
    assert registry.get("ping") is spec


def test_get_returns_none_for_unknown() -> None:
    assert registry.get("missing") is None


def test_all_specs_sorted_by_name() -> None:
    registry.register(
        registry.CommandSpec(name="zebra", summary="z", risk=RiskClass.READ)
    )
    registry.register(
        registry.CommandSpec(name="alpha", summary="a", risk=RiskClass.READ)
    )
    registry.register(
        registry.CommandSpec(name="mango", summary="m", risk=RiskClass.READ)
    )
    assert [s.name for s in registry.all_specs()] == ["alpha", "mango", "zebra"]


def test_register_last_write_wins() -> None:
    first = registry.CommandSpec(name="x", summary="first", risk=RiskClass.READ)
    second = registry.CommandSpec(name="x", summary="second", risk=RiskClass.READ)
    registry.register(first)
    registry.register(second)
    got = registry.get("x")
    assert got is not None
    assert got.summary == "second"


def test_command_spec_full_to_dict_shape() -> None:
    spec = registry.CommandSpec(
        name="spark jobs submit",
        summary="Submit a Spark job",
        risk=RiskClass.DESTRUCTIVE_COST,
        identity_required=True,
        supports_follow=True,
        supports_async_handle=True,
        scopes=("spark:submit", "spark:read"),
    )
    assert spec.to_dict() == {
        "name": "spark jobs submit",
        "summary": "Submit a Spark job",
        "risk": "destructive-cost",
        "identity_required": True,
        "supports_watch": False,
        "supports_follow": True,
        "supports_async_handle": True,
        "scopes": ["spark:submit", "spark:read"],
    }


def test_as_manifest_data_when_registry_empty() -> None:
    data = registry.as_manifest_data()
    assert data["version"] == __version__
    assert data["commands"] == []


def test_as_manifest_data_includes_registered_commands() -> None:
    registry.register(
        registry.CommandSpec(name="a", summary="A", risk=RiskClass.READ)
    )
    data = registry.as_manifest_data()
    assert data["version"] == __version__
    assert len(data["commands"]) == 1
    assert data["commands"][0]["name"] == "a"


def test_clear_empties_the_registry() -> None:
    registry.register(
        registry.CommandSpec(name="a", summary="A", risk=RiskClass.READ)
    )
    registry.clear()
    assert registry.all_specs() == []
