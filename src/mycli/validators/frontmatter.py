"""SKILL.md YAML frontmatter parsing and validation.

A SKILL.md begins with a YAML block delimited by ``---`` lines, then a
free-form Markdown body. This module extracts the YAML block, parses
it, and runs schema checks. Body checks live in :mod:`skill`.

Validation rules (see docs/explainers/contracts-for-ai-agents.md is
about runtime protocol, not authoring conventions; T8 is the authoring
side):

Required:

* ``name`` — kebab-case, skill prefix (from pyproject [tool.agent-cli].skill_prefix),
  equal to the skill directory name.
* ``description`` — non-empty, ≤ ``MAX_DESCRIPTION_LEN`` chars, and must
  contain both ``TRIGGER when:`` and ``DO NOT TRIGGER when:`` markers so
  AI agents know when to activate vs skip the skill.
* ``maintainer`` — non-empty list of strings; each entry must contain ``@``.

Optional:

* ``version`` — semver ``X.Y.Z``.
* ``metadata.requires.bins`` — list of strings (binaries the skill
  depends on, e.g. ``["di"]``).
* ``metadata.cliHelp`` — string.

Unknown top-level fields are reported as warnings, not errors — typos
("maintainers" vs "maintainer") should be visible without blocking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

MAX_DESCRIPTION_LEN = 1024

REQUIRED_TRIGGER_MARKERS: tuple[str, ...] = (
    "TRIGGER when:",
    "DO NOT TRIGGER when:",
)

KNOWN_TOP_LEVEL_FIELDS: frozenset[str] = frozenset(
    {"name", "description", "maintainer", "version", "metadata"}
)

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z\.\-]+)?(\+[0-9A-Za-z\.\-]+)?$")

# A line of ``---`` at the very top, then YAML, then a closing ``---``.
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|$)", re.DOTALL)


@dataclass(frozen=True)
class FrontmatterError(Exception):
    """Raised when SKILL.md does not have a parseable YAML frontmatter."""

    reason: str

    def __str__(self) -> str:
        return self.reason


@dataclass(frozen=True)
class FrontmatterIssue:
    """One issue produced by :func:`validate_frontmatter`.

    ``status`` is ``"fail"`` or ``"warn"`` — frontmatter is structured
    enough that the validator should not need an ``ok`` issue type;
    callers infer ok = empty list.
    """

    status: str  # "fail" | "warn"
    message: str
    field: str | None = None


@dataclass(frozen=True)
class FrontmatterParseResult:
    """Outcome of :func:`parse_skill_frontmatter`.

    ``body`` excludes the leading frontmatter block but includes the
    blank line that often follows; skill-level checks (line length,
    H1 heading) consume it as-is.
    """

    data: dict[str, Any]
    body: str
    raw_yaml: str = field(default="")


def parse_skill_frontmatter(text: str) -> FrontmatterParseResult:
    """Extract and parse the YAML frontmatter from a SKILL.md text.

    Raises :class:`FrontmatterError` when the file does not start with
    ``---``, when the block is unterminated, or when the YAML is
    malformed. The error is structured so the calling validator can
    convert it into a check failure.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise FrontmatterError("SKILL.md must start with a `---` YAML frontmatter block")
    raw = match.group(1)
    body = text[match.end():]
    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter YAML is malformed: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise FrontmatterError("frontmatter must be a YAML mapping")
    return FrontmatterParseResult(data=loaded, body=body, raw_yaml=raw)


def validate_frontmatter(
    data: dict[str, Any],
    *,
    directory_name: str | None = None,
) -> list[FrontmatterIssue]:
    """Run schema checks on a parsed frontmatter mapping.

    When ``directory_name`` is given, ``name`` must equal it — the
    install layer keys symlink names off the directory, so the two have
    to agree or AI agents pick up a skill under one name while the file
    declares another.
    """
    issues: list[FrontmatterIssue] = []
    _check_name(data, directory_name, issues)
    _check_description(data, issues)
    _check_maintainer(data, issues)
    _check_version(data, issues)
    _check_metadata(data, issues)
    _check_unknown_fields(data, issues)
    return issues


