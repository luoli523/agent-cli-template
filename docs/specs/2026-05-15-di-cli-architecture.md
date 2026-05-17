# Spec: di-cli — DI 操作层 for AI Agents

> **Language**: [English](2026-05-15-di-cli-architecture.md) | [中文](2026-05-15-di-cli-architecture.zh-CN.md)

Status: Accepted (Phase 1 of spec-driven workflow — Plan / Tasks / Implement pending)
Author: li.luo@shopee.com
Date: 2026-05-15

## Mission

di-cli is the operation layer between AI agents and the DI 开放平台. It wraps the
platform's complex, scattered, permission-sensitive APIs into a uniform command
system that a machine can **understand, plan, execute, and recover from**.

The DI 开放平台 covers two structurally different families:

- **Query/Compute (Group A):** Spark, Flink, Presto, StarRocks, Kafka, ClickHouse,
  HBase, YARN, Livy. Operations are jobs/queries: submit → poll → stream → cancel.
  Long-running is the norm, not the exception. Compute cost is a first-class risk.
- **Platform Services (Group B):** DataMap, DataService, Scheduler, DQC, SLA
  Manager, Diana, DataHub, RAM. Operations are lookup/register/configure/approve.
  Permission and lifecycle management dominate; RAM gates the others.

These two families have different command shapes, different error models, and
different temporal semantics. di-cli does not pretend they are the same surface.

## Primary consumer

AI Agent. Every command's output, error message, and exit code is parsed by a
machine to decide its next action. Human DI engineers are a secondary consumer
who fall back to `--format pretty` when reading directly.

The single rule this implies: **no command is complete until its failure modes
are machine-actionable.** A bare "permission denied" is a bug; the error must
tell the agent *which* scope/role is missing and *which* command would request it.

## Four design axes (the AI affordances)

The architecture is organized around what an AI needs to operate the platform.
Every contract below traces back to one of these four.

### 1. 理解 (Understand) — discover capability without external docs

- `di --help`, `di <service> --help`, `di schema <service>.<resource>.<method>`
  expose purpose, parameters, scopes, risk class, output schema.
- A `--manifest` command emits a machine-readable map of the entire CLI surface
  for agent indexing.
- Domain terminology is anchored in skill files, with explicit decision rules
  for ambiguous terms (e.g. "task" in Scheduler vs DQC).

### 2. 规划 (Plan) — chain commands predictably

- Every command obeys the same envelope and exit-code contract — AI doesn't
  re-learn shape per service.
- Every command declares **prerequisites** (e.g. an `events.patch` declares
  that the agent must first locate `event_id`).
- Async operations return a **handle envelope** (see below) so the next step is
  spelled out, not inferred.

### 3. 执行 (Execute) — invoke reliably

- JSON-first output. `--format pretty` for humans, never the default.
- Deterministic exit codes, never wrapped in shell error strings.
- `--dry-run` previews the request without executing — for both correctness and
  cost preview.
- `--yes` is the explicit consent token for risky operations (write or compute).

### 4. 纠错 (Correct errors) — recover with structured signals

- Error envelope's `hint` is a runnable command suggestion when one applies.
- Permission errors carry `permission_violations` (missing scopes), `console_url`
  (where to request), and a routed remediation path that differs by identity.
- Rate-limit / retryable errors carry retry-after metadata.
- Unrecoverable errors carry a designated escalation channel for the service.

## Cross-cutting contracts (the project's protocol surface)

### Output envelope

Success (stdout):

```json
{
  "ok": true,
  "identity": "<role>",
  "data": <object|array>,
  "meta": {"count": N, "rollback": "..."},
  "_notice": {"update": {...}, "skills": {...}, "deprecation": {...}}
}
```

Error (stderr):

