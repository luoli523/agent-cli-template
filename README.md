# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

di-cli is the operation layer between AI agents and the DI 开放平台. It wraps
the platform's complex, scattered, permission-sensitive APIs into a uniform
command system that machines can understand, plan, execute, and recover from.

**Status: v0.2 ready to ship — protocol surface, infrastructure commands, skill template, and CI all in place. Real service integrations roll in on top of this in subsequent releases.**

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
| Cross-cutting contracts (envelope / exit / risk / handle / `_notice`) | ✅ Shipped |
| Core commands (`install`, `update`, `doctor`, `validate`, `version`) | ✅ Shipped |
| Skill validator (`di validate`) | ✅ Shipped |
| `di-shared` skill + skill template | ✅ Shipped |
| CI (lint / typecheck / test / validate × Python 3.9, 3.13) | ✅ Shipped |
| Real service integrations | ⏳ Post-v0.2 |

The v0.2.0 release packages the cross-cutting protocol surface and the
infrastructure commands. Sub-team service integrations land on top of
this foundation — see [`docs/explainers/onboarding-sub-team.md`](docs/explainers/onboarding-sub-team.md).

## Documentation

- [Architecture spec (English)](docs/specs/2026-05-15-di-cli-architecture.md)
- [架构 spec (中文)](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)
- [Architecture decisions](docs/decisions/)
- [Project instructions for AI assistants](CLAUDE.md)