def _check_name(
    data: dict[str, Any], directory_name: str | None, issues: list[FrontmatterIssue]
) -> None:
    name = data.get("name")
    if not name:
        issues.append(FrontmatterIssue("fail", "missing required field: name", "name"))
        return
    if not isinstance(name, str):
        issues.append(FrontmatterIssue("fail", "name must be a string", "name"))
        return
    from mycli.validators.skill import SKILL_PREFIX

    if not name.startswith(SKILL_PREFIX):
        issues.append(
            FrontmatterIssue("fail", f"name must start with `{SKILL_PREFIX}` prefix; got {name!r}", "name")
        )
    if not KEBAB_RE.match(name):
        issues.append(
            FrontmatterIssue(
                "fail",
                f"name must be kebab-case ([a-z0-9-]+); got {name!r}",
                "name",
            )
        )
    if directory_name is not None and name != directory_name:
        issues.append(
            FrontmatterIssue(
                "fail",
                f"name {name!r} does not match directory name {directory_name!r}",
                "name",
            )
        )


def _check_description(data: dict[str, Any], issues: list[FrontmatterIssue]) -> None:
    desc = data.get("description")
    if not desc:
        issues.append(
            FrontmatterIssue("fail", "missing required field: description", "description")
        )
        return
    if not isinstance(desc, str):
        issues.append(
            FrontmatterIssue("fail", "description must be a string", "description")
        )
        return
    if len(desc) > MAX_DESCRIPTION_LEN:
        issues.append(
            FrontmatterIssue(
                "fail",
                f"description is {len(desc)} chars; must be ≤ {MAX_DESCRIPTION_LEN}",
                "description",
            )
        )
    missing_markers = [m for m in REQUIRED_TRIGGER_MARKERS if m not in desc]
    if missing_markers:
        issues.append(
            FrontmatterIssue(
                "fail",
                "description must include trigger markers: "
                + ", ".join(repr(m) for m in missing_markers),
                "description",
            )
        )


def _check_maintainer(data: dict[str, Any], issues: list[FrontmatterIssue]) -> None:
    maintainer = data.get("maintainer")
    if not maintainer:
        issues.append(
            FrontmatterIssue("fail", "missing required field: maintainer", "maintainer")
        )
        return
    if not isinstance(maintainer, list):
        issues.append(
            FrontmatterIssue(
                "fail", "maintainer must be a list of email addresses", "maintainer"
            )
        )
        return
    for idx, entry in enumerate(maintainer):
        if not isinstance(entry, str) or "@" not in entry:
            issues.append(
                FrontmatterIssue(
                    "fail",
                    f"maintainer[{idx}] must look like an email (contain `@`); got {entry!r}",
                    "maintainer",
                )
            )


def _check_version(data: dict[str, Any], issues: list[FrontmatterIssue]) -> None:
    if "version" not in data:
        return
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        issues.append(
            FrontmatterIssue(
                "warn",
                f"version should be semver X.Y.Z; got {version!r}",
                "version",
            )
        )


def _check_metadata(data: dict[str, Any], issues: list[FrontmatterIssue]) -> None:
    if "metadata" not in data:
        return
    md = data.get("metadata")
    if not isinstance(md, dict):
        issues.append(
            FrontmatterIssue("fail", "metadata must be a mapping", "metadata")
        )
        return
    requires = md.get("requires")
    if requires is not None:
        if not isinstance(requires, dict):
            issues.append(
                FrontmatterIssue(
                    "fail", "metadata.requires must be a mapping", "metadata.requires"
                )
            )
        else:
            bins = requires.get("bins")
            if bins is not None and (
                not isinstance(bins, list)
                or not all(isinstance(b, str) for b in bins)
            ):
                issues.append(
                    FrontmatterIssue(
                        "fail",
                        "metadata.requires.bins must be a list of strings",
                        "metadata.requires.bins",
                    )
                )
    cli_help = md.get("cliHelp")
    if cli_help is not None and not isinstance(cli_help, str):
        issues.append(
            FrontmatterIssue("fail", "metadata.cliHelp must be a string", "metadata.cliHelp")
        )


def _check_unknown_fields(data: dict[str, Any], issues: list[FrontmatterIssue]) -> None:
    unknown = sorted(set(data.keys()) - KNOWN_TOP_LEVEL_FIELDS)
    if unknown:
        issues.append(
            FrontmatterIssue(
                "warn",
                "unknown top-level field(s): " + ", ".join(unknown),
            )
        )


def read_skill_md(path: Path) -> str:
    """Convenience reader; raises :class:`FrontmatterError` if unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FrontmatterError(f"cannot read {path}: {exc}") from exc
