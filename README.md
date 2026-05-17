# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

di-cli is the operation layer between AI agents and the DI 开放平台. It wraps
the platform's complex, scattered, permission-sensitive APIs into a uniform
command system that machines can understand, plan, execute, and recover from.

**Status: pre-alpha (v0.2 architecture reset, no functional capability yet).**

## Why di-cli exists

The DI 开放平台 covers two structurally different families:

- **Group A — Query/Compute Engines:** Spark, Flink, Presto, StarRocks, Kafka,
  ClickHouse, HBase, YARN, Livy.
- **Group B — Platform Services:** DataMap, DataService, Scheduler, DQC, SLA
  Manager, Diana, DataHub, RAM.

AI agents cannot reliably operate this surface today. di-cli is the unified
CLI that wraps it.

The full architecture is captured in
[docs/specs/2026-05-15-di-cli-architecture.md](docs/specs/2026-05-15-di-cli-architecture.md).

## Primary consumer

AI Agent. Every command's output, error message, and exit code is parsed by a
machine. Human DI engineers are a secondary consumer who fall back to
`--format pretty`.

## Status

| Layer | State |
|-------|-------|
| Architecture spec | ✅ Accepted |
| Cross-cutting contracts (envelope / exit / risk / handle / `_notice`) | 🚧 In progress |
| Core commands (`install`, `update`, `doctor`, `version`) | ⏳ Planned |
| Skill validator | ⏳ Planned |
| `di-shared` skill + skill template | ⏳ Planned |
| Real service integrations | ⏳ Post-v1 |

The project is not installable yet. Track progress against the architecture
spec and the v0.2.0 release tag.

## Documentation

- [Architecture spec (English)](docs/specs/2026-05-15-di-cli-architecture.md)
- [架构 spec (中文)](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)
- [Architecture decisions](docs/decisions/)
- [Project instructions for AI assistants](CLAUDE.md)