```json
{
  "ok": false,
  "identity": "<role>",
  "error": {
    "type": "validation|permission|auth|api|network|internal|cost_gate|confirmation_required|deadline",
    "code": <int>,
    "message": "...",
    "hint": "run `di ram request --scope X`",
    "console_url": "https://...",
    "permission_violations": ["scope:..."],
    "retry_after_ms": <int|null>,
    "detail": {...}
  }
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API / generic error |
| 2 | Validation error |
| 3 | Auth error |
| 4 | Network error |
| 5 | Internal error |
| 6 | Cost gate (would consume more compute than the configured threshold) |
| 10 | Confirmation required — write or destructive-cost operation needs `--yes` |
| 11 | Deadline / timeout exceeded |

### Risk classification

Every command declares a `risk` in its schema. AI reads this before invoking.

| Class | Meaning | Confirmation gate |
|-------|---------|-------------------|
| `read` | No side effects | None |
| `write` | Mutates state, reversible | None — but agent should still surface what it's about to do |
| `high-risk-write` | Mutates state, hard or impossible to reverse | `--yes` required (exit 10) |
| `destructive-cost` | Triggers compute consumption above threshold | `--yes` required (exit 10) — threshold is policy, not per-command |

### Identity

`--as <role>` overrides the resolved identity. **The set of valid roles is
defined by RAM**, not by di-cli core. The CLI surfaces whatever role names
the credential provider returns. Strict mode (per-profile lock) prevents
accidental cross-role execution in CI.

This means v1 ships `--as` as a flag with no hardcoded role enum — it is a
pass-through to the credential layer.

### Credential provider interface

A Protocol-style abstract interface. Implementations form a chain:

```
env vars  →  internal SSO extension  →  RAM token resolver  →  default
```

Each provider returns an `Account` and/or a `Token` for a `TokenSpec`, or
signals "skip" (delegate to next) or "block" (terminate chain with reason).

This is the only contract that v1 must freeze; the default implementation
can be empty stubs.

### Standard flags (every command)

| Flag | Purpose |
|------|---------|
| `--as <role>` | identity override (pass-through to credential layer) |
| `--profile <name>` | switch between configured profiles |
| `--format json\|pretty\|table\|ndjson\|csv` | output format (default: json) |
| `--dry-run` | preview the request, do not execute |
| `--yes` | confirm a `high-risk-write` or `destructive-cost` operation |
| `--watch` | repeat the command on an interval (read-side, polling) |
| `--follow` | stream output (long-running ops; logs, status, results) |
| `--timeout <duration>` | client-side deadline; exits with code 11 on overrun |
| `--page-all`, `--page-limit`, `--page-size` | pagination control |

`--watch` and `--follow` are first-class because Group A's commands return
**handles**, not results, and AI must track them.

### Handle envelope (for async / long-running operations)

A command that initiates a long-running operation returns:

```json
{
  "ok": true,
  "identity": "<role>",
  "data": {
    "handle": {
      "kind": "spark.job",
      "id": "application_1735200000_0042",
      "status": "submitted",
      "actions": {
        "poll":   "di spark jobs status --id application_1735200000_0042",
        "follow": "di spark jobs status --id application_1735200000_0042 --follow",
        "logs":   "di spark jobs logs   --id application_1735200000_0042 --follow",
        "cancel": "di spark jobs cancel --id application_1735200000_0042"
      },
      "deadline": "2026-05-15T16:30:00Z"
    }
  }
}
```

AI does not infer the next command — it reads `actions`. This collapses the
"what now?" decision for every async op into a single, uniform pattern.

### `_notice` channel

Out-of-band signals not tied to the request itself. AI completes the current
task first, then surfaces the notice. Suppressible via env vars
(`DI_NO_UPDATE_NOTIFIER=1`, etc.). Types: `update`, `skills`, `deprecation`,
`auth_expiring`.

## Command architecture (graceful capability degradation)

Three command levels, used as a fallback hierarchy by the agent — not three
audiences:

```
di <service> +<verb>                Curated shortcut — smart defaults, multi-step
di <service> <resource> <method>    Compiled from service schema — 1:1 platform API
di api <service> <METHOD> <path>    Raw escape hatch — any endpoint, no curation
```

Curated shortcuts exist for high-frequency or multi-step workflows the sub-team
chose to invest in. Compiled commands cover everything the schema describes.
Raw API covers endpoints not yet in the schema. AI prefers the highest level;
degrades only when forced.

Group A (query/compute) shortcuts are designed around the **submit → handle →
poll/follow/cancel** lifecycle. Group B shortcuts are designed around the
**lookup → decide → mutate (with consent)** lifecycle.

## Skills as teaching layer

Skills do not execute. They teach AI:

- When to invoke this CLI (TRIGGER keywords + DO NOT TRIGGER markers)
- How to map domain intent to commands (terminology, decision trees)
- What failure modes are common and how to recover (Common AI Failure Modes section — accumulated)
- What is risky and requires user consent

Structure:

```
skills/
├── di-shared/SKILL.md
│   Auth, error, _notice, exit code, handle, risk, --yes protocol —
│   every other skill begins with "first read this"
├── di-skill-template/
│   Fork target for sub-teams with required sections
└── di-<service>/
    ├── SKILL.md
    └── references/   Multi-step orchestration docs loaded on demand
