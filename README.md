# di-cli

DI Toolkit for internal Data Infra developers, service owners, and on-call engineers.

The project packages DI-specific AI assistant capabilities into one maintainable repository: skills, agents, MCP examples, service documentation, rules, contexts, and future Python CLI utilities. The first version is a scaffold that defines the contribution model and repository layout before real integrations are added.

## Status

Initial scaffold. Real CLI commands, Google account authentication, production MCP servers, and service-specific tools will be added in later milestones.

## Quick Start

Python dependencies are managed with `uv`. The dependency source is `pyproject.toml`, and exact resolved versions are locked in `uv.lock`.

First-time setup:

```bash
uv sync
```

Run repository validation before submitting changes:

```bash
bash scripts/validate.sh
```

The validator requires `.venv/`, which is created by `uv sync`. Do not commit `.venv/`, local credential files, or generated auth caches.

## Goals

- Provide a shared toolkit that DI developers can install and update consistently.
- Let service owners contribute skills, agents, service docs, scripts, and MCP examples through a standard layout.
- Keep authentication and credentials centralized under the future Python CLI instead of duplicating login logic in each skill.
- Support Claude Code and Codex with one shared project instruction file.
- Make service ownership, safety boundaries, and review expectations explicit.

## Repository Layout

```text
cli/                 Future Python CLI implementation.
skills/              On-demand DI skills loaded by AI assistants.
agents/              Claude Code and Codex compatible agent definitions.
mcp/sample/          Placeholder MCP example area for future patterns.
docs/services/       Service-level docs owned by service teams.
docs/decisions/      Architecture Decision Records.
rules/               Short always-follow rules for optional installation.
contexts/            Work-mode prompts such as dev, review, research, oncall.
config/              Profiles, prefixes, and credential templates.
scripts/             Install, validate, and doctor scripts.
tests/               Convention and scaffold checks.
CLAUDE.md            Shared project instructions.
AGENTS.md            Symlink to CLAUDE.md for Codex compatibility.
```

## Planned CLI

The future CLI will be Python-based and will use the `di` command namespace.

```bash
di install
di update
di auth login
di auth status
di auth logout
di doctor
```

Until those commands exist, contributors should treat this repository as a scaffold and avoid documenting commands as available.

## Contribution Model

Each contribution should fit one of the top-level areas:

- `skills/`: task-specific DI workflows, operational knowledge, and helper scripts.
- `agents/`: focused AI sub-agents with clear scope and least-privilege behavior.
- `docs/services/`: service owner documentation, onboarding notes, API summaries, and operational playbooks.
- `mcp/`: sample or future MCP server patterns with explicit side-effect semantics.
- `config/`: templates only. Never commit real credentials.

Before adding a real service integration, define the service owner, authentication model, safety boundaries, and test strategy.

## Security

Never commit real tokens, cookies, private keys, OAuth refresh tokens, personal credentials, or production-only secrets. Credential examples must be placeholders.

See `CLAUDE.md` for the working rules used by AI coding assistants in this repository.
