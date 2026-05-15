# di-cli Architecture

This document describes the current structure and boundaries of the di-cli repository. It reflects the scaffold stage. Capabilities marked **planned** do not yet exist; do not describe them as available in skills, agents, or documentation.

## What di-cli Is

di-cli is the shared DI Toolkit — a skill/agent/rule distribution system for Data Infra (数据基础设施) AI coding assistants. It packages team knowledge (service workflows, on-call playbooks, platform APIs) into on-demand modules consumed by Claude Code and Codex.

It is **not** a production service, a data pipeline, or an SDK. It is a knowledge and convention distribution layer.

## Current State (Scaffold Stage)

The repository ships conventions and samples. No real service integrations or runtime installers exist yet.

```
di-cli/
  skills/            On-demand knowledge modules (currently empty — samples pending)
  agents/            Sub-agent definitions (planner, code-reviewer)
  contexts/          Work-mode presets (dev, review, oncall)
  rules/             Always-loaded guidelines (git-workflow)
  config/            Prefix taxonomy and credential templates
  scripts/           validate.sh + validate_repo.py
  tests/             pytest convention checks
  .githooks/         opt-in pre-commit hook
  docs/              Architecture, decisions, specs, service docs
  cli/               Placeholder for future Python CLI
  mcp/sample/        Placeholder for future MCP server patterns
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

Sub-agents with restricted tool access. Each agent is a single markdown file (`agents/<name>.md`) with YAML frontmatter. Agents run as separate entities — not injected into the main conversation like skills.

Current agents:
- `planner`: read-only implementation planner (Read, Grep, Glob / opus).
- `code-reviewer`: convention-focused reviewer with read-only git access (Read, Grep, Glob, Bash / sonnet).

### contexts/

System-prompt presets injected at session start. Not YAML-fronted; plain markdown. Three modes: `dev`, `review`, `oncall`. Users install by aliasing `claude --system-prompt "$(cat ...)"`.

### rules/

Always-loaded guidelines. Currently one rule: `git-workflow.md`. Users opt in by symlinking to `~/.claude/rules/` or `~/.codex/rules/`. Rules are **not** auto-installed.

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
- Convention documentation (READMEs, CLAUDE.md, CONTRIBUTING.md).
- Sample agents, contexts, rules.
- Validator and git hooks.
- Credential and prefix templates.
- Architecture and decision records.

**Out of scope until explicitly approved:**
- Real service integrations (any `skills/<name>/scripts/` calling a production API).
- Google authentication implementation.
- Production MCP servers.
- Any new command namespace beyond `di`.
- Cursor adaptation.

## Decision Log

Significant architectural choices are recorded in `docs/decisions/`. See `0001-scaffold-completion.md` for the rationale behind the scaffold-first approach.
