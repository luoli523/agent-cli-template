"""Repo-shape checks.

These aren't about skill correctness — they enforce that the repo
itself stays in a state our docs and tooling assume. CLAUDE.md is the
canonical assistant-instructions file; ``AGENTS.md`` must remain a
symlink to it (spec § Project structure). Drift here causes confusing
contributor onboarding.

Run by ``di validate --scope repo`` and ``di validate --scope all``.
"""

from __future__ import annotations

import os
from pathlib import Path

from mycli.runtime import FAIL, OK, WARN, Check

# Subdirectories under docs/ that the project ships and the docs link
# tree assumes. Missing one is a warning rather than a hard failure
# because a fresh contributor working in a worktree may not yet have
# all of them.
EXPECTED_DOCS_SUBDIRS: tuple[str, ...] = ("specs", "decisions", "explainers", "reference")


def validate_repo(repo_root: Path) -> list[Check]:
    """Run the full repo-shape audit. Returns a list of checks.

    All checks are name-prefixed ``repo/`` so they share namespace with
    ``skills/<name>`` checks without colliding.
    """
    return [
        _check_agents_symlink(repo_root),
        _check_pyproject(repo_root),
        _check_skills_dir_present(repo_root),
        _check_docs_subdirs(repo_root),
    ]


def _check_agents_symlink(repo_root: Path) -> Check:
    """``AGENTS.md`` must be a symlink to ``CLAUDE.md``.

    Codex reads ``AGENTS.md``; Claude Code reads ``CLAUDE.md``. We
    maintain one file (CLAUDE.md) and symlink the other so the two
    assistants see the same instructions.
    """
    agents = repo_root / "AGENTS.md"
    claude = repo_root / "CLAUDE.md"
    if not agents.exists() and not agents.is_symlink():
        return Check(
            "repo/agents_symlink",
            FAIL,
            "AGENTS.md is missing",
            hint="run `ln -s CLAUDE.md AGENTS.md` from the repo root",
        )
    if not agents.is_symlink():
        return Check(
            "repo/agents_symlink",
            FAIL,
            "AGENTS.md exists but is not a symlink",
            detail={"path": str(agents)},
            hint=(
                "delete AGENTS.md, then `ln -s CLAUDE.md AGENTS.md` so Codex and "
                "Claude Code share the same instructions file"
            ),
        )
    target = Path(os.readlink(agents))
    if target.name != "CLAUDE.md":
        return Check(
            "repo/agents_symlink",
            FAIL,
            f"AGENTS.md points to {target.name!r}; expected CLAUDE.md",
            detail={"target": str(target)},
            hint="re-create the symlink: `ln -snf CLAUDE.md AGENTS.md`",
        )
    if not claude.is_file():
        return Check(
            "repo/agents_symlink",
            FAIL,
            "CLAUDE.md is missing (AGENTS.md symlink would be broken)",
            hint="restore CLAUDE.md from git history",
        )
    return Check(
        "repo/agents_symlink",
        OK,
        "AGENTS.md is a symlink to CLAUDE.md",
    )


def _check_pyproject(repo_root: Path) -> Check:
    """``pyproject.toml`` must exist — it's the package + tool config."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return Check(
            "repo/pyproject",
            FAIL,
            "pyproject.toml not found at repo root",
            detail={"expected_path": str(pyproject)},
            hint="this is not a mycli-cli repo root, or pyproject.toml was deleted",
        )
    return Check("repo/pyproject", OK, "pyproject.toml present")


def _check_skills_dir_present(repo_root: Path) -> Check:
    """``skills/`` must exist (may be empty during early bootstrap)."""
    skills = repo_root / "skills"
    if not skills.is_dir():
        return Check(
            "repo/skills_dir",
            WARN,
            "skills/ directory does not exist",
            hint=(
                "create an empty skills/ directory at the repo root; "
                "install/update/doctor expect it to be present"
            ),
        )
    return Check("repo/skills_dir", OK, "skills/ directory present")


def _check_docs_subdirs(repo_root: Path) -> Check:
    """``docs/{specs,decisions,explainers}`` should all be present.

    Reported as a single check (vs three) because the missing-set
    matters as a group: an audit needs to see "what's missing", not
    cycle through three separate warns.
    """
    missing = []
    docs = repo_root / "docs"
    for sub in EXPECTED_DOCS_SUBDIRS:
        if not (docs / sub).is_dir():
            missing.append(sub)
    if not missing:
        return Check(
            "repo/docs_layout",
            OK,
            "docs/{" + ",".join(EXPECTED_DOCS_SUBDIRS) + "} all present",
        )
    return Check(
        "repo/docs_layout",
        WARN,
        f"{len(missing)} expected docs subdir(s) missing",
        detail={"missing": missing},
        hint="create the missing directories so docs cross-links stay valid",
    )
