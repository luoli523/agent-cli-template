"""Repo-shape validator tests."""

from __future__ import annotations

from pathlib import Path

from di.validators.repo import validate_repo


def _make_repo(tmp_path: Path, *, agents_symlink: bool = True, pyproject: bool = True,
                skills_dir: bool = True, docs_subdirs: tuple[str, ...] = ("specs", "decisions", "explainers")
                ) -> Path:
    """Build a fake repo layout under tmp_path with knobs for each check."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "CLAUDE.md").write_text("# claude\n")
    if agents_symlink:
        (repo / "AGENTS.md").symlink_to("CLAUDE.md")
    if pyproject:
        (repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    if skills_dir:
        (repo / "skills").mkdir()
    docs = repo / "docs"
    docs.mkdir()
    for sub in docs_subdirs:
        (docs / sub).mkdir()
    return repo


def _check_by_name(checks, name):  # type: ignore[no-untyped-def]
    return next(c for c in checks if c.name == name)


def test_clean_repo_yields_all_ok(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    checks = validate_repo(repo)
    assert all(c.status == "ok" for c in checks)


def test_missing_agents_md_is_fail(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, agents_symlink=False)
    check = _check_by_name(validate_repo(repo), "repo/agents_symlink")
    assert check.status == "fail"
    assert "missing" in check.message


def test_agents_as_regular_file_is_fail(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, agents_symlink=False)
    (repo / "AGENTS.md").write_text("not a symlink")
    check = _check_by_name(validate_repo(repo), "repo/agents_symlink")
    assert check.status == "fail"
    assert "not a symlink" in check.message


def test_agents_pointing_elsewhere_is_fail(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, agents_symlink=False)
    (repo / "OTHER.md").write_text("# other\n")
    (repo / "AGENTS.md").symlink_to("OTHER.md")
    check = _check_by_name(validate_repo(repo), "repo/agents_symlink")
    assert check.status == "fail"
    assert "CLAUDE.md" in check.message


def test_missing_pyproject_is_fail(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, pyproject=False)
    check = _check_by_name(validate_repo(repo), "repo/pyproject")
    assert check.status == "fail"


def test_missing_skills_dir_is_warn(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, skills_dir=False)
    check = _check_by_name(validate_repo(repo), "repo/skills_dir")
    assert check.status == "warn"


def test_missing_docs_subdirs_is_warn(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, docs_subdirs=("specs",))  # missing decisions + explainers
    check = _check_by_name(validate_repo(repo), "repo/docs_layout")
    assert check.status == "warn"
    assert set(check.detail["missing"]) == {"decisions", "explainers"}
