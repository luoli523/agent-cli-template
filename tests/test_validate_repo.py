from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_repo.py"
SPEC = importlib.util.spec_from_file_location("validate_repo", VALIDATOR_PATH)
assert SPEC is not None
validate_repo = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_repo
SPEC.loader.exec_module(validate_repo)


def write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_scaffold(root: Path) -> Path:
    write(root / "CLAUDE.md", "# Instructions\n")
    write(root / "README.md", "# README\n")
    write(root / "README.zh-CN.md", "# README\n")
    write(root / "CONTRIBUTING.md", "# Contributing\n")
    (root / "AGENTS.md").symlink_to("CLAUDE.md")

    for rel in validate_repo.REQUIRED_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def validate(root: Path):
    return validate_repo.validate_repository(root)


def messages(result) -> str:
    return "\n".join(result.errors + result.warnings)


def valid_skill(name: str = "datamap-lineage") -> str:
    return f"""---
name: {name}
maintainer:
  - owner@example.com
description: >
  DataMap lineage skill.
  TRIGGER when: user asks about "DataMap" or "lineage".
  DO NOT TRIGGER when: the task is unrelated to metadata.
---

# {name}
"""


def valid_agent(name: str = "service-reviewer", readonly: bool = True) -> str:
    readonly_line = "readonly: true\n" if readonly else ""
    return f"""---
name: {name}
description: >
  Reviews service contributions for ownership, safety, and test gaps.
{readonly_line}---

# {name}
"""


def test_complete_empty_scaffold_passes(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)

    result = validate(root)

    assert result.errors == []
    assert result.warnings == []


