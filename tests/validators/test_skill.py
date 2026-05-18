"""Per-skill-directory validator end-to-end tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from di.validators.skill import validate_skill, validate_skills_root


VALID_SKILL_MD = """---
name: {name}
description: >
  Test skill body. TRIGGER when: test runs. DO NOT TRIGGER when: not a test.
maintainer:
  - owner@example.com
---

# {name}

Body line.
"""


def _write_skill(root: Path, name: str, body: str | None = None) -> Path:
    skill = root / name
    skill.mkdir()
    text = body if body is not None else VALID_SKILL_MD.format(name=name)
    (skill / "SKILL.md").write_text(text)
    return skill


# --- single-skill happy + filesystem failures --------------------------------


def test_valid_skill_returns_ok(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path, "di-shared")
    check = validate_skill(skill)
    assert check.status == "ok"
    assert check.name == "skills/di-shared"


def test_skill_missing_skill_md_is_fail(tmp_path: Path) -> None:
    skill = tmp_path / "di-incomplete"
    skill.mkdir()
    check = validate_skill(skill)
    assert check.status == "fail"
    assert "SKILL.md" in check.message


def test_skill_wrong_prefix_is_fail(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path, "de-other")
    check = validate_skill(skill)
    assert check.status == "fail"
    assert "di-" in check.message


def test_nested_skill_is_fail(tmp_path: Path) -> None:
    outer = _write_skill(tmp_path, "di-outer")
    inner = outer / "di-inner"
    inner.mkdir()
    (inner / "SKILL.md").write_text(VALID_SKILL_MD.format(name="di-inner"))
    check = validate_skill(outer)
    assert check.status == "fail"
    assert "nested" in check.message


def test_skill_with_references_subdir_is_ok(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path, "di-shared")
    refs = skill / "references"
    refs.mkdir()
    (refs / "workflow.md").write_text("# notes")
    check = validate_skill(skill)
    assert check.status == "ok"


def test_skill_with_empty_body_is_fail(tmp_path: Path) -> None:
    body = (
        "---\nname: di-shared\n"
        "description: 'TRIGGER when: x. DO NOT TRIGGER when: y.'\n"
        "maintainer: [owner@example.com]\n---\n\n   \n"
    )
    skill = _write_skill(tmp_path, "di-shared", body=body)
    check = validate_skill(skill)
    assert check.status == "fail"
    assert "empty" in check.message or "H1" in check.message


def test_skill_without_h1_is_fail(tmp_path: Path) -> None:
    body = (
        "---\nname: di-shared\n"
        "description: 'TRIGGER when: x. DO NOT TRIGGER when: y.'\n"
        "maintainer: [owner@example.com]\n---\n\nNo heading here.\n"
    )
    skill = _write_skill(tmp_path, "di-shared", body=body)
    check = validate_skill(skill)
    assert check.status == "fail"
    assert "H1" in check.message


def test_skill_overlong_lines_is_warn_not_fail(tmp_path: Path) -> None:
    long_line = "x" * 250
    body = (
        "---\nname: di-shared\n"
        "description: 'TRIGGER when: x. DO NOT TRIGGER when: y.'\n"
        "maintainer: [owner@example.com]\n---\n\n"
        "# di-shared\n\n"
        f"{long_line}\n"
    )
    skill = _write_skill(tmp_path, "di-shared", body=body)
    check = validate_skill(skill)
    assert check.status == "warn"
    assert "chars" in check.message


# --- skills-root level --------------------------------------------------------


def test_validate_skills_root_missing(tmp_path: Path) -> None:
    checks = validate_skills_root(tmp_path / "absent")
    assert checks[0].name == "skills_root"
    assert checks[0].status == "fail"


def test_validate_skills_root_empty_is_ok(tmp_path: Path) -> None:
    checks = validate_skills_root(tmp_path)
    assert any(c.name == "skills_root" and c.status == "ok" for c in checks)


def test_validate_skills_root_stray_files_are_warn(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("loose file")
    _write_skill(tmp_path, "di-shared")
    checks = validate_skills_root(tmp_path)
    root_check = next(c for c in checks if c.name == "skills_root")
    assert root_check.status == "warn"
    assert root_check.detail and "README.md" in root_check.detail["stray"]


def test_validate_skills_root_walks_every_skill(tmp_path: Path) -> None:
    _write_skill(tmp_path, "di-shared")
    _write_skill(tmp_path, "di-other")
    checks = validate_skills_root(tmp_path)
    names = {c.name for c in checks}
    assert "skills/di-shared" in names
    assert "skills/di-other" in names


@pytest.mark.skip(reason="duplicate detection by directory name requires filesystem-level dup, which is impossible — covered by name-mismatch check instead")
def test_duplicate_skill_names_detected(tmp_path: Path) -> None:
    # On disk, two directories cannot share a name. The duplicate case
    # only arises if a sub-team mistypes a frontmatter `name` to collide
    # with another directory's name — that's caught by the name-vs-dir
    # mismatch check inside validate_frontmatter, not here.
    ...
