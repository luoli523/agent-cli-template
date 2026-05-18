# di-cli Project Instructions

di-cli is the operation layer between AI agents and the DI 开放平台
(Spark, Flink, Presto, StarRocks, Kafka, ClickHouse, HBase, YARN, Livy +
DataMap, DataService, Scheduler, DQC, SLA Manager, Diana, DataHub, RAM).
It wraps the platform's complex, scattered, permission-sensitive APIs into
a uniform command system that machines can understand, plan, execute, and
recover from.

Full architecture: [docs/specs/2026-05-15-di-cli-architecture.md](docs/specs/2026-05-15-di-cli-architecture.md)
(中文: [docs/specs/2026-05-15-di-cli-architecture.zh-CN.md](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)).

These instructions are shared by Claude Code and Codex. `AGENTS.md` must
remain a symlink to this file.

## Primary Consumer

AI Agent. Every command's output, error message, and exit code is parsed by
a machine to decide its next action. Human DI engineers are a secondary
consumer who fall back to `--format pretty` when reading directly.

## Working Rules

1. Before writing code or changing project structure, describe the approach and wait for approval.
2. If requirements are ambiguous, ask clarifying questions before editing files.
3. For bugs, write or identify a reproducing test before fixing the behavior.
4. After code changes, list important edge cases and suggest tests.
5. If corrected by the user, state what was wrong and how the next attempt will avoid the same issue.

## Project Boundaries

- Do not add runtime dependencies beyond stdlib + PyYAML + keyring without approval.
- Do not implement real service calls until the relevant service ADR is reviewed.
- Do not implement authentication / OAuth / token storage until the credential provider chain interface is frozen.
- Do not change the envelope, exit-code, or handle schema — these are the frozen protocol surface; contract change requires explicit approval.
- Do not implement production MCP servers before the sample pattern and safety rules are agreed.
- Do not split assistant instructions across competing root files; update `CLAUDE.md` and keep `AGENTS.md` linked to it.

## Directory Responsibilities

```text
src/di/             Python CLI source.
  contracts/        Envelope, exit codes, error types, handle, risk classification.
  credential/       Credential provider Protocol + chain executor.
  runtime/          Standard flag plumbing, output layer, --watch/--follow/--timeout.
  shortcuts/        Per-service hand-written shortcuts.
  commands/         Schema-compiled commands.
  api/              Raw API escape hatch.
  core/             install / update / doctor / version.
  compiler/         Schema → command registration.
  manifest/         Surface map emitter.
skills/             AI teaching layer (Markdown).
  di-shared/        Auth/error/handle/risk/notice protocol; every other skill imports it.
  di-skill-template/ Fork target for sub-teams.
  di-<service>/     Per-service skill.
docs/
  architecture.md   High-level overview pointing to the spec.
  decisions/        Architecture Decision Records.
  specs/            Feature / architecture specifications.
tests/
  contracts/        Envelope / exit-code / handle / risk contract tests.
  runtime/          --watch / --follow / pagination / --timeout behavior.
  conventions/      Repo-shape validator.
scripts/            Install / validate / doctor scripts.
```

## Cross-Cutting Contracts (Protocol Surface)

The v1 deliverable is a frozen protocol surface: envelope schema, exit codes,
error types, handle envelope, risk classification, `_notice` channel. These
are the contract with AI agents. Exact definitions in
`docs/specs/2026-05-15-di-cli-architecture.md` § Cross-cutting contracts.

Any change to envelope, exit codes, or handle structure is a contract change
and requires explicit approval.

## Three-Layer Command Architecture

Three command levels — a fallback hierarchy chosen by the agent, not three
audiences:

```
di <service> +<verb>                Curated shortcut — high-level, smart defaults
di <service> <resource> <method>    Compiled from service schema — 1:1 platform API
di api <service> <METHOD> <path>    Raw escape hatch — any endpoint, no curation
```

AI prefers the highest level; degrades only when forced.

## Skills

**Skills do not execute.** They teach AI how to use CLI commands.

Skills live directly under `skills/<name>/`. Nested skill directories are not
allowed because AI tools discover only the first directory level.

All skill names must start with the `di-` prefix (enforced by validator).

