#!/usr/bin/env python3
"""agent-cli-template initializer.

Run once after forking: python init.py
Renames mycli → your CLI name across the entire repository.

Idempotency guard: refuses to run if pyproject.toml already has a name
other than "mycli" (the template default), so it is safe to leave in
the repo after initialization.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Template defaults — the strings that must be replaced                       #
# --------------------------------------------------------------------------- #
TEMPLATE_PKG = "mycli"          # Python package name  (snake_case)
TEMPLATE_CMD = "mycli"          # CLI command name     (kebab-case)
TEMPLATE_PROJECT = "mycli"      # pyproject [project].name
TEMPLATE_SKILL_PREFIX = "mycli-"

# Files / dirs to skip entirely (binary, caches, venv, git internals)
SKIP_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache",
             ".ruff_cache", "dist", "infographic"}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".whl", ".tar.gz", ".png", ".jpg",
                   ".jpeg", ".svg", ".ico", ".pdf"}


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _prompt(question: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(1)
    return answer or default


def _to_snake(name: str) -> str:
    return re.sub(r"[-\s]+", "_", name).lower()


def _to_kebab(name: str) -> str:
    return re.sub(r"[_\s]+", "-", name).lower()


def _check_already_initialized() -> None:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return
    text = _read(pyproject)
    if f'name = "{TEMPLATE_PROJECT}"' not in text:
        print("This repo has already been initialized (pyproject.toml name is not 'mycli').")
        print("Run init.py only once, immediately after forking the template.")
        sys.exit(0)


def _collect_replacements(
    new_cmd: str, new_pkg: str, author: str, email: str, repo_url: str
) -> list[tuple[str, str]]:
    """Return ordered (old, new) pairs. Order matters — longer strings first."""
    new_skill_prefix = f"{new_cmd}-"
    pairs = [
        # skill prefix (must come before bare cmd substitutions)
        (f"mycli-skill-template", f"{new_cmd}-skill-template"),
        (f"mycli-shared", f"{new_cmd}-shared"),
        (TEMPLATE_SKILL_PREFIX, new_skill_prefix),
        # Python package (snake_case)
        (TEMPLATE_PKG, new_pkg),
        # CLI command (already same as pkg here, but explicit for clarity)
        (TEMPLATE_CMD, new_cmd),
        # author / email / repo placeholders
        ("agent-cli-template contributors", author if author else "agent-cli-template contributors"),
        ("maintainer@example.com", email if email else "maintainer@example.com"),
    ]
    if repo_url:
        pairs.append(("https://github.com/your-org/your-repo", repo_url))
    return pairs


def _replace_in_file(path: Path, pairs: list[tuple[str, str]]) -> bool:
    try:
        original = _read(path)
    except (UnicodeDecodeError, PermissionError):
        return False
    text = original
    for old, new in pairs:
        text = text.replace(old, new)
    if text != original:
        _write(path, text)
        return True
    return False


def _walk_and_replace(pairs: list[tuple[str, str]]) -> int:
    changed = 0
    for item in sorted(REPO_ROOT.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(REPO_ROOT)
        parts = rel.parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if item.suffix in SKIP_EXTENSIONS:
            continue
        if item.name == "init.py" and item.parent == REPO_ROOT:
            continue  # don't self-modify
        if _replace_in_file(item, pairs):
            changed += 1
    return changed


def _rename_directories(new_cmd: str, new_pkg: str) -> None:
    """Rename src/mycli → src/<pkg> and skills/mycli-* → skills/<cmd>-*."""
    src_old = REPO_ROOT / "src" / TEMPLATE_PKG
    src_new = REPO_ROOT / "src" / new_pkg
    if src_old.is_dir() and not src_new.is_dir():
        shutil.move(str(src_old), str(src_new))
        print(f"  Renamed src/{TEMPLATE_PKG}/ → src/{new_pkg}/")

    skills = REPO_ROOT / "skills"
    if skills.is_dir():
        for d in sorted(skills.iterdir()):
            if d.is_dir() and d.name.startswith(TEMPLATE_SKILL_PREFIX):
                suffix = d.name[len(TEMPLATE_SKILL_PREFIX):]
                new_dir = skills / f"{new_cmd}-{suffix}"
                if not new_dir.exists():
                    shutil.move(str(d), str(new_dir))
                    print(f"  Renamed skills/{d.name}/ → skills/{new_dir.name}/")


def _fix_agents_symlink() -> None:
    """Ensure AGENTS.md is a symlink to CLAUDE.md (may be a plain file after `cp -r`)."""
    agents = REPO_ROOT / "AGENTS.md"
    claude = REPO_ROOT / "CLAUDE.md"
    if claude.is_file() and agents.exists() and not agents.is_symlink():
        agents.unlink()
        agents.symlink_to("CLAUDE.md")
        print("  Re-created AGENTS.md as symlink to CLAUDE.md.")


def _reset_git(reset: bool) -> None:
    if not reset:
        return
    git_dir = REPO_ROOT / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
        print("  Removed existing .git history.")
    subprocess.run(["git", "init"], cwd=REPO_ROOT, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initialize from agent-cli-template"],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    print("  Fresh git history created with initial commit.")


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def main() -> None:
    _check_already_initialized()

    print("\n=== agent-cli-template initializer ===\n")
    print("This wizard renames 'mycli' to your CLI name across the repo.")
    print("Press Ctrl-C at any time to abort.\n")

    cli_name = ""
    while not cli_name:
        raw = _prompt("CLI name (kebab-case, e.g. my-service-cli)")
        cli_name = _to_kebab(raw)
        if not re.match(r"^[a-z][a-z0-9-]+$", cli_name):
            print(f"  '{cli_name}' is not valid kebab-case. Use only [a-z0-9-].")
            cli_name = ""

    pkg_name = _to_snake(cli_name)
    print(f"  → Python package name: {pkg_name}")
    print(f"  → Skill prefix: {cli_name}-\n")

    author = _prompt("Author name", "agent-cli-template contributors")
    email = _prompt("Author email", "maintainer@example.com")
    repo_url = _prompt("Repository URL (optional, press Enter to skip)", "")
    reset_git = _prompt("Reset git history? (y/N)", "N").lower() == "y"

    print(f"\nWill rename 'mycli' → '{cli_name}' / '{pkg_name}' across the repo.")
    if reset_git:
        print("Will also reset git history with a fresh initial commit.")
    confirm = _prompt("Continue? (y/N)", "N")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    print("\nRunning…")

    pairs = _collect_replacements(cli_name, pkg_name, author, email, repo_url)

    # 1. Rename directories first (before text replacement so new paths are touched)
    _rename_directories(cli_name, pkg_name)

    # 2. Text replacement across all files
    changed = _walk_and_replace(pairs)
    print(f"  Updated {changed} file(s).")

    # 3. Ensure AGENTS.md is a symlink (may be a plain file after `cp -r` or gh template clone)
    _fix_agents_symlink()

    # 4. Optionally reset git
    _reset_git(reset_git)

    print(f"""
Done! Next steps:

  uv sync --extra dev          # install dependencies
  uv run {cli_name} hello --name World   # smoke test
  uv run pytest -q             # full test suite
  uv run {cli_name} validate   # skill + repo shape check

Then delete src/{pkg_name}/core/hello.py (and its test) and add
your first real service command.
""")


if __name__ == "__main__":
    main()
