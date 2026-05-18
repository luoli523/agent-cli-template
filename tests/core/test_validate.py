"""``di validate`` subcommand end-to-end."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from di.cli import main


VALID_SKILL_MD = """---
name: {name}
description: >
  Test fixture skill. TRIGGER when: tests are running. DO NOT TRIGGER when: not.
maintainer:
  - owner@example.com
---

# {name}

Body line.
"""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Construct a minimal valid repo layout under tmp_path."""
    r = tmp_path / "repo"
    r.mkdir()
    (r / "CLAUDE.md").write_text("# claude\n")
    (r / "AGENTS.md").symlink_to("CLAUDE.md")
    (r / "pyproject.toml").write_text("[project]\nname='x'\n")
    (r / "skills").mkdir()
    docs = r / "docs"
    docs.mkdir()
    for sub in ("specs", "decisions", "explainers"):
        (docs / sub).mkdir()
    monkeypatch.setenv("DI_SKILLS_DIR", str(r / "skills"))
    return r


def _write_skill(repo: Path, name: str) -> Path:
    skill = repo / "skills" / name
    skill.mkdir()
    (skill / "SKILL.md").write_text(VALID_SKILL_MD.format(name=name))
    return skill


# --- end-to-end happy path ----------------------------------------------------


def test_validate_clean_repo_is_healthy(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(repo, "di-shared")
    code = main(["validate"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["data"]["overall"] == "healthy"


def test_validate_scope_skills_skips_repo_checks(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(repo, "di-shared")
    code = main(["validate", "--scope", "skills"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert all(not c["name"].startswith("repo/") for c in payload["data"]["checks"])


def test_validate_scope_repo_skips_skills_checks(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(repo, "di-shared")
    code = main(["validate", "--scope", "repo"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert all(not c["name"].startswith("skills/") for c in payload["data"]["checks"])


# --- end-to-end failure paths -------------------------------------------------


def test_validate_skill_missing_trigger_markers_is_unhealthy(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill = repo / "skills" / "di-bad"
    skill.mkdir()
    # description lacks both TRIGGER markers — fail per contract
    (skill / "SKILL.md").write_text(
        "---\nname: di-bad\ndescription: 'No markers here.'\n"
        "maintainer: [owner@example.com]\n---\n\n# di-bad\nbody\n"
    )
    code = main(["validate", "--scope", "skills"])
    captured = capsys.readouterr()
    assert code == 5
    payload = json.loads(captured.err)
    assert payload["ok"] is False
    assert payload["error"]["detail"]["overall"] == "unhealthy"


def test_validate_repo_with_broken_agents_md_is_unhealthy(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "AGENTS.md").unlink()
    (repo / "AGENTS.md").write_text("not a symlink")
    code = main(["validate", "--scope", "repo"])
    captured = capsys.readouterr()
    assert code == 5
    payload = json.loads(captured.err)
    failing = [c for c in payload["error"]["detail"]["checks"] if c["status"] == "fail"]
    assert any(c["name"] == "repo/agents_symlink" for c in failing)


# --- --skills-dir override and unresolved cases -------------------------------


def test_validate_uses_explicit_skills_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Build a skills dir but no repo around it; --scope skills should
    # only walk the override and succeed.
    skills = tmp_path / "elsewhere" / "skills"
    skills.mkdir(parents=True)
    monkeypatch.delenv("DI_SKILLS_DIR", raising=False)
    code = main(["validate", "--scope", "skills", "--skills-dir", str(skills)])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["skills_dir"].endswith("skills")


def test_validate_missing_skills_dir_is_unhealthy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DI_SKILLS_DIR", str(tmp_path / "absent"))
    code = main(["validate", "--scope", "skills"])
    captured = capsys.readouterr()
    assert code == 5
    payload = json.loads(captured.err)
    assert any(
        c["name"] == "skills_root" and c["status"] == "fail"
        for c in payload["error"]["detail"]["checks"]
    )


# --- live-repo gate ----------------------------------------------------------


def test_validate_passes_against_live_repo_skills(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Live-repo regression gate.

    Runs the validator against the *real* skills/ directory that ships
    with this checkout. The point is to keep di-shared (and any future
    bundled skill) honest: if someone edits the SKILL.md and breaks the
    contract, this test goes red — same red CI consumers will see.

    Uses the package walk-up resolution (no DI_SKILLS_DIR override) so
    the test exercises exactly what end-users hit.
    """
    monkeypatch.delenv("DI_SKILLS_DIR", raising=False)
    code = main(["validate", "--scope", "skills"])
    captured = capsys.readouterr()
    if code != 0:
        # Surface the failing envelope to the test log so debugging
        # doesn't require a separate `di validate` invocation.
        raise AssertionError(
            f"live skills/ failed validation:\n"
            f"stdout={captured.out}\nstderr={captured.err}"
        )
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "healthy"
    names = {c["name"] for c in payload["data"]["checks"]}
    assert "skills/di-shared" in names


# --- manifest registration ---------------------------------------------------


def test_validate_appears_in_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--manifest"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    specs = {c["name"]: c for c in payload["data"]["commands"]}
    assert "validate" in specs
    assert specs["validate"]["risk"] == "read"
    assert specs["validate"]["identity_required"] is False
