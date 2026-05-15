# Contexts（工作模式预设）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

会话启动时注入的工作模式预设，为本次会话设定 AI 的优先级、行为方式和安全默认值。**当前为空占位**——暂未附 context 样例。

## 什么时候在这里贡献

什么时候该加 context：

- 某种工作模式（例如开发、代码评审、on-call 排查、research）需要**整段会话**保持一致 AI 行为，而不只是单个任务。
- 这种行为**无法**用 rule（始终生效）或 skill（按话题触发）表达——它专属于"我现在在什么模式"。
- 团队**真的会去用它**。没人用的 context 是纯负担。

## 编写格式

context 是**纯 markdown**——没有 frontmatter、没有 validator 必填字段。当 system prompt 写：直接、可操作、简洁。

推荐结构：

```markdown
# Context: <模式名>

<一段话说明：这是什么模式，什么时候用>

## Priorities
1. <最高优先级行为>
2. ...

## Approach
- <这个模式下如何行动>

## Safety
- <这个模式下需要特别注意或避免的>
```

每个 context 控制在 ~100 行内。再长 AI 会跳读。

## 用户怎么激活 context

context 不会自动安装，用户在会话启动时手动注入。

**Claude Code**：

```bash
claude --system-prompt "$(cat ~/.di/repos/di-cli/contexts/<mode>.md)"
```

配一个 shell alias 更方便。**Codex** 不支持运行时 system prompt 注入；把内容粘到第一条消息或工作区 prompt。

## Validator 行为

validator 不检查 contexts——无结构要求。

## 参考

- `CLAUDE.md` 里的 rule / context / skill 三者关系说明