```

The Common AI Failure Modes section is required. It is the踩坑笔记 — the
project's accumulated experience of where agents get the platform wrong.

## Sub-team onboarding model

A DI sub-team integrates their service via:

1. **Service schema** — endpoints, params, scopes, risk class, identity
   requirements, async-handle declarations. Format chosen with the first
   integration (candidates: OpenAPI 3, lightweight YAML).
2. **SKILL.md + references/** — teaching layer.
3. **(Optional) Custom shortcuts** — Python for multi-step orchestrations
   the schema can't express.
4. **(Optional) Credential provider extension** — when service auth differs
   from the default chain.
5. **Service ADR** — owner, safety boundaries, escalation channel.

di-cli core owns: schema compiler, credential chain, output/error contracts,
shared skill, skill template, validator, install/update/doctor.

Sub-team owns: schema correctness, SKILL.md quality, custom shortcuts,
service-specific auth extension.

## Project structure

```
di-cli/
├── src/di/
│   ├── cli.py                 Entry point (argparse root)
│   ├── contracts/             Envelope, exit codes, error types, handle, risk
│   ├── credential/            Provider Protocol + chain executor
│   ├── runtime/               Common: pagination, --watch, --follow, --timeout
│   ├── shortcuts/             Hand-written per-service shortcuts (empty in v1)
│   ├── commands/              Schema-compiled commands (empty in v1)
│   ├── api/                   Raw API escape hatch
│   ├── core/                  install / update / doctor / version
│   ├── compiler/              Schema → command registration
│   └── manifest/              Surface map emitter
├── skills/
│   ├── di-shared/
│   └── di-skill-template/
├── docs/
│   ├── architecture.md
│   ├── decisions/             ADRs
│   └── specs/                 Feature/architecture specs (this file lives here)
├── tests/
│   ├── contracts/             Envelope / exit-code / handle / risk contract tests
│   ├── runtime/               --watch / --follow / pagination behavior
│   └── conventions/           Repo-shape validator
├── scripts/
├── CLAUDE.md
├── AGENTS.md → CLAUDE.md
├── README.md / README.zh-CN.md
├── pyproject.toml
└── .gitlab-ci.yml
```

## Tech stack

- Language: Python ≥ 3.9
- CLI framework: stdlib `argparse` initially; revisit Typer when shortcut count > 20
- Async / long-running: stdlib `asyncio`; SSE/WS for engines that expose them
- Secret storage: `keyring` library (cross-platform)
- Runtime deps in v1: stdlib + `PyYAML` + `keyring` only

## Distribution

Distribution channel is a packaging concern, not an architecture concern.
Switching channels later does not change any CLI code.

**v1:** `uv tool install di-cli` (recommended) or `pipx install di-cli`
(equivalent). Both install the wheel from the configured Python index. uv
additionally installs a compatible Python runtime if the user lacks one.

No single-file binary, no Node.js wrapper. If a real "zero-prerequisite
install" need surfaces later, revisit then.

## Commands

```
Install (dev, editable):  uv tool install --editable .   # or: pipx install --editable .
Test:                     uv run pytest -q
Lint:                     uv run ruff check src tests
Type check:               uv run mypy --strict src
Validate repo:            bash scripts/validate.sh
Build wheel:              uv build
Run CLI:                  di --help
```

## Code style

PEP 8, type hints required, `ruff format`, `mypy --strict`. Value objects are
frozen dataclasses. Commands return structured envelopes via dedicated
constructors — never raise bare exceptions. Stdout is data, stderr is everything
else; mixing breaks pipe chains.

## Testing strategy

- **Contract tests** (`tests/contracts/`) — envelope schema, exit-code map,
  error types, handle structure, risk-class enforcement. **Highest priority** —
  these are the protocol with AI.
- **Runtime tests** (`tests/runtime/`) — `--watch`, `--follow`, pagination,
  `--timeout` behavior with mock clocks and mock backends.
- **Convention tests** (`tests/conventions/`) — repo shape validator.
- **Service tests** — added per integration, dry-run by default; live tests
  gated by env vars, skipped on fork PRs.
- Coverage: 100% on `contracts/`; 80%+ on `runtime/` and `core/`.

## Boundaries

### Always do

- Output JSON envelope from every command (including errors)
- Declare `risk` and `identity` requirements in every command's schema
- Return `handle` envelopes from any async operation
- Return structured errors with `hint` whenever a remediation exists
- Test envelope/exit/handle/risk contracts (these are the AI protocol)

### Ask first

- Adding runtime dependencies
- Adding the first real service integration
- Implementing OAuth / token storage
- Changing the envelope, exit-code, or handle schema (contract change!)
- Changing more than 3 files in one batch

### Never do

- Commit secrets, tokens, refresh tokens
- Silently bypass `--yes` (exit 10) protocol
- Have a skill execute API calls — skills teach, they don't run
- Use a command namespace other than `di`
- Place service business logic inside a skill
- Default to `--format pretty` (humans aren't the primary consumer)

## Success criteria (sign-off conditions — all met)

- [x] Mission and the two-family capability surface (Group A / Group B)
- [x] Primary-consumer-is-AI framing and its implications
- [x] The four design axes as the design organizing principle
- [x] Cross-cutting contracts (envelope / exit / risk / handle / `_notice`) as a
      frozen protocol surface that v1 implements even with no real services
- [x] Identity model deferred to RAM (no hardcoded role enum in core)
- [x] Sub-team onboarding model: schema + SKILL.md + optional shortcuts/auth/ADR
- [x] v1 scope: contracts + structure + di-shared skill + install/update/doctor.
      Zero real services.

## Open questions (deliberately deferred)

1. **RAM identity model** — what's the actual role taxonomy? Resolved at the
   first integration that hits RAM (likely required for *any* real integration,
   so this answers itself early).
2. **Schema format** — OpenAPI 3 / lightweight YAML / something proprietary.
   Decided with the first sub-team's input.
3. **Async protocol per engine** — Spark (REST + ApplicationId), Flink (Job
   REST API), Presto (query_id), Livy (session), Kafka (consumer/topic) —
   each has its own state machine. The `handle` envelope unifies the agent
   contract, but the underlying poll mechanism is per-engine. A survey
   document is needed before Group A onboarding begins.
4. **Cost gate threshold** — `destructive-cost` triggers above what threshold?
   Policy, not code. Likely per-engine, possibly per-profile.
5. **Multi-tool support beyond Claude Code + Codex** — Cursor / Trae / Gemini
   deferred until Claude+Codex usage is established.
6. **MCP layer** — when does a service graduate from CLI command surface to a
   first-class MCP server? Dedicated ADR when the question becomes concrete.
