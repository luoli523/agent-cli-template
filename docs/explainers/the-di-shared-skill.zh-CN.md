# di-shared skill —— 是什么、谁读、为什么存在

> **Language**: [English](the-di-shared-skill.md) | [中文](the-di-shared-skill.zh-CN.md)

这份文档解释 `skills/di-shared/SKILL.md` 这个**资产**本身 —— 它是什么、谁消费、子团队怎么和它相处。它**不重复** skill 里的内容；agent 实际要遵守的规则在 skill 文件本身里。

如果你是一个加载了 di-cli skill 的 AI agent，不需要读这份文档 —— 直接读 [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)（英文）。

## 是什么

`di-shared` 是一个 skill —— Markdown + YAML frontmatter —— 它教 AI agent 怎么消费 di-cli 的操作协议：envelope shape、退出码、错误恢复、`_notice` 通道、`exit 10` 确认门禁、身份 sanity check。它是**每个 `di-*` skill 的隐式依赖**。

把它当成跨服务的"基类"：每个服务 skill 第一行就写 "CRITICAL — read `../di-shared/SKILL.md` first"，然后只记录自己服务特有的内容。

## 谁读

| 读者 | 时机 |
|------|------|
| **AI agent** | 运行时，调任何 `di` 命令前。这是主要、也是 intended 的消费者。 |
| 子团队贡献者 | 一次性 —— 学习协议是什么的时候，理解自己的服务 skill 要 defer 给它什么。 |
| di-cli 维护者 | 更新协议契约时，让教学层同步。 |

它**不是**新 skill 的复制粘贴源，**也不是**人类用来理解"协议为什么这样设计"的文档 —— 那是 [`contracts-for-ai-agents.zh-CN.md`](contracts-for-ai-agents.zh-CN.md)。

## 为什么存在

横切契约（envelope、退出码、风险等级、`_notice`、身份）**跨所有服务都完全一致**。如果没有 `di-shared`：

- 每个服务 skill 都要从头再解释一遍同一套协议。
- skill 之间的漂移不可避免 —— 一个说 "exit 10 意思是 X"，下一个说的可能微妙不同。
- 更新协议意味着改 N 份 skill，而不是一份。

`di-shared` 通过成为**单一教学点**解决这个问题。服务 skill 链到它；不复制它。改协议 → 改一份文件 → 每个 skill 通过引用自动同步。

## 内容（章节速查）

skill 共有 13 个章节。用下表判断该查哪一节；具体内容打开 skill 本身。

| 章节 | 一句话总结 |
|------|-----------|
| CRITICAL — first actions | 调 `di` 前先读这份 skill；默认 `--format json`。 |
| Envelope contract | success / error envelope 形态；`stdout = 数据, stderr = 其余`。 |
| Exit code → action | 退出码 → 恢复动作 的查表。 |
| Error.type catalogue | 粗分类 —— `validation`、`permission`、`auth` 等 —— 以及每种的恢复策略。 |
| Permission errors — recovery protocol | 读 `permission_violations` + `hint`；`console_url` 原样转交。 |
| exit 10 protocol | 最常被违反的规则。确认门禁行为 + 明确的*禁止*列表。 |
| `_notice` protocol | 带外信号；不打断当前任务；之后再提。 |
| Identity (`--as`) — sanity check | 每个 envelope 都回显 `identity` —— 用来确认 lens 是不是预期的锚。 |
| Three-layer command surface | shortcut > resource.method > 裸 `di api`；agent 的优先序。 |
| Available infrastructure commands (v0.2) | v0.2 五个命令的表 + 风险等级。 |
| Common AI failure modes | 累积观察到的 agent 错误。F-001 已 seed；新的随观察添加。 |
| When to stop and ask the user | 默认要确认的清单。 |
| Glossary | Envelope / identity / risk / handle / `_notice` / manifest。 |

## 子团队怎么和它相处

三条规则。

