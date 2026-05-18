# Changelog

All notable changes to di-cli are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/) and the project adheres
to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(empty — populated as work lands on main after v0.2.0)

## [0.2.0] — 2026-05-18

The first ship of di-cli. Establishes the protocol surface, infrastructure
commands, and skill authoring conventions that all future service
integrations build on. **No real DI services are exposed in this release**
— this is the foundation, not the consumer-facing CLI.

### Added — protocol layer
- Standard envelope shape (success / error) with `_notice` channel for
  out-of-band signals
- Exit code table: `0` ok, `1` api, `2` validation, `3` auth, `4` network,
  `5` internal, `6` cost_gate, `10` confirmation_required, `11` deadline
- Error type catalogue: `validation`, `permission`, `auth`, `api`,
  `network`, `internal`, `cost_gate`, `confirmation_required`, `deadline`
- Risk classification: `read` / `write` / `high-risk-write` /
  `destructive-cost`
- Handle envelope for async / long-running operations
- Cross-cutting standard flags (`--format`, `--dry-run`, `--yes`,
  `--as`, `--profile`, `--watch`, `--follow`, `--timeout`, `--page-*`)

### Added — infrastructure commands
- `di version` — show CLI version, Python interpreter, host platform
- `di install [--target ...]` — symlink `skills/di-*/` into
  `~/.claude/skills` and `~/.codex/skills` with atomic conflict policy
- `di update [--target ...]` — re-sync + remove orphans whose source
  skill no longer exists
- `di doctor [--target ...]` — read-only health check (Python /
  source / target dirs / sync drift)
- `di validate [--scope ...]` — skill authoring + repo shape audit
  used as the CI convention gate
- `di --manifest` — machine-readable surface map of registered
  commands

### Added — skill assets
- `skills/di-shared/SKILL.md` — runtime protocol every `di-*` skill
  inherits (envelope contract, exit code policy, exit-10 confirmation
  gate, `_notice` protocol, identity sanity check, Common AI failure
  modes accumulation pattern)
- `skills/di-skill-template/` — compliant fork starting point for
  sub-team skills (excluded from `di install`)

### Added — CI + tooling
- `.gitlab-ci.yml` — lint + typecheck + test + validate across
  Python 3.9 and 3.13
- Live-repo regression gate: `tests/core/test_validate.py` runs `di
  validate` against the real `skills/` directory, so any drift in
  shipped skills fails CI immediately
- Skill validator: SKILL.md frontmatter (name, description with
  required `TRIGGER when:` / `DO NOT TRIGGER when:` markers,
  maintainer, optional version / metadata), body shape (H1 heading,
  no nested skills), and repo shape (AGENTS.md → CLAUDE.md symlink,
  pyproject, skills/, docs/{specs,decisions,explainers,reference})

### Added — documentation
- Architecture spec: `docs/specs/2026-05-15-di-cli-architecture.md` +
  Chinese mirror
- ADRs: `docs/decisions/0002-architecture-reset.md` (v0.2 reset
  rationale)
- Explainers (bilingual): `contracts-for-ai-agents`,
  `the-di-shared-skill`, `onboarding-sub-team`
- Reference (bilingual): `commands` — human-readable catalogue of
  every shipped command
- Bilingual `README.md` rewritten as a v0.2 contributor entry point
  with role-based reading lists
- `CLAUDE.md` § Validation Expectations rewritten to point at the
  real `uv run di validate` commands instead of a placeholder script

### Not in this release (post-v0.2)
- Real DI service integrations (DataMap, Scheduler, DQC, Spark,
  Flink, Presto, Livy, …)
- `di auth login` / Google OAuth device flow
- MCP server pattern
- `_notice.update` version checker against a package index
- PyPI / internal index publishing — install path is still
  `uv tool install --editable .`
- Cursor / Trae / Gemini agent support

[Unreleased]: https://git.garena.com/shopee/data-infra/di-cli-internal/-/compare/v0.2.0...main
[0.2.0]: https://git.garena.com/shopee/data-infra/di-cli-internal/-/releases/v0.2.0
