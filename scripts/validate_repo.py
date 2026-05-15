#!/usr/bin/env python3
"""Validate the di-cli repository scaffold and contribution conventions."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only when dependency is missing.
    yaml = None  # type: ignore[assignment]

import json


ROOT_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "README.zh-CN.md",
    "CONTRIBUTING.md",
]

REQUIRED_DIRS = [
    "cli",
    "skills",
    "agents",
    "mcp/sample",
    "docs/services",
    "docs/decisions",
    "docs/contribution",
    "rules",
    "contexts",
    "config",
    "scripts",
    "tests",
]

TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

DESCRIPTION_MAX_CHARS = 1024

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SERVICE_DOC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
SUBDIR_README_FILES = frozenset({"README.md", "README.zh-CN.md"})
PERSONAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9_./-])/Users/[A-Za-z0-9._-]+/")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
TRIGGER_MARKER_RE = re.compile(r"(?<!DO NOT )\bTRIGGER when:")
DO_NOT_TRIGGER_MARKER_RE = re.compile(r"\bDO NOT TRIGGER when:")

SECRET_PATTERNS = [
    (
        "private key block",
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    ),
    (
        "aws access key",
        re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    ),
    (
        "github token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
    ),
    (
        "slack token",
        re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{20,}\b"),
    ),
    (
        "hardcoded credential assignment",
        re.compile(
            r"""(?ix)
            ['"]?\b(token|api[_-]?key|secret|password|refresh[_-]?token|private[_-]?key|cookie)\b['"]?
            \s*[:=]\s*
            ['"]([^'"<>{}\s][^'"]{19,})['"]
            """
        ),
    ),
    (
        "authorization bearer token",
        re.compile(r"(?i)\bauthorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._~+/=-]{24,}"),
    ),
]


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate di-cli repository conventions.")
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root. Defaults to the parent of scripts/.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_text_file(path: Path) -> bool:
    if path.name in {"AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md"}:
        return True
    return path.suffix in TEXT_SUFFIXES


SCAN_SKIP_DIRS = frozenset({".git", ".claude", ".cursor", ".codex", ".venv"})


def iter_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if SCAN_SKIP_DIRS.intersection(path.parts):
            continue
        if path.is_file() or path.is_symlink():
            files.append(path)
    return files


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str | None]:
    if yaml is None:
        return {}, "PyYAML is required; install project dependencies before validating"

    text = read_text(path)
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, "missing YAML frontmatter"

    raw = match.group(1)
    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return {}, f"invalid YAML frontmatter: {exc}"

    if loaded is None:
        return {}, "empty YAML frontmatter"
    if not isinstance(loaded, Mapping):
        return {}, "YAML frontmatter must be a mapping"

    fields: dict[str, Any] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            return {}, "YAML frontmatter keys must be strings"
        fields[key] = value
    return fields, None


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def require_string_field(
    fields: dict[str, Any],
    field: str,
    path: Path,
    root: Path,
    result: ValidationResult,
) -> str:
    value = fields.get(field)
    if not has_value(value):
        result.error(f"{path.relative_to(root)}: missing {field!r} field")
        return ""
    if not isinstance(value, str):
        result.error(f"{path.relative_to(root)}: {field!r} field must be a string")
        return ""
    return value


def validate_maintainer_field(
    fields: dict[str, Any],
    path: Path,
    root: Path,
    result: ValidationResult,
) -> None:
    value = fields.get("maintainer")
    if not has_value(value):
        result.error(f"{path.relative_to(root)}: missing 'maintainer' field")
        return

    if isinstance(value, str):
        if not value.strip():
            result.error(f"{path.relative_to(root)}: 'maintainer' field must not be empty")
        return

    if isinstance(value, list):
        if not value:
            result.error(f"{path.relative_to(root)}: 'maintainer' field must not be empty")
            return
        for item in value:
            if not isinstance(item, str) or not item.strip():
                result.error(
                    f"{path.relative_to(root)}: 'maintainer' entries must be non-empty strings"
                )
                return
        return

    result.error(f"{path.relative_to(root)}: 'maintainer' field must be a string or list")


def is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def load_prefixes(root: Path) -> tuple[set[str], str]:
    """Return (known_prefix_strings, enforce_policy) from config/prefixes.json.

    Returns (empty set, "warn") if the file is absent or malformed, so callers
    silently skip the prefix check rather than crashing.
    """
    prefixes_path = root / "config" / "prefixes.json"
    if not prefixes_path.is_file():
        return set(), "warn"
    try:
        data = json.loads(prefixes_path.read_text(encoding="utf-8"))
        known = {entry["prefix"] for entry in data.get("prefixes", []) if "prefix" in entry}
        enforce = data.get("policy", {}).get("enforce", "warn")
        return known, enforce
    except (json.JSONDecodeError, TypeError, KeyError):
        return set(), "warn"


def validate_root(root: Path, result: ValidationResult) -> None:
    for rel in ROOT_FILES:
        path = root / rel
        if not path.exists() and not path.is_symlink():
            result.error(f"{rel} is required")

    agents_path = root / "AGENTS.md"
    if not agents_path.is_symlink():
        result.error("AGENTS.md must be a symlink to CLAUDE.md")
    else:
        target = os.readlink(agents_path)
        if target != "CLAUDE.md":
            result.error(f"AGENTS.md must point to CLAUDE.md, got {target!r}")

    for rel in REQUIRED_DIRS:
        path = root / rel
        if not path.is_dir():
            result.error(f"{rel}/ directory is required")


def validate_skills(root: Path, result: ValidationResult) -> None:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return

    known_prefixes, enforce = load_prefixes(root)

    for child in sorted(skills_dir.iterdir()):
        if child.name == ".gitkeep":
            continue
        if child.is_file() and child.name in SUBDIR_README_FILES:
            continue
        if child.is_file():
            result.error(f"skills/{child.name}: files are not allowed directly under skills/")
            continue
        if not child.is_dir():
            continue
        if not KEBAB_CASE_RE.fullmatch(child.name):
            result.error(f"skills/{child.name}: skill directory must be kebab-case")

        skill_file = child / "SKILL.md"
        if not skill_file.is_file():
            result.error(f"skills/{child.name}/SKILL.md is required")
            continue

        fields, parse_error = parse_frontmatter(skill_file)
        if parse_error:
            result.error(f"{skill_file.relative_to(root)}: {parse_error}")
            continue

        name = require_string_field(fields, "name", skill_file, root, result)
        description = require_string_field(fields, "description", skill_file, root, result)
        validate_maintainer_field(fields, skill_file, root, result)

        if name and name != child.name:
            result.error(
                f"{skill_file.relative_to(root)}: name must match directory {child.name!r}"
            )

        if name and known_prefixes:
            if not any(name.startswith(p) for p in known_prefixes):
                msg = (
                    f"{skill_file.relative_to(root)}: skill name {name!r} does not start with"
                    f" a known prefix ({', '.join(sorted(known_prefixes))})"
                )
                if enforce == "error":
                    result.error(msg)
                else:
                    result.warn(msg)

        if description:
            if len(description) > DESCRIPTION_MAX_CHARS:
                result.error(
                    f"{skill_file.relative_to(root)}: description exceeds"
                    f" {DESCRIPTION_MAX_CHARS} characters ({len(description)} chars)"
                )
            if not TRIGGER_MARKER_RE.search(description):
                result.error(f"{skill_file.relative_to(root)}: description missing 'TRIGGER when:'")
            if not DO_NOT_TRIGGER_MARKER_RE.search(description):
                result.error(
                    f"{skill_file.relative_to(root)}: description missing 'DO NOT TRIGGER when:'"
                )

        for nested in child.rglob("*"):
            if nested.is_dir() and nested.name == "SKILL.md":
                result.error(f"{nested.relative_to(root)}: invalid nested skill-like directory")


def validate_agents(root: Path, result: ValidationResult) -> None:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return

    for child in sorted(agents_dir.iterdir()):
        if child.name == ".gitkeep":
            continue
        if child.is_file() and child.name in SUBDIR_README_FILES:
            continue
        if child.is_dir():
            result.error(f"agents/{child.name}: agent entries must be markdown files")
            continue
        if child.suffix != ".md":
            result.error(f"agents/{child.name}: agent files must use .md")
            continue
        if not KEBAB_CASE_RE.fullmatch(child.stem):
            result.error(f"agents/{child.name}: agent filename must be kebab-case")

        fields, parse_error = parse_frontmatter(child)
        if parse_error:
            result.error(f"{child.relative_to(root)}: {parse_error}")
            continue

        name = require_string_field(fields, "name", child, root, result)
        require_string_field(fields, "description", child, root, result)

        if name and name != child.stem:
            result.error(f"{child.relative_to(root)}: name must match filename {child.stem!r}")

        # strict type checks for optional agent frontmatter fields
        tools = fields.get("tools")
        if tools is not None:
            if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
                result.error(
                    f"{child.relative_to(root)}: 'tools' must be a list of strings"
                )

        readonly = fields.get("readonly")
        if readonly is not None:
            if not isinstance(readonly, bool):
                result.error(
                    f"{child.relative_to(root)}: 'readonly' must be a boolean (true or false)"
                )
        if not is_true(readonly):
            result.warn(f"{child.relative_to(root)}: readonly: true is recommended")

        model = fields.get("model")
        if model is not None and not isinstance(model, str):
            result.error(f"{child.relative_to(root)}: 'model' must be a string")


def validate_service_docs(root: Path, result: ValidationResult) -> None:
    services_dir = root / "docs/services"
    if not services_dir.is_dir():
        return

    for child in sorted(services_dir.iterdir()):
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            result.error(f"docs/services/{child.name}: service docs must be markdown files")
            continue
        if not SERVICE_DOC_RE.fullmatch(child.name):
            result.error(f"docs/services/{child.name}: filename must be kebab-case .md")


def validate_security(root: Path, result: ValidationResult) -> None:
    for path in iter_repo_files(root):
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if path.is_symlink() or not is_text_file(path):
            continue

        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            if PERSONAL_PATH_RE.search(line):
                result.error(f"{rel}:{line_no}: personal absolute path is not allowed")

            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    result.error(f"{rel}:{line_no}: possible {label}")
                    break


def print_results(result: ValidationResult) -> int:
    for warning in result.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if result.errors:
        print(f"FAILED: {len(result.errors)} error(s), {len(result.warnings)} warning(s)", file=sys.stderr)
        return 1

    print(f"OK: validation passed with {len(result.warnings)} warning(s)")
    return 0


def validate_repository(root: Path) -> ValidationResult:
    root = root.resolve()

    result = ValidationResult(errors=[], warnings=[])
    validate_root(root, result)
    validate_skills(root, result)
    validate_agents(root, result)
    validate_service_docs(root, result)
    validate_security(root, result)
    return result


def main() -> int:
    args = parse_args()
    result = validate_repository(args.root)
    return print_results(result)


if __name__ == "__main__":
    raise SystemExit(main())