1. **链过去，不复制。** 每个新 skill 第一行写 `CRITICAL — read ../di-shared/SKILL.md first`。不要把协议规则粘到新 skill 里 —— 它们会漂移。
2. **沿用它的术语。** 如果你的服务有概念跟 envelope / identity / risk / handle 重叠，用 `di-shared` 用的词。发明新词只会让 agent 的心智模型碎片化。
3. **如果你需要一条与 di-shared 冲突的规则，写 ADR。** 不要 fork 规则到自己的 skill 里。协议表面是被治理的（见 [`CLAUDE.md`](../../CLAUDE.md) § Project Boundaries）—— 契约变更是项目级决策，不是 skill 级决策。

## 怎么保持准确

三个机制让 `di-shared` 不偏离：

- **真相源 pinning。** 它教的契约定义在 [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § 横切契约。envelope shape、退出码、错误类型、handle 结构、风险等级的改动需要 CLAUDE.md 显式批准。
- **结构校验。** T8 的 `di validate --scope skills` 在每个 MR（以及本地）跑，frontmatter 或正文形态退化的 skill 会被拒。di-shared 也不例外。
- **Live-repo 回归门。** `tests/core/test_validate.py::test_validate_passes_against_live_repo_skills` 对 checkout 里**实际**的 `skills/di-shared/SKILL.md` 跑 validator。改坏文件的人会立刻在 CI 红。

## 什么时候才改它

改动**少见**。"AI agent 应该知道什么"的大多数新增都属于服务 skill，不属于 di-shared。合理的触发：

- **真实生产 trace 里观察到新的跨服务 AI 失败模式** → 在 "Common AI failure modes" 加一条新 `F-N`。这是改这份文件最常见的理由。
- **新契约字段 ship**（比如 spec 加了新的 `_notice` 类型）→ 把教学层补到 di-shared。
- **协议字段改名或删除** → 在同一个改契约的 MR 里同步 di-shared。

避免：

- 加服务专属指导 —— 那属于对应的服务 skill。
- 加只对一个服务有意义的示例 —— 同理。
- 按个人风格重写 —— 这份文件是给 AI agent 看的，不是给人优化阅读流畅度的。

## "Common AI failure modes" 的累积模式

`di-shared` 的长期价值不是协议总结 —— 那一次写完就完了。它的价值是**累积观察到的 AI 失败模式列表**。每次 agent 对 di-cli 犯一类**跨服务适用**的错误，修复就是这里加一条新 F-N。

每条的格式：

- **Symptom** —— agent 做了什么错（具体行为，不是模糊描述）。
- **Why it is wrong** —— 被违反的约束，用大白话说。
- **Correct behavior** —— agent 应该改做什么。
- **Spotting it in review** —— reviewer 在 transcript 里识别这种失败的着眼点。

贡献规则：**加，不替换**。这份列表是"AI agent 对 di-cli 会犯什么错"的机构记忆。一个新模型已经修好的旧失败仍然值得保留 —— 模型降级、回归、新人复现都会用到，条目本身就是"我们试过这条路"的文档。

F-001（看到 `exit 10` 自动加 `--yes` 重试）是已 seed 的样例。加 F-002 时照它的格式抄。

## 与其它文档的关系

这块涉及 4 份文档；下表把它们的角色讲清楚，方便你按问题挑对的文档。

| 文档 | 受众 | 回答什么 |
|------|------|---------|
| [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § 横切契约 | 项目维护者 | 契约**是什么**（规范）。 |
| [`docs/explainers/contracts-for-ai-agents.zh-CN.md`](contracts-for-ai-agents.zh-CN.md) | 学习项目的工程师 | 契约**为什么**这样设计。 |
| **本文档** | 子团队贡献者；任何问 "`di-shared` 是什么？" 的人 | `di-shared` 这个资产是什么、怎么和它相处。 |
| [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)（英文） | **AI agent** | 运行时怎么消费协议。 |

## 另见

- skill 本身：[`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)（英文）
- 契约设计原理：[`docs/explainers/contracts-for-ai-agents.zh-CN.md`](contracts-for-ai-agents.zh-CN.md)
- 规范定义：[`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § 横切契约
- 子团队接入流程：[`docs/explainers/onboarding-sub-team.zh-CN.md`](onboarding-sub-team.zh-CN.md)
- Skill 模板：[`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md)
