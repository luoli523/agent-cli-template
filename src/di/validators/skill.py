"""Per-skill-directory validator.

A skill is a directory under ``skills/`` whose layout must match the
contract install/update assumes. Checks here come in two layers:

1. **Filesystem layout** — directory shape, presence of ``SKILL.md``,
   absence of nested skills, name matching the frontmatter ``name``.
2. **SKILL.md content** — frontmatter (via :mod:`frontmatter`) plus a
   handful of body rules: must have an H1 heading and non-empty body.

The validator never modifies files. It returns one :class:`Check` per
skill (the worst single issue determines the check's status) so the
``di validate`` envelope stays a flat list keyed by ``skills/<name>``.
"""

from __future__ import annotations

from pathlib import Path

from di.runtime import FAIL, OK, WARN, Check
from di.validators.frontmatter import (
    FrontmatterError,
    FrontmatterIssue,
    parse_skill_frontmatter,
    read_skill_md,
    validate_frontmatter,
)

SKILL_PREFIX = "di-"
SKILL_MANIFEST = "SKILL.md"
ALLOWED_NESTED_DIRS: frozenset[str] = frozenset({"references", "assets"})

MAX_LINE_LEN = 200


def validate_skill(skill_dir: Path) -> Check:
    """Validate a single skill directory. Returns one :class:`Check`.

    The check's name is ``skills/<dir>`` so the validate envelope is
    self-describing without needing nested structures.
    """
    name = skill_dir.name
    check_name = f"skills/{name}"

    # 1. Prefix
    if not name.startswith(SKILL_PREFIX):
        return Check(
            check_name,
            FAIL,
            f"skill directory name must start with `di-` prefix; got {name!r}",
            hint="rename the directory to start with `di-`",
        )

    # 2. SKILL.md presence
    manifest = skill_dir / SKILL_MANIFEST
    if not manifest.is_file():
        return Check(
            check_name,
            FAIL,
            f"missing required file: {SKILL_MANIFEST}",
            detail={"expected_path": str(manifest)},
            hint=f"create {SKILL_MANIFEST} in the skill directory",
        )

    # 3. Nested skill ban (directory shape)
    nested_issue = _detect_nested_skill(skill_dir)
    if nested_issue is not None:
        return nested_issue

    # 4. SKILL.md parse + frontmatter
    try:
        text = read_skill_md(manifest)
        parsed = parse_skill_frontmatter(text)
    except FrontmatterError as exc:
        return Check(
            check_name,
            FAIL,
            f"SKILL.md frontmatter: {exc}",
            hint="add a valid YAML frontmatter block between two `---` lines at the top",
        )

    fm_issues = validate_frontmatter(parsed.data, directory_name=name)
    body_issues = _validate_body(parsed.body)

    issues = fm_issues + body_issues
    return _reduce(check_name, issues)


def validate_skills_root(skills_root: Path) -> list[Check]:
    """Validate every skill directory under ``skills_root``.

    Also reports stray files at the root (skills/ must contain only
    directories) and duplicate skill names. Returns one check per
    skill plus one ``skills_root`` check for root-level shape.
    """
    if not skills_root.is_dir():
        return [
            Check(
                "skills_root",
                FAIL,
                f"skills root not found: {skills_root}",
                hint="ensure the skills/ directory exists or pass --skills-dir",
            )
        ]

    stray_files = [p.name for p in sorted(skills_root.iterdir()) if p.is_file()]
    root_check: Check
    if stray_files:
        root_check = Check(
            "skills_root",
            WARN,
            f"{len(stray_files)} non-directory entr(y/ies) under skills/",
            detail={"stray": stray_files},
            hint="skills/ should contain only skill directories; move loose files elsewhere",
        )
    else:
        root_check = Check(
            "skills_root",
            OK,
            "skills/ contains only directories",
            detail={"path": str(skills_root)},
        )

    skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir())
    skill_checks = [validate_skill(p) for p in skill_dirs]

    # Duplicate-name detection: an extra check appears only when there's
    # actually a duplicate. Compares directory names; frontmatter-name
    # mismatches are handled inside validate_skill.
    seen: dict[str, list[str]] = {}
    for p in skill_dirs:
        seen.setdefault(p.name, []).append(str(p))
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    if duplicates:
        skill_checks.append(
            Check(
                "skills_root/duplicates",
                FAIL,
                f"{len(duplicates)} duplicate skill name(s)",
                detail={"duplicates": duplicates},
                hint="rename one of each duplicate pair; install keys symlinks by directory name",
            )
        )

    return [root_check, *skill_checks]


# --- helpers -----------------------------------------------------------------


def _detect_nested_skill(skill_dir: Path) -> Check | None:
    """A skill directory must not contain another skill (no recursion).

    A nested ``SKILL.md`` indicates the author put a sub-skill inside —
    install would symlink the outer directory and the inner SKILL.md
    would only be reachable through path traversal, which AI tools do
    not do. Reject the layout at validation time instead of silently
    losing the inner skill.
    """
    for entry in skill_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in ALLOWED_NESTED_DIRS:
            continue
        if (entry / SKILL_MANIFEST).is_file():
            return Check(
                f"skills/{skill_dir.name}",
                FAIL,
                f"nested skill detected at {entry.relative_to(skill_dir)}/",
                detail={"nested_at": str(entry)},
                hint="flatten skills — one SKILL.md per top-level skills/<name>/ directory",
            )
    return None


def _validate_body(body: str) -> list[FrontmatterIssue]:
    """Body-level checks: must start with H1, must not be empty, line length."""
    issues: list[FrontmatterIssue] = []
    stripped = body.strip()
    if not stripped:
        issues.append(
            FrontmatterIssue("fail", "SKILL.md body is empty; add at least an H1 heading")
        )
        return issues
    first_non_blank = next((line for line in stripped.splitlines() if line.strip()), "")
    if not first_non_blank.startswith("# "):
        issues.append(
            FrontmatterIssue(
                "fail",
                "SKILL.md body must start with an `# H1` heading after the frontmatter",
            )
        )
    overlong = [
        (i + 1, len(line))
        for i, line in enumerate(body.splitlines())
        if len(line) > MAX_LINE_LEN
    ]
    if overlong:
        # Report up to the first 3 offenders so the warning stays readable.
        sample = overlong[:3]
        issues.append(
            FrontmatterIssue(
                "warn",
                f"{len(overlong)} line(s) exceed {MAX_LINE_LEN} chars: "
                + ", ".join(f"line {ln} ({n} chars)" for ln, n in sample),
            )
        )
    return issues


def _reduce(check_name: str, issues: list[FrontmatterIssue]) -> Check:
    """Collapse a list of FrontmatterIssues into a single :class:`Check`.

    Worst-status-wins. Multiple issues are surfaced via ``detail``; a
    single one-liner becomes the message.
    """
    if not issues:
        return Check(check_name, OK, "SKILL.md valid")
    fails = [i for i in issues if i.status == FAIL]
    warns = [i for i in issues if i.status == WARN]
    status = FAIL if fails else WARN
    surfaced = fails if fails else warns
    if len(surfaced) == 1:
        msg = surfaced[0].message
    else:
        msg = f"{len(surfaced)} issue(s): {surfaced[0].message}"
    detail = {
        "issues": [
            {"status": i.status, "message": i.message, **({"field": i.field} if i.field else {})}
            for i in issues
        ]
    }
    return Check(check_name, status, msg, detail=detail)
