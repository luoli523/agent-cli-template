"""``di update`` subcommand end-to-end.

update extends install with orphan removal: any symlink we previously
planted into a target whose source skill no longer exists upstream is
unlinked. Forward-direction behavior (install, skip, refresh stale,
conflict on user data) is exercised by ``test_install.py``; this file
focuses on the *additional* removal semantics and on confirming the
shared forward behavior still works through the update entry point.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from di.cli import main


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    return h


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    s = tmp_path / "src-skills"
    s.mkdir()
    monkeypatch.setenv("DI_SKILLS_DIR", str(s))
    return s


def _make_skill(source: Path, name: str) -> Path:
    skill = source / name
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"# {name}\n")
    return skill.resolve()


def _make_managed_symlink(target_root: Path, name: str, points_to: Path) -> Path:
    """Pre-create a symlink at the target as if a previous install put it there."""
    target_root.mkdir(parents=True, exist_ok=True)
    link = target_root / name
    link.symlink_to(points_to, target_is_directory=True)
    return link


# --- forward-direction sanity (mirrors install behavior through update) -------


def test_update_with_no_source_succeeds_empty(
    home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DI_SKILLS_DIR", str(tmp_path / "does-not-exist"))
    code = main(["update"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["source"] is None
    assert payload["data"]["installed"] == []
    assert payload["data"]["removed"] == []


def test_update_installs_missing_skills_like_install_does(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill = _make_skill(source, "di-shared")
    code = main(["update"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert len(payload["data"]["installed"]) == 2  # both targets
    assert (home / ".claude" / "skills" / "di-shared").resolve() == skill


def test_update_is_idempotent_with_no_orphans(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")
    main(["update"])  # first run installs
    capsys.readouterr()
    code = main(["update"])  # second run: all skip, no orphans
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["installed"] == []
    assert payload["data"]["removed"] == []
    assert len(payload["data"]["skipped"]) == 2


# --- orphan removal: the new behavior -----------------------------------------


def test_update_removes_orphan_symlink(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Simulate an older install that placed di-old, then was deleted upstream.
    # Source today only has di-shared.
    _make_skill(source, "di-shared")
    stale_source = source / "di-old"
    stale_source.mkdir()
    (stale_source / "SKILL.md").write_text("# stale\n")
    orphan_link = _make_managed_symlink(
        home / ".claude" / "skills", "di-old", stale_source.resolve()
    )
    # Now remove the source for di-old (the upstream "deletion").
    (stale_source / "SKILL.md").unlink()
    stale_source.rmdir()

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    removed = payload["data"]["removed"]
    assert len(removed) == 1
    assert removed[0]["name"] == "di-old"
    assert removed[0]["target"] == "claude"
    assert not orphan_link.exists() and not orphan_link.is_symlink()
    # di-shared still ends up installed.
    assert (home / ".claude" / "skills" / "di-shared").is_symlink()


def test_update_removes_orphan_with_broken_link(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # An orphan whose target was already gone — readlink still tells us
    # the link used to point into our source tree, so it's still ours.
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    orphan = claude_skills / "di-old"
    orphan.symlink_to(source / "di-old-already-gone", target_is_directory=True)

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    removed = payload["data"]["removed"]
    assert any(r["name"] == "di-old" and r["reason"] == "orphan-broken" for r in removed)
    assert not orphan.is_symlink() and not orphan.exists()


def test_update_combined_install_skip_remove(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # End-to-end re-sync: one skill stays (skip), one is new (install),
    # one is dropped upstream (remove).
    _make_skill(source, "di-shared")  # will skip (already linked)
    _make_skill(source, "di-new")     # will install
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    _make_managed_symlink(
        home / ".claude" / "skills", "di-shared", source / "di-shared"
    )
    _make_managed_symlink(
        home / ".claude" / "skills", "di-old", stale.resolve()
    )
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    names_installed = [a["name"] for a in payload["data"]["installed"]]
    names_skipped = [a["name"] for a in payload["data"]["skipped"]]
    names_removed = [a["name"] for a in payload["data"]["removed"]]
    assert names_installed == ["di-new"]
    assert names_skipped == ["di-shared"]
    assert names_removed == ["di-old"]


# --- what update refuses to touch ---------------------------------------------


def test_update_leaves_non_prefixed_symlinks_alone(
    home: Path, source: Path, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A user-created symlink named "my-personal-skill" (no di- prefix)
    # must never be in scope for orphan removal.
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    user_link = claude_skills / "my-personal-skill"
    user_link.symlink_to(tmp_path, target_is_directory=True)

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    assert user_link.is_symlink()  # untouched
    payload = json.loads(captured.out)
    assert payload["data"]["removed"] == []


def test_update_leaves_foreign_symlink_alone(
    home: Path, source: Path, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A symlink with the di- prefix that points OUTSIDE our source tree —
    # not ours to touch. install would classify it as a conflict only if
    # a same-named source skill existed; with no matching source, it just
    # sits there silently. update must respect the same rule.
    _make_skill(source, "di-shared")
    foreign = tmp_path / "foreign-target"
    foreign.mkdir()
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    foreign_link = claude_skills / "di-foreign"
    foreign_link.symlink_to(foreign.resolve(), target_is_directory=True)

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    assert foreign_link.is_symlink()
    assert foreign_link.resolve() == foreign.resolve()
    payload = json.loads(captured.out)
    assert payload["data"]["removed"] == []


def test_update_leaves_real_directory_alone(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A real directory named di-foo with no matching source — user data,
    # not an orphan. install would conflict only with a matching name;
    # with no matching source, update simply leaves it.
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    user_dir = claude_skills / "di-foo"
    user_dir.mkdir()
    sentinel = user_dir / "personal-note.md"
    sentinel.write_text("mine")

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    assert sentinel.read_text() == "mine"
    payload = json.loads(captured.out)
    assert payload["data"]["removed"] == []


# --- conflicts still abort everything -----------------------------------------


def test_update_aborts_on_conflict_and_skips_orphan_removal(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Setup: one valid skill conflicts with a user directory, AND an
    # orphan exists at the same time. Atomic policy means NEITHER the
    # install nor the orphan removal happens until the conflict is fixed.
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    # Conflict: real directory under di-shared
    user_dir = claude_skills / "di-shared"
    user_dir.mkdir()
    # Orphan: managed-looking symlink that would otherwise be removed
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    orphan = _make_managed_symlink(claude_skills, "di-old", stale.resolve())
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.err)
    assert payload["error"]["type"] == "validation"
    # Orphan was NOT removed because the run aborted before apply.
    assert orphan.is_symlink()


# --- flag behavior ------------------------------------------------------------


def test_update_dry_run_reports_but_makes_no_changes(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    orphan = _make_managed_symlink(
        home / ".claude" / "skills", "di-old", stale.resolve()
    )
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["update", "--target", "claude", "--dry-run"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["dry_run"] is True
    # Reports the would-be actions…
    assert len(payload["data"]["installed"]) == 1
    assert len(payload["data"]["removed"]) == 1
    # …but neither the install nor the removal happened.
    assert not (home / ".claude" / "skills" / "di-shared").exists()
    assert orphan.is_symlink()


def test_update_target_filter_scopes_orphan_search(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # An orphan in ~/.codex must not be touched when --target claude.
    _make_skill(source, "di-shared")
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    codex_orphan = _make_managed_symlink(
        home / ".codex" / "skills", "di-old", stale.resolve()
    )
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["update", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    # codex was not scanned, so no removal recorded.
    assert payload["data"]["removed"] == []
    assert codex_orphan.is_symlink()


# --- manifest registration ----------------------------------------------------


def test_update_appears_in_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--manifest"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    specs = {c["name"]: c for c in payload["data"]["commands"]}
    assert "update" in specs
    assert specs["update"]["risk"] == "write"
    assert specs["update"]["identity_required"] is False
