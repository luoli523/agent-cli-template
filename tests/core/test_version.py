"""``di version`` subcommand end-to-end."""

from __future__ import annotations

import json

import pytest

from di import __version__
from di.cli import main


def test_version_command_emits_envelope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["version"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["identity"] == "local"
    assert payload["data"]["version"] == __version__


def test_version_command_data_includes_runtime_info(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["version"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)["data"]
    # Tells AI agents which Python and OS the CLI runs on — useful for
    # doctor-style triage when something behaves unexpectedly.
    assert "python" in data
    assert "platform" in data
    # python field is dotted version string like "3.13.5"
    assert data["python"].count(".") == 2


def test_version_command_writes_nothing_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["version"])
    captured = capsys.readouterr()
    assert captured.err == ""


def test_version_pretty_format_after_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Standard convention (matches git, kubectl, terraform): flags go
    # AFTER the subcommand name. `di --format pretty version` does not
    # propagate --format to the subparser (argparse parents= quirk),
    # but `di version --format pretty` always works.
    code = main(["version", "--format", "pretty"])
    captured = capsys.readouterr()
    assert code == 0
    assert "\n  " in captured.out  # indent=2
    payload = json.loads(captured.out)
    assert payload["ok"] is True


def test_version_appears_in_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--manifest"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    commands = payload["data"]["commands"]
    names = {c["name"] for c in commands}
    assert "version" in names

    version_spec = next(c for c in commands if c["name"] == "version")
    assert version_spec["risk"] == "read"
    assert version_spec["identity_required"] is False
