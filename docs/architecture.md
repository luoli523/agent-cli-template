# di-cli Architecture

This document describes the current structure and boundaries of the di-cli repository. It reflects the scaffold stage. Capabilities marked **planned** do not yet exist; do not describe them as available in skills, agents, or documentation.

## What di-cli Is

di-cli is the shared DI Toolkit — a skill/agent/rule distribution system for Data Infra (数据基础设施) AI coding assistants. It packages team knowledge (service workflows, on-call playbooks, platform APIs) into on-demand modules consumed by Claude Code and Codex.

It is **not** a production service, a data pipeline, or an SDK. It is a knowledge and convention distribution layer.

## Current State (Scaffold Stage)

The repository ships conventions plus one real skill (`di-mr-flow`). All other extension directories are intentional placeholders — the team adds content there only when a real need shows up.

```
di-cli/
  skills/            On-demand knowledge modules (1 real: di-mr-flow)
  agents/            Empty placeholder; see agents/README.md
  contexts/          Empty placeholder; see contexts/README.md
  rules/             Empty placeholder; see rules/README.md
  mcp/               Empty placeholder; see mcp/README.md
  config/            Prefix taxonomy and credential templates
  scripts/           validate.sh + validate_repo.py
  tests/             pytest convention checks
  .githooks/         opt-in pre-commit hook
  docs/              Architecture, decisions, specs, service docs
  cli/               Placeholder for future Python CLI
```

## Component Responsibilities

### skills/

On-demand knowledge modules. Each skill is a directory (`skills/<name>/`) containing `SKILL.md` with YAML frontmatter. AI tools load a skill when the user's task matches its `description` trigger keywords.

Rules:
- Flat structure only (no nesting).
- `name` must equal the directory name.
- `description` must include `TRIGGER when:` and `DO NOT TRIGGER when:` and be ≤ 1024 characters.
- `maintainer` is required.
- Skill names must start with a prefix declared in `config/prefixes.json`.

### agents/

Sub-agents with restricted tool access. **Empty placeholder.** Cross-tool format is unresolved: Claude Code uses Markdown + YAML frontmatter at `~/.claude/agents/<name>.md`; Codex uses TOML at `~/.codex/agents/<name>.toml`. Until the team decides whether to ship parallel files, generate them, or pick one tool, no samples ship. See `agents/README.md` for the authoring contract and validator behavior.

### contexts/

System-prompt presets injected at session start. **Empty placeholder.** No contexts ship yet — see `contexts/README.md` for when to add one and the recommended format.

### rules/

Always-loaded guidelines for Claude Code (`~/.claude/rules/`) and Codex (appended to `~/.codex/AGENTS.md`). **Empty placeholder.** No rules ship yet — see `rules/README.md` for install styles and authoring conventions.

### mcp/

MCP server patterns. **Empty placeholder.** The first contribution requires a reviewed ADR — see `mcp/README.md` and `CONTRIBUTING.md` § MCP Contributions.

### config/

- `prefixes.json` — single source of truth for skill naming prefixes. Validator reads it.
- `credentials.template.json` — placeholder template. The future installer merges it into `~/.config/di/credentials.json` and prompts for real values.

### scripts/validate_repo.py

Convention validator. Checks:
- Root file presence and `AGENTS.md → CLAUDE.md` symlink.
- `skills/`: flat layout, frontmatter, prefix, description length, trigger markers.
- `agents/`: frontmatter types (`tools` list[str], `readonly` bool, `model` str), `readonly` warning.
- `docs/services/`: kebab-case filenames.
- Security scan: credentials patterns, personal absolute paths; excludes `.git`, `.claude`, `.cursor`, `.codex`, `.venv`.

### .githooks/pre-commit

Opt-in hook. Activate with `git config core.hooksPath .githooks`. Runs `validate.sh`. Degrades gracefully if `.venv` is absent.

## Planned (Not Yet Implemented)

The following are documented as planned in `CLAUDE.md`. Do not reference them as available.

| Capability | Notes |
|---|---|
| `di install` | Python CLI — installs skills, symlinks agents and rules. |
| `di update` | Python CLI — pulls latest and re-links. |
| `di auth login / status / logout` | Google account OAuth flow, managed centrally. |
| `di doctor` | Environment health check. |
| MCP server | First pattern lands after design review in `docs/decisions/`. |
| Real skill integrations | Require owner, auth design, safety review. See `CONTRIBUTING.md`. |

## Boundaries

**In scope for scaffold stage:**
- Convention documentation (per-directory READMEs, CLAUDE.md, CONTRIBUTING.md).
- One real skill (`di-mr-flow`) exercising the full MR workflow end-to-end.
- Validator and git hooks.
- Credential and prefix templates.
- Architecture and decision records.

**Intentional placeholders (filled when real consumers appear):**
- `agents/`, `contexts/`, `rules/`, `mcp/` — see each directory's README.

**Out of scope until explicitly approved:**
- Real service integrations (any `skills/<name>/scripts/` calling a production API).
- Google authentication implementation.
- Production MCP servers.
- Any new command namespace beyond `di`.
- Cursor adaptation.

## Decision Log

Significant architectural choices are recorded in `docs/decisions/`. See `0001-scaffold-completion.md` for the rationale behind the scaffold-first approach.
