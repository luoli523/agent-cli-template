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

Rule **不会自动安装**，需要用户手动 opt-in。下面是两种安装方式，二选一。

下面片段里的 `/path/to/di-cli` 请替换为实际克隆路径（未来 `di` CLI 安装时默认是 `~/.sra/repos/di-cli`，或你自己的克隆位置）。

### 方式 A：显式 symlink（推荐）

只 link **具名文件**，不要 link 整个目录：

```bash
# Claude Code（用户级别）
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.claude/rules/git-workflow.md
```

**反例**：

```bash
# 错误 —— 会把 README.md 也 link 进去，污染每次对话
ln -sf /path/to/di-cli/rules/*  ~/.claude/rules/
```

`~/.claude/rules/` 是 Claude Code 自动扫描的目录，丢进去的任何 `.md` 文件都会被每次会话加载。本仓库里的 README 是约定文档、不是 rule，不要让它们进 `~/.claude/rules/`。

项目级安装（只在某个仓库内生效）：

```bash
mkdir -p .claude/rules
cp /path/to/di-cli/rules/git-workflow.md .claude/rules/
```

### 方式 B：在 CLAUDE.md 里 `@import`（仅 Claude Code）

编辑 `~/.claude/CLAUDE.md`（不存在则新建），加一行：

```markdown
@~/.di/repos/di-cli/rules/git-workflow.md
```

Claude Code 会解析并加载被 import 的文件（最多 5 跳递归）。首次 import 时 Claude Code 会弹批准对话框，同意即可。相比 symlink 的好处：import **显式可见**——打开 CLAUDE.md 就能看到引了哪些外部文件；仓库被删时会报清晰错误，而不是留下静默失效的 symlink。

### Codex（用户级别）

Codex 只读一个指令文件——`~/.codex/AGENTS.md`——**不会**扫描 `rules/` 子目录，也**不支持** `@import`。（`~/.codex/rules/` 是 Codex 的 execpolicy/沙箱目录，完全不同的子系统，不要把 rule 文件放进去。）

要在 Codex 下使用 di-cli 的 rule，选择以下之一：

**Codex 方式 1 —— 把 rule 内容追加**到 `~/.codex/AGENTS.md`：

```bash
cat /path/to/di-cli/rules/git-workflow.md >> ~/.codex/AGENTS.md
```

代价：上游 rule 更新不会自动同步；rule 更新后需重跑。

**Codex 方式 2 —— symlink `AGENTS.md`**，仅在你 Codex 没有其它指令文件时使用：

```bash
ln -sf /path/to/di-cli/rules/git-workflow.md ~/.codex/AGENTS.md
```

代价：这会成为 Codex 的唯一指令文件；多个来源要么手工合并，要么用方式 1。

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
