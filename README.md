# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Shared DI Toolkit for internal Data Infra developers, service owners, business teams, and on-call engineers.

This project exists to consolidate the AI toolkits that DI teams currently maintain separately. The goal is to give every team a common home for skills, agents, service documentation, rules, contexts, MCP patterns, and future CLI utilities, with authentication managed centrally instead of duplicated in each toolkit.

By collecting these tools in one repository, each team can make its own knowledge reusable by others and can also adopt workflows already organized by peer teams. This should reduce duplicated automation, make operational playbooks easier to discover, and let service-specific experience compound across DI instead of staying isolated in separate repos.

## Status

Scaffold stage with one real skill: [`di-mr-flow`](skills/di-mr-flow/SKILL.md), the standard GitLab merge-request workflow for this repository.

Available today:

- Repository conventions for skills, agents, service docs, MCP patterns, rules, contexts, and future CLI work.
- `di-mr-flow`, covering branch creation, commit, push, MR creation, CI, squash merge, and cleanup.
- `bash scripts/validate.sh`, the repository convention and safety validator.
- `uv run pytest tests/ -q`, the pytest convention test suite.
- Optional `.githooks/pre-commit`, which runs validation before commits when enabled.
- Prefix taxonomy in `config/prefixes.json`; skill names currently must use the declared `di-` prefix.

Not implemented yet:

- Real `di` CLI commands.
- Central Google account authentication.
- Production MCP servers.
- Service-specific production integrations.
- Shipped agents, contexts, or rules beyond placeholder authoring guidance.

## Quick Start

Python dependencies are managed with `uv`. The dependency source is `pyproject.toml`, and exact resolved versions are locked in `uv.lock`.

First-time setup:

```bash
uv sync --extra dev
```

Run repository validation before submitting changes:

```bash
bash scripts/validate.sh
uv run pytest tests/ -q
```

The validator requires `.venv/`, which is created by `uv sync --extra dev`. Do not commit `.venv/`, local credential files, or generated auth caches.

To enable the opt-in pre-commit hook:

```bash
git config core.hooksPath .githooks
```

## Goals

- Provide a shared toolkit that DI developers and business teams can install and update consistently.
- Gradually bring team-maintained AI toolkits into one project so knowledge, workflows, and helpers can be reused across DI.
- Let service owners contribute skills, agents, service docs, scripts, and MCP examples through a standard layout.
- Keep authentication and credentials centralized under the future Python CLI instead of duplicating login logic in each team toolkit or skill.
- Support Claude Code and Codex with one shared project instruction file.
- Make service ownership, safety boundaries, and review expectations explicit.

## Repository Layout

```text
cli/                 Placeholder for the future Python CLI implementation.
skills/              On-demand DI skills loaded by AI assistants; currently ships di-mr-flow.
agents/              Empty placeholder; see agents/README.md for authoring guidance.
mcp/                 Empty placeholder for future MCP server patterns.
docs/services/       Service-level docs owned by service teams; currently empty.
docs/decisions/      Architecture Decision Records.
rules/               Empty placeholder for optional always-follow rules.
contexts/            Empty placeholder for work-mode prompts.
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

Business and service teams are encouraged to migrate their maintained AI toolkit pieces into this repository incrementally. Start with durable knowledge artifacts, read-only workflows, and scaffolded skills before adding integrations that call production services.

Before adding a real service integration, define the service owner, authentication model, safety boundaries, and test strategy.

## Security

Never commit real tokens, cookies, private keys, OAuth refresh tokens, personal credentials, or production-only secrets. Credential examples must be placeholders.

See `CLAUDE.md` for the working rules used by AI coding assistants in this repository.
