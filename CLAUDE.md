# di-cli Project Instructions

`di-cli` is the shared DI Toolkit repository for Data Infra developers, service owners, and on-call engineers. It collects AI assistant capabilities such as skills, agents, MCP examples, service documentation, rules, contexts, and future Python CLI utilities.

These instructions are shared by Claude Code and Codex. `AGENTS.md` must remain a symlink to this file.

## Working Rules

1. Before writing code or changing project structure, describe the approach and wait for approval.
2. If requirements are ambiguous, ask clarifying questions before editing files.
3. If a task requires changes to more than three files, break it into smaller approved batches first.
4. For bugs, write or identify a reproducing test before fixing the behavior.
5. After code changes, list important edge cases and suggest tests.
6. If corrected by the user, state what was wrong and how the next attempt will avoid the same issue.

## Project Boundaries

This repository should be independently useful as the DI Toolkit. Keep the first implementation stages lightweight:

- Do not implement real production service calls in scaffold-only changes.
- Do not add runtime dependencies without approval.
- Do not implement Google authentication without a reviewed design.
- Do not implement production MCP servers before the sample pattern and safety rules are agreed.
- Do not split assistant instructions across competing root files; update `CLAUDE.md` and keep `AGENTS.md` linked to it.

## Directory Responsibilities

```text
cli/                 Future Python CLI implementation.
skills/              On-demand DI skills loaded by AI assistants.
agents/              Sub-agent definitions (empty placeholder; see agents/README.md).
mcp/                 MCP server patterns (empty placeholder; see mcp/README.md).
docs/services/       Service-level docs owned by service teams.
docs/decisions/      Architecture Decision Records.
rules/               Always-follow rules (empty placeholder; see rules/README.md).
contexts/            Work-mode prompts (empty placeholder; see contexts/README.md).
config/              Profiles, prefixes, and credential templates.
scripts/             Install, validate, and doctor scripts.
tests/               Convention and scaffold checks.
```

Keep service-specific details inside `docs/services/` or the relevant skill directory. Keep cross-cutting architectural decisions in `docs/decisions/`.

## Contribution Gates

Every contribution must have a clear owner, a bounded scope, and a verification path. Service-facing contributions must also document authentication, permissions, side effects, and safety boundaries before implementation.

Use `CONTRIBUTING.md` and `docs/contribution/overview.md` as the contribution governance references. If contribution rules change, update the docs and validation logic in the same approved batch.

Before adding a real service integration, confirm:

- The service owner or maintainer is named.
- The intended users and workflows are described.
- Read-only, resource-consuming, mutating, and destructive operations are distinguished.
- Mutating or destructive actions have explicit confirmation behavior.
- Authentication and permission requirements are documented.
- Tests or manual verification steps are defined.

Do not merge unowned service integrations, undocumented production mutations, or changes that weaken safety checks without a reviewed reason.

## Skills

Skills live directly under `skills/<name>/`. Nested skill directories are not allowed because AI tools generally discover only the first directory level.

Each real skill must include `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: datamap-lineage
maintainer:
  - owner@example.com
description: >
  DataMap lineage skill — query table metadata, lineage, owners, and governance hints.
  TRIGGER when: user asks about "DataMap", "lineage", "table owner", "schema", or "metadata".
  DO NOT TRIGGER when: the task is general SQL writing without metadata lookup.
---
```

Use concise skill bodies. Put detailed API notes, schemas, and playbooks in `references/`. Put helper scripts in `scripts/` inside the skill directory.

## Agents

Agents live in `agents/<name>.md`. Use one agent per responsibility, and prefer read-only behavior unless the agent explicitly needs write access.

Agent frontmatter should be compatible with both Claude Code and Codex:

```yaml
---
name: service-onboarding-reviewer
description: >
  Reviews a proposed DI service onboarding package for docs, safety boundaries, tests, and ownership gaps.
tools:
  - Read
  - Grep
  - Glob
readonly: true
---
```

## MCP

`mcp/` is an empty placeholder area. The first MCP contribution requires a reviewed design (an ADR under `docs/decisions/`) and must document:

- Tool purpose and expected user workflow.
- Authentication and identity propagation.
- Side effects: none, consumes resources, mutates state, or destructive.
- Confirmation requirements for mutating and destructive actions.
- Error shape and pagination/truncation behavior.
- Test and local run instructions.

## CLI

The future CLI is Python-based and uses the `di` command namespace. Do not add another command namespace without approval.

Planned command areas:

```bash
di install
di update
di auth login
di auth status
di auth logout
di doctor
```

Until a command is implemented and tested, document it as planned rather than available.

## Authentication And Credentials

The intended authentication model is personal company Google account login managed centrally by the future Python CLI. Individual skills should not invent their own login flow unless explicitly approved.

Never commit real credentials:

- tokens
- cookies
- private keys
- OAuth refresh tokens
- personal account secrets
- production-only secrets

Credential files in `config/` must be templates with placeholder values only.

## Documentation

Prefer short, durable docs:

- `README.md` and `README.zh-CN.md` explain the project and current status.
- `docs/services/<service>.md` explains a service from the service owner's perspective.
- `docs/decisions/NNNN-title.md` records architectural decisions that would be costly to reverse.

Docs should not claim unfinished capabilities are available.

## Validation Expectations

When validation scripts exist, run them before finishing changes:

```bash
bash scripts/validate.sh
```

For scaffold changes before validation scripts exist, manually check:

```bash
test -L AGENTS.md
readlink AGENTS.md
git status --short
```

## Naming

Use kebab-case for skills, agents, rules, contexts, and decision filenames.

Prefer service-oriented names:

- `datamap-lineage`
- `scheduler-task-debug`
- `dqc-rule-check`
- `ram-permission-debug`
- `livy-session-debug`
- `flink-job-debug`

Use clear nouns before actions. Avoid vague names such as `helper`, `tool`, or `misc`.
