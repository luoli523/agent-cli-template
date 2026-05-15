# Changelog

All notable changes to di-cli are documented here.

Format: version entries are newest-first. Each entry lists what changed and why it matters to contributors and users.

---

## v0.1.0 — Scaffold Completion (2026-05-15)

First meaningful version. Brings the repository from a bare directory skeleton to a contributor-ready scaffold: convention docs, sample agents/contexts/rules, a strengthened validator, an opt-in git hook, and governance files.

### New: Convention Documentation

- `skills/README.md` and `README.zh-CN.md` — SKILL.md format, flat-directory invariant, trigger keyword description format, optional sra-toolkit-compatible fields, prefix taxonomy reference.
- `agents/README.md` and `README.zh-CN.md` — cross-tool frontmatter contract (Claude Code `tools` + Codex `readonly`), least-privilege principle, agents vs skills comparison.
- `contexts/README.md` and `README.zh-CN.md` — context vs rules vs skills, Claude Code alias setup, Codex injection, new context template.
- `rules/README.md` and `README.zh-CN.md` — when to write a rule vs skill, opt-in install paths, rule template.

### New: Sample Agents

- `agents/planner.md` — read-only implementation planner (Read, Grep, Glob / opus). Produces a structured Goal / Assumptions / Plan / Risks / Open Questions report before any code is written.
- `agents/code-reviewer.md` — convention-focused reviewer (Read, Grep, Glob, Bash / sonnet). Bash access is limited to read-only git commands and justified in the agent body. Severity-grouped findings (🔴 blocking / 🟡 warning / 🟢 nit).

### New: Sample Contexts

- `contexts/dev.md` — development mode: ship working code first, batch discipline (≤3 files), no vapor-ware.
- `contexts/review.md` — code review mode: blocking / warning / nit findings, convention checklist, no fix implementation.
- `contexts/oncall.md` — oncall mode: evidence before conclusions, read-only by default, explicit confirmation before mutating actions.

### New: Sample Rule

- `rules/git-workflow.md` — commit type table, imperative mood, 72-char first-line limit, branch naming pattern (`{username}/{type}/{description}`), MR checklist. Covers Always / Never invariants for AI assistants.

### New: Config and Templates

- `config/prefixes.json` — single source of truth for skill naming prefixes. Currently declares `di-` (department scope). `policy.enforce: "warn"` during scaffold stage.
- `config/credentials.template.json` — placeholder-only template with `_readme`, `_credential_path`, and an example service block for future skill installers.

### New: Git Hook

- `.githooks/pre-commit` — opt-in hook (activate with `git config core.hooksPath .githooks`) that runs `validate.sh` before every commit. Degrades gracefully if `.venv` is absent.
- `CONTRIBUTING.md` — added Git Hooks section documenting opt-in enable/disable.

### Validator Enhancements

- `validate_repo.py`: reads `config/prefixes.json`; skill names with an unknown prefix emit a warning (`enforce: warn`) or error (`enforce: error`).
- Description length: error when parsed description exceeds 1024 characters.
- Agent frontmatter strict types: `tools` must be `list[str]`, `readonly` must be `bool`, `model` must be `str` when present.
- Security scan now excludes `.claude/`, `.cursor/`, `.codex/`, `.venv/` — these tool-local config dirs may contain absolute paths by design.
- `validate_repo.py`: allow `README.md` and `README.zh-CN.md` directly under `skills/` and `agents/` (previously rejected as invalid files).

### Tests

- 45 pytest cases (+34 since initial scaffold), covering all new validator rules: prefix warn/error/skip, description length boundary, agent type strictness, tool-config dir exclusion, and subdirectory README allowance.

### Documentation

- `docs/specs/2026-05-14-scaffold-completion.md` — approved spec for this release.
- `docs/architecture.md` — scaffold-stage overview: component responsibilities, planned vs. implemented capabilities, out-of-scope boundaries.
- `docs/decisions/0001-scaffold-completion.md` — ADR capturing the scaffold-first strategy.

---

## v0.0.1 — Initial Scaffold (2026-05-14)

Baseline skeleton: `CLAUDE.md`, `AGENTS.md → CLAUDE.md` symlink, `README.md`, `README.zh-CN.md`, `CONTRIBUTING.md`, required directory layout, `scripts/validate_repo.py` (root / skills / agents / service-docs / security checks), `pyproject.toml` with `uv` + `pytest`.
