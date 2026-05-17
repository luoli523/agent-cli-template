"""End-to-end behavior of the argparse root and main()."""

from __future__ import annotations

import json

import pytest

from di import __version__
from di.cli import main


def test_main_no_args_prints_help_and_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main([])
    captured = capsys.readouterr()
    assert code == 0
    # argparse help is written to stdout when called via print_help.
    assert "usage" in captured.out.lower()


def test_main_manifest_emits_envelope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["--manifest"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["identity"] == "local"
    assert payload["data"]["version"] == __version__
    assert payload["data"]["commands"] == []
    # Stderr stays clean for success.
    assert captured.err == ""


def test_main_manifest_pretty_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["--manifest", "--format", "pretty"])
    captured = capsys.readouterr()
    assert code == 0
    # Pretty uses indent=2; flat json would not have indented lines.
    assert "\n  " in captured.out
    payload = json.loads(captured.out)
    assert payload["ok"] is True


def test_main_version_flag_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_main_unknown_flag_exits_two() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--no-such-flag"])
    assert exc_info.value.code == 2


def test_main_manifest_with_unimplemented_format_falls_back_to_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Spec § Standard flags lists csv/ndjson/table. v1 renders them as
    # json so AI agents still parse successfully.
    code = main(["--manifest", "--format", "csv"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
