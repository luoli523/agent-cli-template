# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Internal CLI for Data Infra engineers and AI agents working with the DI 开放平台 (DI open platform).

**Status: v0.2 ready** — protocol surface, infrastructure commands, skill template, and CI all in place. Real service integrations roll in on top of this in subsequent releases.

---

## What it is

The DI 开放平台 covers two structurally different families:

- **Group A — Query / Compute engines**: Spark, Flink, Presto, StarRocks, Kafka, ClickHouse, HBase, YARN, Livy. Lifecycle is typically `submit → poll → logs → cancel`. Long-running is the norm.
- **Group B — Platform services**: DataMap, DataService, Scheduler, DQC, SLA Manager, Diana, DataHub, RAM. Lifecycle is `lookup → decide → mutate → recover`. Permission-sensitive, RAM-gated.

AI agents cannot reliably operate this surface today. di-cli is the unified CLI that wraps it. The full architecture (three-layer command model, frozen protocol surface, sub-team contribution model) is captured in [`docs/specs/2026-05-15-di-cli-architecture.md`](docs/specs/2026-05-15-di-cli-architecture.md).

**Primary consumer**: AI agents. Every command output, error message, and exit code is parsed by a machine. Human DI engineers are the secondary consumer; they fall back to `--format pretty` for direct reading.

---

## What ships in v0.2

The v0.2 surface is **agent-facing protocol + tooling**, not service integrations. All of the below are in `main` and exercised by CI on every MR.

| Layer | What it provides |
|-------|------------------|
| Cross-cutting protocol surface | Envelope, exit codes, error types, handle, risk classification, `_notice` channel |
| Infrastructure commands | `di install` / `update` / `doctor` / `validate` / `version` |
| Skill validator (`di validate`) | Enforces SKILL.md frontmatter, body shape, and repo conventions |
| `di-shared` skill | Runtime protocol every future skill inherits |
| `di-skill-template` | Compliant fork starting point for sub-team skills |
| CI pipeline | `lint` + `typecheck` + `test` + `validate` × Python 3.9, 3.13 |
| Bilingual docs | spec / decisions / explainers / reference, EN + 中文 |

## What does NOT ship in v0.2

Tracking these explicitly so sub-teams don't waste time looking for them:

| Capability | Where it stands |
|------------|-----------------|
| Real service integrations (DataMap, Scheduler, …) | Post-v0.2 — first sub-team co-designs the schema format. |
| `di auth login` / Google OAuth | Post-v0.2 — pending design ADR before code lands. |
| MCP server pattern | Deferred — requires reviewed ADR per [`CLAUDE.md`](CLAUDE.md) § MCP. |
| `_notice.update` version checker | Deferred — pending PyPI / internal index strategy. |
| PyPI / internal index publish | Comes with release tooling after v0.2 ship. |
| Cursor / Trae / Gemini support | Out of scope until Claude Code + Codex usage stabilizes. |

---

## Repository layout

```text
di-cli/
├── src/di/
│   ├── contracts/         Envelope, exit codes, error types, handle, risk, _notice
│   ├── core/              Infrastructure commands (install/update/doctor/validate/version)
│   ├── runtime/           Standard flags, output layer, Check primitive
│   ├── manifest/          --manifest surface emitter
│   ├── validators/        SKILL.md frontmatter, skill-shape, repo-shape checks
│   ├── shortcuts/         (post-v0.2) Per-service hand-written shortcuts
│   ├── commands/          (post-v0.2) Schema-compiled commands
│   ├── compiler/          (post-v0.2) Schema → command registration
│   └── api/               (post-v0.2) Raw API escape hatch
├── skills/
│   ├── di-shared/         Runtime protocol every di-* skill inherits
│   └── di-skill-template/ Fork starting point (NOT installed by `di install`)
├── docs/
│   ├── specs/             Architecture spec (normative)
│   ├── decisions/         ADRs
│   ├── explainers/        Teaching docs — "why this protocol shape"
│   └── reference/         Lookup tables — "what commands ship, what they do"
├── tests/                 contracts / runtime / core / validators
├── .gitlab-ci.yml         CI: lint + typecheck + test + validate
├── CLAUDE.md              AI assistant project instructions
├── AGENTS.md              Symlink → CLAUDE.md (Codex + Claude share one file)
└── pyproject.toml
```

---

## Available commands (v0.2)

Five infrastructure commands. They operate on the local machine or on di-cli itself; no DI service is wired up yet.

| Command | What it does | Risk |
|---------|--------------|------|
| `di version` | Show CLI version, Python interpreter, host platform | read |
| `di install [--target ...]` | Symlink `skills/di-*/` into `~/.claude/skills` and `~/.codex/skills` | write |
| `di update [--target ...]` | Re-sync skills + remove orphans | write |
| `di doctor [--target ...]` | Health check — source / target dirs / sync drift | read |
| `di validate [--scope ...]` | Repo + skills convention audit (CI gate) | read |

