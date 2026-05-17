# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

di-cli 是 AI Agent 与 DI 开放平台 之间的操作层。它把这套复杂、分散、权限敏感的
API 包装成一套统一的命令体系，让机器能够理解、规划、执行、纠错。

**状态：pre-alpha（v0.2 架构重置中，暂无可用功能）**。

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
| 横切契约（envelope / exit / risk / handle / `_notice`） | 🚧 进行中 |
| 核心命令（`install`、`update`、`doctor`、`version`） | ⏳ 计划中 |
| Skill validator | ⏳ 计划中 |
| `di-shared` skill 与 skill template | ⏳ 计划中 |
| 真实服务接入 | ⏳ v1 之后 |

项目尚未可安装。进展跟着架构 spec 和 v0.2.0 release tag 推进。

## 文档

- [架构 spec (中文)](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)
- [Architecture spec (English)](docs/specs/2026-05-15-di-cli-architecture.md)
- [架构决策](docs/decisions/)
- [AI 助手项目说明](CLAUDE.md)
