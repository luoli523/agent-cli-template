"""Skill and repo-shape validators consumed by ``di validate``.

Each validator returns one or more :class:`di.core.doctor.Check`
records. Validators are kept side-effect-free and ordered so their
output is deterministic (CI diffs need this).

Module map:

* :mod:`frontmatter` — parse SKILL.md YAML, validate required fields.
* :mod:`skill` — per-skill-directory checks (filesystem + frontmatter).
* :mod:`repo` — repo-shape checks (root files, docs dirs, AGENTS.md
  symlink to CLAUDE.md).

Validators are deliberately *not* part of the contract module — they
enforce convention, not protocol. Conventions can tighten without
breaking AI agents; contracts cannot.
"""

from mycli.validators.frontmatter import (
    FrontmatterError,
    parse_skill_frontmatter,
    validate_frontmatter,
)
from mycli.validators.repo import validate_repo
from mycli.validators.skill import validate_skill, validate_skills_root

__all__ = [
    "FrontmatterError",
    "parse_skill_frontmatter",
    "validate_frontmatter",
    "validate_repo",
    "validate_skill",
    "validate_skills_root",
]
