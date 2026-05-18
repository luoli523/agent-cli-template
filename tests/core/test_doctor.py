"""``di doctor`` subcommand end-to-end.

doctor is read-only — it inspects the same state install/update would
mutate and reports drift. Tests confirm:

* Each individual check (python / source / target_dirs / sync_status)
  returns the right status for both ok and broken inputs.
* The overall grade is worst-status-wins.
* Unhealthy routes through the error envelope on stderr with exit 5;
  healthy / degraded route through stdout with exit 0.
* The filesystem is never modified.
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
    target_root.mkdir(parents=True, exist_ok=True)
    link = target_root / name
    link.symlink_to(points_to, target_is_directory=True)
    return link


def _checks_by_name(payload: dict) -> dict[str, dict]:
    return {c["name"]: c for c in payload["checks"]}


# --- happy paths ---------------------------------------------------------------


def test_doctor_all_healthy(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Setup: install di-shared into both targets so sync_status = ok.
    skill = _make_skill(source, "di-shared")
    _make_managed_symlink(home / ".claude" / "skills", "di-shared", skill)
    _make_managed_symlink(home / ".codex" / "skills", "di-shared", skill)

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["data"]["overall"] == "healthy"
    checks = _checks_by_name(payload["data"])
    assert checks["python"]["status"] == "ok"
    assert checks["source"]["status"] == "ok"
    assert checks["target_dirs"]["status"] == "ok"
    assert checks["sync_status"]["status"] == "ok"


def test_doctor_python_check_includes_version(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["doctor"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    py = _checks_by_name(payload["data"])["python"]
    # Don't assert exact version (varies per CI); just confirm the field
    # is dotted X.Y.Z and the floor is reported.
    assert py["detail"]["required"] == "3.9"
    assert py["detail"]["actual"].count(".") == 2


# --- target_dirs warning -------------------------------------------------------


def test_doctor_warns_when_target_dirs_missing(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # No target dirs exist at all → both missing → warn → degraded.
    skill = _make_skill(source, "di-shared")  # noqa: F841

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0  # degraded still exits 0
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "degraded"
    target_dirs = _checks_by_name(payload["data"])["target_dirs"]
    assert target_dirs["status"] == "warn"
    missing = target_dirs["detail"]["missing"]
    assert {m["target"] for m in missing} == {"claude", "codex"}


def test_doctor_target_filter_scopes_dir_check(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Only claude exists; --target claude → all green.
    skill = _make_skill(source, "di-shared")
    _make_managed_symlink(home / ".claude" / "skills", "di-shared", skill)

    code = main(["doctor", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "healthy"


# --- source fail ---------------------------------------------------------------


def test_doctor_fails_when_source_unresolved(
    home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DI_SKILLS_DIR", str(tmp_path / "does-not-exist"))

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 5  # unhealthy → ExitCode.INTERNAL
    payload = json.loads(captured.err)  # error envelope on stderr
    assert payload["ok"] is False
    assert payload["error"]["type"] == "validation"
    inner = payload["error"]["detail"]
    assert inner["overall"] == "unhealthy"
    checks = _checks_by_name(inner)
    assert checks["source"]["status"] == "fail"
    # sync_status is skipped when source is unresolved
    assert checks["sync_status"]["status"] == "ok"
    assert "source unresolved" in checks["sync_status"]["detail"]["reason"]


# --- sync_status drift ---------------------------------------------------------


def test_doctor_reports_needs_install(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")  # exists in source, not linked anywhere
    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".codex" / "skills").mkdir(parents=True)

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0  # warn → degraded → exit 0
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "degraded"
    sync = _checks_by_name(payload["data"])["sync_status"]
    assert sync["status"] == "warn"
    assert len(sync["detail"]["needs_install"]) == 2  # both targets
    assert sync["detail"]["conflicts"] == []
    assert sync["hint"] == "run `di update` to re-sync"


def test_doctor_reports_orphan(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill = _make_skill(source, "di-shared")
    _make_managed_symlink(home / ".claude" / "skills", "di-shared", skill)
    _make_managed_symlink(home / ".codex" / "skills", "di-shared", skill)
    # Add an orphan: managed-looking symlink whose source no longer exists
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    _make_managed_symlink(home / ".claude" / "skills", "di-old", stale.resolve())
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "degraded"
    sync = _checks_by_name(payload["data"])["sync_status"]
    assert sync["status"] == "warn"
    orphans = sync["detail"]["orphans"]
    assert len(orphans) == 1
    assert orphans[0]["name"] == "di-old"


def test_doctor_fails_on_conflict(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    (home / ".codex" / "skills").mkdir(parents=True)
    # Real directory conflict at di-shared
    (claude_skills / "di-shared").mkdir()

    code = main(["doctor"])
    captured = capsys.readouterr()
    assert code == 5
    payload = json.loads(captured.err)
    assert payload["error"]["detail"]["overall"] == "unhealthy"
    sync = _checks_by_name(payload["error"]["detail"])["sync_status"]
    assert sync["status"] == "fail"
    assert len(sync["detail"]["conflicts"]) >= 1
    assert "di update" in (sync["hint"] or "")


def test_doctor_conflict_dominates_orphan_in_grade(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Setup both a conflict and an orphan; overall must be unhealthy
    # (conflict's fail beats orphan's warn).
    _make_skill(source, "di-shared")
    claude_skills = home / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    (claude_skills / "di-shared").mkdir()  # conflict
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    _make_managed_symlink(claude_skills, "di-old", stale.resolve())
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["doctor", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 5
    payload = json.loads(captured.err)
    assert payload["error"]["detail"]["overall"] == "unhealthy"


# --- combined-state realism ---------------------------------------------------


def test_doctor_combined_warn_buckets(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # One ok (already linked), one needs_install (new in source), one orphan
    # (gone from source). Should be a single warn with three populated buckets.
    skill = _make_skill(source, "di-shared")
    _make_skill(source, "di-new")
    _make_managed_symlink(home / ".claude" / "skills", "di-shared", skill)
    stale = source / "di-old"
    stale.mkdir()
    (stale / "SKILL.md").write_text("# stale\n")
    _make_managed_symlink(home / ".claude" / "skills", "di-old", stale.resolve())
    (stale / "SKILL.md").unlink()
    stale.rmdir()

    code = main(["doctor", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["data"]["overall"] == "degraded"
    sync = _checks_by_name(payload["data"])["sync_status"]
    assert sync["status"] == "warn"
    assert sync["detail"]["in_sync"] == 1
    assert len(sync["detail"]["needs_install"]) == 1
    assert len(sync["detail"]["orphans"]) == 1
    assert sync["detail"]["conflicts"] == []


# --- side-effect-free guarantee ----------------------------------------------


def test_doctor_does_not_modify_filesystem(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")
    main(["doctor"])
    capsys.readouterr()
    # After doctor reported needs_install, install should still see those
    # entries — proving doctor did not silently link them.
    code = main(["install", "--target", "claude"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert len(payload["data"]["installed"]) == 1


# --- format / manifest --------------------------------------------------------


def test_doctor_pretty_format(
    home: Path, source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_skill(source, "di-shared")
    code = main(["doctor", "--format", "pretty"])
    captured = capsys.readouterr()
    assert code == 0
    assert "\n  " in captured.out  # indent=2
    payload = json.loads(captured.out)
    assert payload["ok"] is True


def test_doctor_appears_in_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--manifest"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    specs = {c["name"]: c for c in payload["data"]["commands"]}
    assert "doctor" in specs
    assert specs["doctor"]["risk"] == "read"
    assert specs["doctor"]["identity_required"] is False
