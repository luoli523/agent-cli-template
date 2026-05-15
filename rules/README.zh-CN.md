# Rules（规则）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Rule 是**始终加载的约定**——用户手动安装后，每次 AI 助手会话都会自动注入，无论当前任务是什么。和 skill（按需匹配触发）不同，rule 是持续存在的。

## Rule vs Skill vs Context

| | Rule | Skill | Context |
|---|------|-------|---------|
| **加载方式** | 每次对话（手动安装后自动） | 按需——根据任务描述匹配 | 会话开始——通过 CLI 注入 |
| **范围** | 通用约定 | 某个领域的专项知识 | 本次会话的工作模式 |
| **内容** | 简短的"始终做 / 禁止做"规范 | 服务 API、查询模板、runbook | 开发 / 评审 / oncall 等模式的行为优先级 |
| **适用场景** | commit 格式、分支命名、安全不变量 | 面向特定服务的工作流 | 为整个会话设定 AI 的行为模式 |

当某个约定**短小、通用、需要在每次对话中都生效**——而不只是偶尔涉及某个话题时——才写 rule。

如果某个约定很长、只针对特定服务、或者偶尔才用到，放进 skill 更合适。

## 安装方式

Rule **不会自动安装**，需要用户手动 symlink 或复制到 AI 工具的规则目录：

```bash
# Claude Code（用户级别）
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.claude/rules/git-workflow.md

# Codex（用户级别）
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.codex/rules/git-workflow.md
```

将 `/path/to/di-cli` 替换为实际克隆路径（未来 `di` CLI 安装时默认是 `~/.sra/repos/di-cli`，或你自己的克隆位置）。

项目级安装（只在某个仓库内生效）：

```bash
# Claude Code 项目级
mkdir -p .claude/rules
cp /path/to/di-cli/rules/git-workflow.md .claude/rules/
```

## 已有规则

| 规则 | 说明 |
|------|------|
| `git-workflow.md` | di-cli 贡献者的 commit 格式、分支命名和 MR checklist。 |

## 新建 Rule

好的 rule 需满足：

- **简短** —— 一到两屏内。更长的内容放 skill 或 doc。
- **通用** —— 适用于所有 di-cli 工作，不只针对某个服务或场景。
- **可操作** —— 明确告诉 AI 该做什么或不做什么，不是模糊原则。
- **不重复** —— 不重复 `CLAUDE.md` 里已有的内容。

模板：

```markdown
# Rule: <名字>

<一段说明目的>

## Always
- <具体行动>

## Never
- <具体禁止>

## Examples
<如有帮助，写简短的前后对比>
```

提 PR 前先问自己："每个 di-cli 贡献者在每次对话里都需要这条约定吗？"如果答案是"只有时候需要"，改写成 skill。
