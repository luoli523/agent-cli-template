# ADR-0002: Architecture Reset for di-cli v0.2

Status: Accepted (this commit implements the reset)
Date: 2026-05-16
Author: li.luo@shopee.com
Supersedes: ADR-0001 (preserved at git tag `v0.1-scaffold-archive`)
References: [docs/specs/2026-05-15-di-cli-architecture.md](../specs/2026-05-15-di-cli-architecture.md)

## Context

v0.1 framed di-cli as a "shared DI Toolkit" — a Markdown repository for
distributing skills, agents, MCP examples, service docs, rules, and contexts.
After surveying lark-cli's architecture and re-examining the DI 开放平台's
actual surface, we concluded that framing under-shoots the project's purpose.

The DI 开放平台 covers complex, scattered, permission-sensitive APIs across
two structurally different families:

- **Group A — Query/Compute Engines:** Spark, Flink, Presto, StarRocks, Kafka,
  ClickHouse, HBase, YARN, Livy. Operations are jobs/queries: submit → poll →
  stream → cancel. Long-running is the norm, not the exception.
- **Group B — Platform Services:** DataMap, DataService, Scheduler, DQC,
  SLA Manager, Diana, DataHub, RAM. Operations are lookup / register /
  configure / approve. Permission and lifecycle management dominate; RAM
  gates the others.

AI agents cannot reliably operate this surface today. A Markdown distribution
layer does not address the underlying problem.

## Decision

Reset the working tree. v0.2 reframes di-cli as the operation layer between
AI agents and the DI 开放平台, with cross-cutting contracts (envelope, exit
codes, risk classification, handle envelope, `_notice` channel) as the v1
deliverable. The full v0.2 architecture is captured in
[docs/specs/2026-05-15-di-cli-architecture.md](../specs/2026-05-15-di-cli-architecture.md).

The v0.1 working tree is discarded. The complete v0.1 snapshot is preserved
at the annotated git tag `v0.1-scaffold-archive` (pointing to commit
`af8c735`). Anything that needs to be inspected later — ADR-0001, the
`di-mr-flow` skill, the v0.1 validator, the v0.1 CI pipeline — can be read
via `git show v0.1-scaffold-archive:<path>`.

## What this commit ships

- `CLAUDE.md` rewritten to match v0.2 positioning (delivered in the
  pre-T1 commit and preserved here).
- `docs/specs/2026-05-15-di-cli-architecture.md` and the `.zh-CN.md` mirror
  (delivered in the pre-T1 commit and preserved here).
- This ADR.
- `README.md` / `README.zh-CN.md` rewritten to reflect pre-alpha status.
- `pyproject.toml` rewritten for the `src/di/` layout.
- `.gitignore` rewritten for the v0.2 file set.
- `.gitlab-ci.yml` placeholder (real pipeline lands in T11).
- `docs/architecture.md` reduced to a pointer to the spec.
- `src/di/__init__.py` (only file needed for `hatchling` to build the wheel).

No functional CLI capability ships in this commit. Cross-cutting contracts
land in T2; runtime in T3; commands in T4–T7; validator in T8; skills in
T9–T10; real CI in T11; release tag in T12.

## Consequences

Positive:

- Architecture is derived from mission, not from prior decisions.
- Cross-cutting contracts are the v1 deliverable, defining the protocol AI
  agents read.
- Sub-team onboarding model is explicit (schema + SKILL.md + optional
  custom shortcuts + optional credential provider extension + service ADR).
- AI is the documented primary consumer; human users are secondary.
- Identity model defers to RAM rather than inventing a binary in core.

Negative / trade-offs:

- v0.1 assets (validator, `di-mr-flow` skill, ADR-0001, prefixes config,
  contribution docs) are not carried forward into the working tree. If
  proven valuable, they must be re-derived against v0.2 contracts.
- This commit ships zero functional capability. Real value lands across
  T2 through T11.
- `pyproject.toml` declares the `di` script entry but `di.cli:main` does
  not exist until T3. `pip install -e .` succeeds; invoking `di` would
  fail with ImportError until T3 lands.

## What this ADR does not decide

- The first real service to integrate (spec § Open questions #1).
- The schema format for sub-team integrations (spec § Open questions #2).
- The async protocol per Group A engine (spec § Open questions #3).
- The `destructive-cost` gate threshold (spec § Open questions #4).
- Multi-tool support beyond Claude Code + Codex (spec § Open questions #5).
- MCP layer graduation criteria (spec § Open questions #6).
