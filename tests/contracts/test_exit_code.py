"""ExitCode catalogue: spec § Exit codes must be 1:1 with this enum."""

from __future__ import annotations

from mycli.contracts.exit_code import ExitCode


def test_exit_code_values_match_spec() -> None:
    # Spec § Exit codes — every entry below is load-bearing for AI agents
    # branching on shell exit codes. Any change is a contract change.
    assert ExitCode.OK == 0
    assert ExitCode.API == 1
    assert ExitCode.VALIDATION == 2
    assert ExitCode.AUTH == 3
    assert ExitCode.NETWORK == 4
    assert ExitCode.INTERNAL == 5
    assert ExitCode.COST_GATE == 6
    assert ExitCode.CONFIRMATION_REQUIRED == 10
    assert ExitCode.DEADLINE == 11


def test_exit_code_count_is_exactly_nine() -> None:
    # If you find yourself adjusting this number, ask: is this a real
    # protocol change that needs ADR approval?
    assert len(list(ExitCode)) == 9


def test_exit_code_is_int_compatible() -> None:
    # IntEnum so sys.exit() and shell consumers accept the value directly.
    assert int(ExitCode.CONFIRMATION_REQUIRED) == 10