def test_agents_must_be_symlink(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    (root / "AGENTS.md").unlink()
    write(root / "AGENTS.md", "# wrong\n")

    result = validate(root)

    assert "AGENTS.md must be a symlink to CLAUDE.md" in messages(result)


def test_agents_symlink_must_point_to_claude(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    (root / "AGENTS.md").unlink()
    (root / "AGENTS.md").symlink_to("README.md")

    result = validate(root)

    assert "AGENTS.md must point to CLAUDE.md" in messages(result)


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("CLAUDE.md", "CLAUDE.md is required"),
        ("README.md", "README.md is required"),
        ("README.zh-CN.md", "README.zh-CN.md is required"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md is required"),
    ],
)
def test_required_root_files(tmp_path: Path, relative_path: str, expected: str) -> None:
    root = make_scaffold(tmp_path)
    (root / relative_path).unlink()

    result = validate(root)

    assert expected in messages(result)


def test_required_directory(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    shutil.rmtree(root / "docs/services")

    result = validate(root)

    assert "docs/services/ directory is required" in messages(result)


def test_skill_requires_skill_md(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    (root / "skills/datamap-lineage").mkdir()

    result = validate(root)

    assert "skills/datamap-lineage/SKILL.md is required" in messages(result)


def test_skill_rejects_malformed_yaml(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "skills/datamap-lineage/SKILL.md", "---\nname: [broken\n---\n")

    result = validate(root)

    assert "invalid YAML frontmatter" in messages(result)


@pytest.mark.parametrize(
    ("frontmatter", "expected"),
    [
        (
            """---
name: datamap-lineage
description: >
  DataMap lineage skill.
  TRIGGER when: user asks about metadata.
  DO NOT TRIGGER when: unrelated.
---
""",
            "missing 'maintainer' field",
        ),
        (
            """---
name: datamap-lineage
maintainer: []
description: >
  DataMap lineage skill.
  TRIGGER when: user asks about metadata.
  DO NOT TRIGGER when: unrelated.
---
""",
            "missing 'maintainer' field",
        ),
        (
            """---
name: datamap-lineage
maintainer:
  - ""
description: >
  DataMap lineage skill.
  TRIGGER when: user asks about metadata.
  DO NOT TRIGGER when: unrelated.
---
""",
            "'maintainer' entries must be non-empty strings",
        ),
        (
            """---
name: wrong-name
maintainer:
  - owner@example.com
description: >
  DataMap lineage skill.
  TRIGGER when: user asks about metadata.
  DO NOT TRIGGER when: unrelated.
---
""",
            "name must match directory 'datamap-lineage'",
        ),
        (
            """---
name: datamap-lineage
maintainer:
  - owner@example.com
description: >
  DataMap lineage skill.
  DO NOT TRIGGER when: unrelated.
---
""",
            "description missing 'TRIGGER when:'",
        ),
    ],
)
def test_skill_frontmatter_errors(tmp_path: Path, frontmatter: str, expected: str) -> None:
    root = make_scaffold(tmp_path)
    write(root / "skills/datamap-lineage/SKILL.md", frontmatter)

    result = validate(root)

    assert expected in messages(result)


def test_valid_skill_with_folded_description_passes(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "skills/datamap-lineage/SKILL.md", valid_skill())

    result = validate(root)

    assert result.errors == []


def test_skills_directory_rejects_direct_files_and_non_kebab_names(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "skills/foo.md", "# invalid\n")
    write(root / "skills/DataMapSkill/SKILL.md", valid_skill("DataMapSkill"))

    result = validate(root)

    text = messages(result)
    assert "skills/foo.md: files are not allowed directly under skills/" in text
    assert "skills/DataMapSkill: skill directory must be kebab-case" in text


def test_agent_requires_description(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "agents/service-reviewer.md", "---\nname: service-reviewer\nreadonly: true\n---\n")

    result = validate(root)

    assert "agents/service-reviewer.md: missing 'description' field" in messages(result)


def test_agent_missing_readonly_warns_but_passes(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "agents/service-reviewer.md", valid_agent(readonly=False))

    result = validate(root)

    assert result.errors == []
    assert "readonly: true is recommended" in messages(result)


def test_agent_rejects_bad_entries(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "agents/foo.txt", "invalid")
    (root / "agents/foo-dir").mkdir()
    write(root / "agents/Foo.md", valid_agent("Foo"))

    result = validate(root)

    text = messages(result)
    assert "agents/foo.txt: agent files must use .md" in text
    assert "agents/foo-dir: agent entries must be markdown files" in text
    assert "agents/Foo.md: agent filename must be kebab-case" in text


def test_service_doc_filenames_must_be_kebab_case_markdown(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "docs/services/DataMap.md", "# invalid\n")
    write(root / "docs/services/foo.txt", "invalid")
    (root / "docs/services/foo-dir").mkdir()

    result = validate(root)

    text = messages(result)
    assert "docs/services/DataMap.md: filename must be kebab-case .md" in text
    assert "docs/services/foo.txt: filename must be kebab-case .md" in text
    assert "docs/services/foo-dir: service docs must be markdown files" in text


def test_valid_service_doc_passes(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "docs/services/data-map.md", "# DataMap\n")

    result = validate(root)

    assert result.errors == []


@pytest.mark.parametrize(
    ("relative_path", "content", "expected"),
    [
        ("config/key.txt", "-----BEGIN " + "RSA PRIVATE KEY-----\n", "possible private key block"),
        ("config/aws.txt", "AKIA" + "1234567890ABCDEF\n", "possible aws access key"),
        (
            "config/github.txt",
            "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyzAB\n",
            "possible github token",
        ),
        (
            "config/slack.txt",
            "xoxb-" + "123456789012-abcdefABCDEFabcdef\n",
            "possible slack token",
        ),
        (
            "config/token.json",
            '{"token": "' + "abcdefghijklmnopqrstuvwxyz1234567890" + '"}\n',
            "possible hardcoded credential assignment",
        ),
        (
            "config/auth.txt",
            "Authorization: Bearer " + "abcdefghijklmnopqrstuvwxyz123456\n",
            "possible authorization bearer token",
        ),
        (
            "scripts/run.sh",
            "cd " + "/Users/" + "alice/project\n",
            "personal absolute path is not allowed",
        ),
    ],
)
def test_security_scan_rejects_sensitive_patterns(
    tmp_path: Path,
    relative_path: str,
    content: str,
    expected: str,
) -> None:
    root = make_scaffold(tmp_path)
    write(root / relative_path, content)

    result = validate(root)

    assert expected in messages(result)


def test_placeholder_credentials_pass(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    write(root / "config/example.json", '{"token": "<fill-me>", "client_id": "<google-oauth-client-id>"}\n')

    result = validate(root)

    assert result.errors == []


def test_multiple_errors_are_collected(tmp_path: Path) -> None:
    root = make_scaffold(tmp_path)
    (root / "README.md").unlink()
    write(root / "skills/datamap-lineage/SKILL.md", "---\nname: wrong\n---\n")

    result = validate(root)

    text = messages(result)
    assert "README.md is required" in text
    assert "missing 'maintainer' field" in text
    assert "missing 'description' field" in text
