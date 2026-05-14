# Agents（代理）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Agent 是**带工具权限范围、职责聚焦的子代理**。和 skill（被加载到主对话中的知识）不同，agent 是一个**独立运行的实体**：自己的 system prompt、自己的上下文、受限的工具访问。

## 文件布局

每个 agent 就是一个 markdown 文件：`agents/<name>.md`。同一个文件同时被 Claude Code 和 Codex 使用——各自读自己认识的 frontmatter 字段，忽略其他字段。

| 工具 | 用户级路径 | 项目级路径 |
|------|------------|------------|
| Claude Code | `~/.claude/agents/` | `.claude/agents/` |
| Codex | `~/.codex/agents/` | `.codex/agents/` |

未来的 `di` 安装器会把 `agents/*.md` 同时 symlink 到两个目录。当前阶段，贡献者和用户可手动复制或 symlink。

## Frontmatter

```yaml
---
name: planner                       # 必需；kebab-case；等于不含 .md 的文件名
description: >                      # 必需；推荐使用触发关键词格式
  Read-only implementation planner.
  TRIGGER when: user asks for a step-by-step plan touching multiple files.
  DO NOT TRIGGER when: change is a typo or single-line fix.
tools:                              # 仅 Claude Code 读取 —— 限制可用工具
  - Read
  - Grep
  - Glob
model: opus                         # 仅 Claude Code 读取 —— opus | sonnet | haiku
readonly: true                      # 仅 Codex 读取 —— 限制写/执行权限
---
```

| 字段 | 必填 | Claude Code | Codex | 说明 |
|-------|------|-------------|-------|------|
| `name` | **是** | 是 | 是 | kebab-case，必须等于文件名（去 `.md`）。 |
| `description` | **是** | 是 | 是 | 决定自动委派；推荐用触发关键词格式。 |
| `tools` | 否 | **是** | 忽略 | 最小权限工具列表；省略则继承主代理。 |
| `model` | 否 | 是 | 忽略 | `opus` 用于推理，`sonnet`/`haiku` 用于吞吐。 |
| `readonly` | 否 | 忽略 | **是** | 推荐 `true`，除非该 agent 必须写文件。 |

`readonly: true` 缺失时 validator 会给出 warning——写权限必须是显式选择，而不是默认。

虽然 validator 不强制要求 agent 的 `description` 用触发关键词格式（这一点只对 skill 强制），但**强烈推荐**：AI 工具用 `description` 决定是否自动委派给该 agent，skill 那套 `TRIGGER when:` / `DO NOT TRIGGER when:` 结构对 agent 同样适用。

## Agent vs Skill

| | Agent | Skill |
|---|-------|-------|
| 文件 | `agents/<name>.md` | `skills/<name>/SKILL.md`（可选 `references/`、`scripts/`） |
| 加载方式 | 显式——用户 `@name` 或 AI 工具自动委派 | 自动——按 `description` 关键词匹配 |
| 工具访问 | 受 `tools` / `readonly` 限制 | 与主对话一致 |
| Token 成本 | 运行时独立上下文 | 加载时消耗主上下文 |
| 用途 | **能力** —— 结构化流程、审批逻辑 | **知识** —— API、查询模板、runbook |

一个直观的类比：skill 是"加载到脑子里的知识"，agent 是"可以呼叫的专家——他有自己的工位和门禁卡"。

## 设计原则

1. **最小权限**。默认 `readonly: true` + `tools: [Read, Grep, Glob]`。加 `Bash` 必须在 agent 正文写明理由；加 `Edit` / `Write` 仅限"职责本身就是改文件"的 agent。
2. **单一职责**。每个 agent 一件事。planner 只做计划，reviewer 只做评审。如果 description 变成"X 和 Y"，该拆。
3. **模型选择**。`opus` 用于推理重的规划/评审/设计；`sonnet`/`haiku` 用于延迟或成本敏感的高吞吐重复任务。
4. **不画饼**。不要引用 di-cli 当前**不存在**的命令或服务。如果 agent 依赖某个计划中能力，要明确标注 planned，并在缺失时优雅降级。

## 调用方式

```text
> Use the planner agent to plan adding a new skill.
> @planner Plan the rollout of convention X.
> @code-reviewer Review the changes on this branch.
```

当用户提示词与 `description` 匹配时，工具也可能自动委派。若想阻止自动委派，显式点名想用的 agent。

## 新建 agent

1. 在 `agents/<name>.md` 里写好上面那段 frontmatter。
2. 正文分三段：**Role**、**Process**、**Output format**。
3. 工具访问保持窄。每多一个非默认工具，在正文里写明为什么需要。
4. PR 前跑 `bash scripts/validate.sh`。

完整 review checklist 见 `CONTRIBUTING.md`。
