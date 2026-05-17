"""Shared fixtures for runtime tests.

Both the command registry and the notice provider are module-level
singletons. Tests that mutate them must run against a clean baseline,
otherwise ordering would matter. This auto-fixture resets both before
and after every runtime test.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from di.manifest import registry
from di.runtime.output import default_notice_provider, set_notice_provider


@pytest.fixture(autouse=True)
def clean_runtime_globals() -> Iterator[None]:
    registry.clear()
    set_notice_provider(default_notice_provider)
    yield
    registry.clear()
    set_notice_provider(default_notice_provider)
