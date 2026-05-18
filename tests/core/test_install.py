"""``di install`` subcommand end-to-end.

Every test runs against a tmp_path-rooted home and a tmp_path-rooted
source skills directory (via ``MYCLI_SKILLS_DIR``) so nothing escapes into
the developer's real ``~/.claude`` / ``~/.codex``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mycli.cli import main


# --- fixtures ------------------------------------------------------------------


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated ``$HOME`` for the duration of a test.

    install reads ``os.path.expanduser("~")`` to find ``~/.claude`` and
    ``~/.codex``; pinning ``HOME`` to a fresh tmp dir keeps every test
    independent and prevents accidental writes to the developer's real
    home directory.
    """
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    return h


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated source skills directory.

    Setting ``MYCLI_SKILLS_DIR`` short-circuits the package-walk source
    resolution, so tests do not depend on the layout of the surrounding
    repo (which has no ``skills/`` directory until T9/T10).
    """
    s = tmp_path / "src-skills"
    s.mkdir()
    monkeypatch.setenv("MYCLI_SKILLS_DIR", str(s))
    return s


def _make_skill(source: Path, name: str) -> Path:
    """Create a minimal valid skill directory and return its absolute path."""
    skill = source / name
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"# {name}\n")
    return skill.resolve()


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict, str]:
    code = main(args)
    captured = capsys.readouterr()
    out = captured.out or captured.err
    return code, json.loads(out), captured.err


# --- discovery edge cases ------------------------------------------------------


def test_install_with_empty_skills_dir_succeeds(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # source is created but contains no skills; install should still
    # succeed with empty buckets so agents bootstrapping a fresh repo
    # don't see a confusing failure.
    code, payload, _ = _run(["install"], capsys)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["installed"] == []
    assert payload["data"]["skipped"] == []
    assert payload["data"]["updated"] == []


def test_install_with_no_source_succeeds_empty(
    home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Point MYCLI_SKILLS_DIR at a non-existent path — source resolution
    # returns None, but install still succeeds (source=None in envelope).
    monkeypatch.setenv("MYCLI_SKILLS_DIR", str(tmp_path / "does-not-exist"))
    code, payload, _ = _run(["install"], capsys)
    assert code == 0
    assert payload["data"]["source"] is None
    assert payload["data"]["installed"] == []


def test_install_ignores_non_skill_entries(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Three entries that look like skills but are not:
    (source / "README.md").write_text("not a directory")
    (source / "no-prefix").mkdir()
    (source / "no-prefix" / "SKILL.md").write_text("# wrong prefix")
    (source / "mycli-incomplete").mkdir()  # missing SKILL.md
    _make_skill(source, "mycli-valid")

    code, payload, _ = _run(["install"], capsys)
    assert code == 0
    names = [a["name"] for a in payload["data"]["installed"]]
    assert names == ["mycli-valid"] * 2  # one per target


def test_install_skips_skill_template(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The fork-starting-point template ships under skills/ but must
    # never be installed into AI tool directories — it teaches nothing
    # at runtime. Enforced via EXCLUDED_FROM_INSTALL in _sync.py.
    _make_skill(source, "mycli-skill-template")
    _make_skill(source, "mycli-real")

    code, payload, _ = _run(["install"], capsys)
    assert code == 0
    names = {a["name"] for a in payload["data"]["installed"]}
    assert names == {"mycli-real"}
    assert not (home / ".claude" / "skills" / "mycli-skill-template").exists()
    assert not (home / ".codex" / "skills" / "mycli-skill-template").exists()


# --- happy path ----------------------------------------------------------------


def test_install_creates_symlinks_under_both_targets(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill = _make_skill(source, "mycli-shared")

    code, payload, _ = _run(["install"], capsys)
    assert code == 0

    claude_link = home / ".claude" / "skills" / "mycli-shared"
    codex_link = home / ".codex" / "skills" / "mycli-shared"
    assert claude_link.is_symlink()
    assert codex_link.is_symlink()
    assert claude_link.resolve() == skill
    assert codex_link.resolve() == skill

    targets = {a["target"] for a in payload["data"]["installed"]}
    assert targets == {"claude", "codex"}


def test_install_is_idempotent(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")

    main(["install"])  # first run installs
    capsys.readouterr()  # discard
    code, payload, _ = _run(["install"], capsys)  # second run skips
    assert code == 0
    assert payload["data"]["installed"] == []
    assert len(payload["data"]["skipped"]) == 2
    for row in payload["data"]["skipped"]:
        assert row["reason"] == "already-linked"


# --- update paths --------------------------------------------------------------


def test_install_replaces_broken_symlink(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    dead = claude_skills / "mycli-shared"
    dead.symlink_to("/nonexistent/path", target_is_directory=True)

    code, payload, _ = _run(["install", "--target", "claude"], capsys)
    assert code == 0
    updates = payload["data"]["updated"]
    assert len(updates) == 1
    assert updates[0]["reason"] == "broken-symlink"
    assert dead.is_symlink() and dead.resolve() == (source / "mycli-shared").resolve()


def test_install_rewrites_stale_source_symlink(
    home: Path, source: Path, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Existing symlink points at a *different* skill inside our source
    # tree (e.g., the skill was renamed). install rewrites it.
    skill_new = _make_skill(source, "mycli-shared")
    stale_target = source / "mycli-old-name"
    stale_target.mkdir()
    (stale_target / "SKILL.md").write_text("# old")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    link = claude_skills / "mycli-shared"
    link.symlink_to(stale_target.resolve(), target_is_directory=True)

    code, payload, _ = _run(["install", "--target", "claude"], capsys)
    assert code == 0
    updates = payload["data"]["updated"]
    assert len(updates) == 1
    assert updates[0]["reason"] == "stale-source"
    assert link.resolve() == skill_new


# --- conflict paths ------------------------------------------------------------


def test_install_aborts_on_real_directory_conflict(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    user_owned = claude_skills / "mycli-shared"
    user_owned.mkdir()
    sentinel = user_owned / "my-notes.md"
    sentinel.write_text("user's own work")

    code = main(["install"])
    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.err)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "validation"
    conflicts = payload["error"]["detail"]["conflicts"]
    assert any(c["reason"] == "real-directory" for c in conflicts)
    # Atomic abort: nothing was installed, user data is untouched.
    assert sentinel.read_text() == "user's own work"
    assert not (home / ".codex" / "skills" / "mycli-shared").exists()


def test_install_aborts_on_foreign_symlink(
    home: Path, source: Path, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _make_skill(source, "mycli-shared")
    foreign = tmp_path / "external-target"
    foreign.mkdir()
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    link = claude_skills / "mycli-shared"
    link.symlink_to(foreign.resolve(), target_is_directory=True)

    code = main(["install"])
    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.err)
    conflicts = payload["error"]["detail"]["conflicts"]
    assert any(c["reason"] == "foreign-symlink" for c in conflicts)
    assert link.resolve() == foreign.resolve()  # untouched


# --- flag behavior -------------------------------------------------------------


def test_install_dry_run_makes_no_filesystem_changes(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")

    code, payload, _ = _run(["install", "--dry-run"], capsys)
    assert code == 0
    assert payload["data"]["dry_run"] is True
    # Envelope still reports what *would* happen…
    assert len(payload["data"]["installed"]) == 2
    # …but the filesystem is untouched.
    assert not (home / ".claude").exists()
    assert not (home / ".codex").exists()


def test_install_target_filter_only_touches_chosen_tool(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")

    code, payload, _ = _run(["install", "--target", "claude"], capsys)
    assert code == 0
    assert (home / ".claude" / "skills" / "mycli-shared").is_symlink()
    assert not (home / ".codex").exists()
    assert set(payload["data"]["targets"]) == {"claude"}


def test_install_pretty_format(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "mycli-shared")
    code = main(["install", "--format", "pretty"])
    captured = capsys.readouterr()
    assert code == 0
    assert "\n  " in captured.out  # indent=2
    payload = json.loads(captured.out)
    assert payload["ok"] is True


# --- manifest registration -----------------------------------------------------


def test_install_appears_in_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--manifest"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    specs = {c["name"]: c for c in payload["data"]["commands"]}
    assert "install" in specs
    assert specs["install"]["risk"] == "write"
    assert specs["install"]["identity_required"] is False