Full per-command behaviors, envelope shapes, and examples → [**Command reference**](docs/reference/commands.md). Machine-readable surface → `di --manifest`.

---

## Where to start, by role

### 🔧 Sub-team service owner — *"How do I expose my service to AI agents?"*

1. [`docs/explainers/onboarding-sub-team.md`](docs/explainers/onboarding-sub-team.md) — the 6-step procedural flow (start here).
2. [`docs/explainers/the-di-shared-skill.md`](docs/explainers/the-di-shared-skill.md) — what your skill must defer to.
3. [`docs/explainers/contracts-for-ai-agents.md`](docs/explainers/contracts-for-ai-agents.md) — why the protocol is shaped this way.
4. [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md) — skim; this is what your agents read at runtime.
5. [`skills/di-skill-template/README.md`](skills/di-skill-template/README.md) — fork and start.

### 🤖 AI agent author / di-cli runtime user

1. [`docs/explainers/contracts-for-ai-agents.md`](docs/explainers/contracts-for-ai-agents.md) — the protocol your agent consumes.
2. [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md) — canonical runtime instructions.
3. [`docs/reference/commands.md`](docs/reference/commands.md) — command catalogue.
4. `di --manifest` — machine-readable surface at runtime.

### 🛠 di-cli core maintainer

1. [`docs/specs/2026-05-15-di-cli-architecture.md`](docs/specs/2026-05-15-di-cli-architecture.md) — normative spec.
2. [`docs/decisions/`](docs/decisions/) — ADRs (especially [`0002-architecture-reset.md`](docs/decisions/0002-architecture-reset.md)).
3. [`CLAUDE.md`](CLAUDE.md) — project boundaries, working rules.
4. `src/di/contracts/` — frozen protocol surface.
5. `tests/contracts/` — contract tests guarding the protocol.

### 🧪 Just trying it locally

```bash
git clone <this-repo> && cd di-cli-internal
uv tool install --editable .
di --manifest
di doctor
```

`di doctor` will flag `target_dirs` as `warn` if you don't have Claude Code or Codex installed — that's normal.

---

## Local development

Same commands CI runs (see [`.gitlab-ci.yml`](.gitlab-ci.yml)):

```bash
uv sync --frozen --extra dev
uv run ruff check src tests
uv run mypy --strict src
uv run pytest -q
uv run di validate
```

For repo conventions, working rules, and project boundaries see [`CLAUDE.md`](CLAUDE.md).

---

## Documentation map

| Audience | Document |
|----------|----------|
| Project maintainer | [Architecture spec](docs/specs/2026-05-15-di-cli-architecture.md) · [架构 spec](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md) |
| Project maintainer | [`docs/decisions/`](docs/decisions/) — ADRs |
| Engineer learning the project | [Contracts: why this protocol shape](docs/explainers/contracts-for-ai-agents.md) · [中文](docs/explainers/contracts-for-ai-agents.zh-CN.md) |
| Sub-team contributor | [Onboarding a sub-team](docs/explainers/onboarding-sub-team.md) · [中文](docs/explainers/onboarding-sub-team.zh-CN.md) |
| Sub-team contributor | [The di-shared skill explained](docs/explainers/the-di-shared-skill.md) · [中文](docs/explainers/the-di-shared-skill.zh-CN.md) |
| AI agent at runtime | [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md) |
| Sub-team contributor | [`skills/di-skill-template/README.md`](skills/di-skill-template/README.md) — fork starting point |
| Anyone browsing commands | [Command reference](docs/reference/commands.md) · [中文](docs/reference/commands.zh-CN.md) |
| AI assistants (Claude Code / Codex) | [`CLAUDE.md`](CLAUDE.md) — working rules, boundaries |

---

## Project boundaries

di-cli ships a **frozen protocol surface** (envelope, exit codes, handle structure, risk classification). Changes to these require explicit approval and an ADR. See [`CLAUDE.md`](CLAUDE.md) § Project Boundaries for the full "always do / ask first / never do" list.

---

## What's next

Post-v0.2 work is **service-driven**:

- **First real service skill** — picks a high-pain workflow (DataMap lineage lookup or Scheduler task debug are likely candidates), exercises the full onboarding flow, validates the design end-to-end.
- **`di auth login`** — Google OAuth device flow + keyring storage. Lands when the first identity-bearing service is ready.
- **Schema compiler** — co-design the schema format with the first sub-team, then ship `src/di/compiler/` and `src/di/commands/`.
- **PyPI / internal index publish** — needed for `pipx install di-cli` to work without `--editable`.

Track via the v0.2.0 tag and subsequent release tags.
