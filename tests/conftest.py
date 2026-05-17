"""Shared fixtures for the whole tests/ tree.

The command registry and the notice provider are module-level singletons
that any test calling :func:`di.cli.main` will mutate (via subparser
registration and envelope emission). To keep test ordering irrelevant,
this auto-fixture resets both before and after every test.

Contract tests don't touch this state, so the fixture is a no-op for them.
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
