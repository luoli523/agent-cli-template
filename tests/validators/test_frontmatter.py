"""Tests for SKILL.md frontmatter parsing and schema validation."""

from __future__ import annotations

import pytest

from di.validators.frontmatter import (
    FrontmatterError,
    parse_skill_frontmatter,
    validate_frontmatter,
)


def _make(text: str) -> dict:
    """Return parsed frontmatter dict for a given full-text fixture."""
    return parse_skill_frontmatter(text).data


VALID_TEXT = """---
name: di-shared
description: >
  Shared di-cli authorization and notice protocol used by every other di-* skill.
  TRIGGER when: any di-* skill is loaded; the agent needs the di envelope contract.
  DO NOT TRIGGER when: the user is asking a general question with no di-cli action involved.
maintainer:
  - owner@example.com
version: 0.1.0
metadata:
  requires:
    bins: ["di"]
  cliHelp: "di --help"
---

# di-shared

Body content.
"""


# --- parsing -----------------------------------------------------------------


def test_parses_valid_frontmatter() -> None:
    result = parse_skill_frontmatter(VALID_TEXT)
    assert result.data["name"] == "di-shared"
    assert result.body.lstrip().startswith("# di-shared")


def test_rejects_text_without_frontmatter() -> None:
    with pytest.raises(FrontmatterError, match="must start with"):
        parse_skill_frontmatter("# just a markdown file\n")


def test_rejects_malformed_yaml() -> None:
    bad = "---\nname: [unclosed\n---\n# body\n"
    with pytest.raises(FrontmatterError, match="malformed"):
        parse_skill_frontmatter(bad)


def test_rejects_non_mapping_frontmatter() -> None:
    bad = "---\n- a\n- b\n---\n# body\n"
    with pytest.raises(FrontmatterError, match="mapping"):
        parse_skill_frontmatter(bad)


# --- schema: valid -----------------------------------------------------------


def test_valid_frontmatter_yields_no_issues() -> None:
    data = _make(VALID_TEXT)
    assert validate_frontmatter(data, directory_name="di-shared") == []


# --- schema: name ------------------------------------------------------------


def test_missing_name_is_fail() -> None:
    data = _make(VALID_TEXT)
    del data["name"]
    issues = validate_frontmatter(data, directory_name="di-shared")
    assert any(i.status == "fail" and i.field == "name" for i in issues)


def test_wrong_prefix_is_fail() -> None:
    data = _make(VALID_TEXT)
    data["name"] = "de-shared"  # wrong prefix
    issues = validate_frontmatter(data, directory_name="de-shared")
    assert any("di-" in i.message for i in issues if i.status == "fail")


def test_name_mismatch_with_directory_is_fail() -> None:
    data = _make(VALID_TEXT)
    issues = validate_frontmatter(data, directory_name="di-other")
    assert any(
        i.status == "fail" and i.field == "name" and "does not match" in i.message
        for i in issues
    )


def test_non_kebab_name_is_fail() -> None:
    data = _make(VALID_TEXT)
    data["name"] = "di_shared"  # underscore not allowed
    issues = validate_frontmatter(data, directory_name="di_shared")
    assert any("kebab" in i.message for i in issues if i.status == "fail")


# --- schema: description -----------------------------------------------------


def test_missing_trigger_markers_is_fail() -> None:
    data = _make(VALID_TEXT)
    data["description"] = "Just a regular description without the markers."
    issues = validate_frontmatter(data, directory_name="di-shared")
    msgs = [i.message for i in issues if i.status == "fail"]
    assert any("TRIGGER when:" in m for m in msgs)
    assert any("DO NOT TRIGGER when:" in m for m in msgs)


def test_oversize_description_is_fail() -> None:
    data = _make(VALID_TEXT)
    data["description"] = "TRIGGER when: x. DO NOT TRIGGER when: y. " + "padding " * 200
    issues = validate_frontmatter(data, directory_name="di-shared")
    assert any("must be ≤" in i.message for i in issues if i.status == "fail")


# --- schema: maintainer ------------------------------------------------------


def test_maintainer_must_be_list() -> None:
    data = _make(VALID_TEXT)
    data["maintainer"] = "owner@example.com"  # string not list
    issues = validate_frontmatter(data, directory_name="di-shared")
    assert any(i.status == "fail" and i.field == "maintainer" for i in issues)


def test_maintainer_entry_must_look_like_email() -> None:
    data = _make(VALID_TEXT)
    data["maintainer"] = ["not-an-email"]
    issues = validate_frontmatter(data, directory_name="di-shared")
    assert any("email" in i.message for i in issues if i.status == "fail")


# --- schema: optional fields -------------------------------------------------


def test_bad_version_is_warn_not_fail() -> None:
    data = _make(VALID_TEXT)
    data["version"] = "v1"  # not semver
    issues = validate_frontmatter(data, directory_name="di-shared")
    versions = [i for i in issues if i.field == "version"]
    assert versions and all(i.status == "warn" for i in versions)


def test_bad_metadata_bins_is_fail() -> None:
    data = _make(VALID_TEXT)
    data["metadata"]["requires"]["bins"] = "di"  # must be list
    issues = validate_frontmatter(data, directory_name="di-shared")
    assert any(i.field == "metadata.requires.bins" for i in issues)


def test_unknown_top_level_field_is_warn() -> None:
    data = _make(VALID_TEXT)
    data["maintainers"] = ["typo@example.com"]  # plural typo
    issues = validate_frontmatter(data, directory_name="di-shared")
    unknowns = [i for i in issues if "unknown" in i.message]
    assert unknowns and all(i.status == "warn" for i in unknowns)
