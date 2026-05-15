# Contexts（工作模式预设）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Context 是**工作模式预设**，在会话开始时注入，为本次会话设定 AI 的优先级、行为方式和安全默认值。

## Context vs Rule vs Skill

| | Context | Rule | Skill |
|---|---------|------|-------|
| **加载方式** | 手动——会话启动时通过 CLI 注入 | 自动——每次对话（安装后） | 自动——按任务描述匹配 |
| **范围** | 仅本次会话 | 每次会话 | 话题相关时 |
| **内容** | 工作模式：优先级、行为方式、安全策略 | 通用约定 | 领域知识、API、runbook |
| **适用场景** | "本次会话 AI 应该怎么想" | "始终要遵守的" | "AI 该了解的平台知识" |

Context 回答的是"我现在在做什么类型的工作"。Rule 和 skill 无论何种 context 下都保持激活。

## 可用 Context

| Context | 模式 | 适用场景 |
|---------|------|----------|
| `dev.md` | 开发模式 | 主动编码——先出可用代码，事后解释 |
| `review.md` | 代码评审 | PR review——关注质量、安全、约定合规 |
| `oncall.md` | On-call 排查 | 事故响应——跟随证据链，默认只读 |

## 使用方式

### Claude Code

会话开始时通过 `--system-prompt` 注入：

```bash
claude --system-prompt "$(cat ~/.claude/skills/di-cli/contexts/dev.md)"
```

在 `~/.zshrc` 或 `~/.bashrc` 里配好 alias，更方便：

```bash
DI_CONTEXTS="$HOME/.claude/skills/di-cli/contexts"   # 按实际安装路径调整

alias claude-dev='claude --system-prompt "$(cat $DI_CONTEXTS/dev.md)"'
alias claude-review='claude --system-prompt "$(cat $DI_CONTEXTS/review.md)"'
alias claude-oncall='claude --system-prompt "$(cat $DI_CONTEXTS/oncall.md)"'
```

启动会话：

```bash
claude-oncall     # on-call 排查模式
claude-dev        # 开发模式
claude-review     # 代码评审模式
```

### Codex

Codex 不支持在会话启动时动态注入 system prompt。可以手动把 context 内容粘贴到第一条消息里，或者写入你的工作区 system prompt 配置。

## 新建 Context

Context 是普通 markdown 文件，**不需要** YAML frontmatter。把它当 system prompt 写：直接、简洁、可操作。

结构模板：

```markdown
# Context: <模式名>

<一段话说明：这是什么模式，什么时候用。>

## Priorities
1. <最高优先级行为>
2. ...

## Approach
- <这个模式下如何行动>

## Safety
- <这个模式下需要特别注意或避免的>
```

控制在 ~100 行内。覆盖太多反而变成噪音。如果一个约定需要在每次会话里都生效，写 rule；如果只针对某个服务或领域，写 skill。
