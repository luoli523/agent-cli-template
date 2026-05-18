# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

di-cli 是 AI Agent 与 DI 开放平台 之间的操作层。它把这套复杂、分散、权限敏感的
API 包装成一套统一的命令体系，让机器能够理解、规划、执行、纠错。

**状态：v0.2 即将发布 —— 核心契约 + 基础命令 + skill 模板 + CI 已 ship；真实服务接入将在 v0.2 之后逐步引入**。

## 为什么需要 di-cli

DI 开放平台分两个结构不同的族：

- **Group A — 查询/计算引擎**：Spark、Flink、Presto、StarRocks、Kafka、
  ClickHouse、HBase、YARN、Livy。
- **Group B — 平台服务**：DataMap、DataService、Scheduler、DQC、SLA Manager、
  Diana、DataHub、RAM。

AI Agent 目前还无法可靠操作这个面。di-cli 是把它包装统一的 CLI。

完整架构见
[docs/specs/2026-05-15-di-cli-architecture.zh-CN.md](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)。

## 主要消费者

AI Agent。每条命令的输出、错误消息、退出码都被机器解析。DI 工程师是次要使用者，
直接阅读时退回到 `--format pretty`。

## 当前状态

| 层 | 状态 |
|----|------|
| 架构 spec | ✅ 已接受 |
| 横切契约（envelope / exit / risk / handle / `_notice`） | ✅ 已 ship |
| 核心命令（`install`、`update`、`doctor`、`validate`、`version`） | ✅ 已 ship |
| Skill validator（`di validate`） | ✅ 已 ship |
| `di-shared` skill 与 skill 模板 | ✅ 已 ship |
| CI（lint / typecheck / test / validate × Python 3.9, 3.13） | ✅ 已 ship |
| 真实服务接入 | ⏳ v0.2 之后 |

v0.2.0 release 打包横切协议层 + 基础设施命令。子团队的服务接入会建在这个底座之上 —— 见
[`docs/explainers/onboarding-sub-team.zh-CN.md`](docs/explainers/onboarding-sub-team.zh-CN.md)。

## 文档

- [架构 spec (中文)](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)
- [Architecture spec (English)](docs/specs/2026-05-15-di-cli-architecture.md)
- [架构决策](docs/decisions/)
- [AI 助手项目说明](CLAUDE.md)