Each real skill must include `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: di-datamap-lineage
maintainer:
  - owner@example.com
description: >
  DataMap lineage skill — query table metadata, lineage, owners, and governance hints.
  TRIGGER when: user asks about "DataMap", "lineage", "table owner", or "metadata".
  DO NOT TRIGGER when: the task is general SQL writing without metadata lookup.
---
```

Every service skill begins with `CRITICAL — first read ../di-shared/SKILL.md`.
The "Common AI Failure Modes" section is required — it accumulates 踩坑笔记
from real agent use.

Use concise SKILL.md bodies. Put detailed workflow docs in `references/`.

## Sub-team Onboarding

A DI sub-team brings a service into di-cli by providing:

1. **Service schema** — endpoints, params, scopes, risk class, identity requirements, async-handle declarations.
2. **SKILL.md + references/** — teaching layer.
3. **(Optional) Custom shortcuts** — Python for multi-step orchestrations.
4. **(Optional) Credential provider extension** — when service auth differs from default.
5. **Service ADR** — owner, safety boundaries, escalation channel.

Onboarding gates (must be satisfied before merge):

- Service owner / maintainer named in SKILL.md frontmatter and ADR
- Read / write / high-risk-write / destructive-cost operations distinguished via `risk` class
- Mutating and destructive operations have `--yes` confirmation behavior
- Identity and scope requirements documented
- Tests or manual verification steps defined

## Agents

Out of scope. Claude Code and Codex use incompatible agent formats; revisit
once skills usage is established.

## MCP

Out of scope until a service graduates from CLI to a first-class MCP server.
The first MCP contribution requires a reviewed ADR under `docs/decisions/`
documenting tool purpose, identity propagation, side effects, confirmation
requirements, error shape, and test instructions.

## Identity & Credentials

`--as <role>` overrides the resolved identity. The set of valid roles is
defined by RAM, not by di-cli core. v1 ships the credential provider Protocol
with a placeholder default implementation; real implementations land per
service onboarding.

Never commit real credentials: tokens, cookies, private keys, OAuth refresh
tokens, personal account secrets, production-only secrets.

## Documentation

Prefer short, durable docs:

- `README.md` / `README.zh-CN.md` — project overview and current status.
- `docs/specs/<date>-<topic>.md` — architecture and feature specifications.
- `docs/decisions/NNNN-title.md` — ADRs for hard-to-reverse decisions.

Docs must not claim unfinished capabilities are available.

## Validation Expectations

Before opening an MR, run the same checks CI runs (see `.gitlab-ci.yml`).
Each step also has its own exit code so an AI agent can branch on the
result the way ``di doctor`` and ``di validate`` envelopes intend:

```bash
uv run ruff check src tests   # lint
uv run mypy --strict src      # types
uv run pytest -q              # tests
uv run di validate            # repo + skills conventions
```

`di validate` emits the standard envelope on stdout (healthy / degraded)
or stderr (unhealthy). Walk the ``checks`` list when a step is not
``ok`` — each entry carries its own ``hint``.

## Naming

Use kebab-case for skill / agent / decision filenames.

All skill names must start with the `di-` prefix. Prefer service-oriented names:

- `di-datamap-lineage`
- `di-scheduler-task-debug`
- `di-dqc-rule-check`
- `di-ram-permission-debug`
- `di-livy-session-debug`
- `di-flink-job-debug`

Use clear nouns before actions. Avoid vague names like `helper`, `tool`, `misc`.

## Boundaries

### Always do

- Output JSON envelope from every command (including errors)
- Declare `risk` and identity requirements in every command's schema
- Return `handle` envelopes from any async operation
- Return structured errors with `hint` whenever a remediation exists
- Test envelope / exit-code / handle / risk contracts (these are the AI protocol)

### Ask first

- Adding runtime dependencies
- Adding the first real service integration
- Implementing OAuth / token storage
- Changing envelope, exit-code, or handle schema (contract change!)

### Never do

- Commit secrets, tokens, refresh tokens
- Silently bypass `--yes` (exit 10) protocol
- Have a skill execute API calls — skills teach, they don't run
- Use a command namespace other than `di`
- Place service business logic inside a skill
- Default to `--format pretty` (humans aren't the primary consumer)
