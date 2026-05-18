"""Parsing behavior for every standard flag in spec § Standard flags."""

from __future__ import annotations

import pytest

from mycli.cli import build_parser
from mycli.runtime.flags import VALID_FORMATS


def test_format_default_is_json() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.format == "json"


def test_format_accepts_all_documented_choices() -> None:
    parser = build_parser()
    for fmt in VALID_FORMATS:
        args = parser.parse_args(["--format", fmt])
        assert args.format == fmt


def test_format_rejects_unknown_value() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--format", "yaml"])


def test_as_flag_pass_through_arbitrary_role() -> None:
    # No hardcoded role enum in core — RAM defines the set, mycli-cli is a
    # transparent conduit. Any non-empty string parses.
    parser = build_parser()
    for role in ("user", "service", "service-account-spark", "oncall"):
        args = parser.parse_args(["--as", role])
        assert args.identity_as == role


def test_profile_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--profile", "prod"])
    assert args.profile == "prod"


def test_dry_run_defaults_false_and_flag_sets_true() -> None:
    parser = build_parser()
    assert parser.parse_args([]).dry_run is False
    assert parser.parse_args(["--dry-run"]).dry_run is True


def test_yes_flag() -> None:
    parser = build_parser()
    assert parser.parse_args([]).yes is False
    assert parser.parse_args(["--yes"]).yes is True


def test_watch_and_follow_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--watch", "--follow"])
    assert args.watch is True
    assert args.follow is True


def test_timeout_flag_accepts_arbitrary_string() -> None:
    # Duration parsing is the caller's responsibility (humanfriendly /
    # ISO-8601 / raw seconds — to be decided per command). v1 accepts
    # any string and passes it down.
    parser = build_parser()
    args = parser.parse_args(["--timeout", "30s"])
    assert args.timeout == "30s"
    args = parser.parse_args(["--timeout", "PT5M"])
    assert args.timeout == "PT5M"


def test_page_flags_parse_as_int_with_correct_dest() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["--page-all", "--page-size", "100", "--page-limit", "5"]
    )
    assert args.page_all is True
    assert args.page_size == 100
    assert args.page_limit == 5


def test_page_size_rejects_non_int() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--page-size", "many"])


def test_manifest_flag_default_and_set() -> None:
    parser = build_parser()
    assert parser.parse_args([]).manifest is False
    assert parser.parse_args(["--manifest"]).manifest is True
