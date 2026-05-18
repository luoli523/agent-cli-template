"""Surface of ``di.contracts``: pin the exported symbols.

If you find yourself adjusting the expected set below, ask: is this a
real protocol change that needs ADR approval? Adding to the public API
is fine; removing or renaming is a contract break.
"""

from __future__ import annotations

import mycli.contracts as c


EXPECTED_PUBLIC_API: frozenset[str] = frozenset({
    "Envelope",
    "ErrDetail",
    "ErrorEnvelope",
    "ErrorType",
    "ExitCode",
    "Handle",
    "Meta",
    "NoticeType",
    "RiskClass",
    "RiskDetail",
})


def test_public_api_matches_expected() -> None:
    assert set(c.__all__) == EXPECTED_PUBLIC_API


def test_every_exported_name_is_resolvable() -> None:
    for name in c.__all__:
        assert hasattr(c, name), f"{name} declared in __all__ but not bound on module"


def test_no_unexpected_exports() -> None:
    # Public symbols are exactly what __all__ promises; nothing leaks.
    leaked = {
        n for n in dir(c)
        if not n.startswith("_") and n not in EXPECTED_PUBLIC_API
        # tolerate submodule names; the public API is the curated set
        and n not in {"envelope", "error_type", "exit_code", "handle", "notice", "risk"}
    }
    assert leaked == set(), f"Unexpected public names: {leaked}"
