"""``mycli hello`` subcommand end-to-end."""

from __future__ import annotations

import json

import pytest

from mycli.cli import main


def test_hello_returns_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["hello", "--name", "World"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["data"]["greeting"] == "Hello, World!"


def test_hello_format_pretty(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["hello", "--name", "Alice", "--format", "pretty"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Hello, Alice!" in captured.out


def test_hello_missing_name_exits_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["hello"])
    assert exc.value.code != 0


def test_hello_blank_name_is_validation_error(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["hello", "--name", "   "])
    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.err)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "validation"
