# Agents（代理）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

带权限边界的子代理，由用户显式调用或 AI 工具自动委派。**当前为空占位**——跨工具格式问题未定，暂不附 sample（详见 [`docs/architecture.md`](../docs/architecture.md) § agents/）。

## 什么时候在这里贡献

什么时候该加 agent：

- 某个聚焦、可复用的任务需要一个**独立 system prompt + 限定工具**的子代理。
- agent 在 DI 工作流中有**真实消费者**。不要为了"演示格式"加 demo——有用户才写。
- 单一职责。一个 agent 一件事。若 description 变成"X 且 Y"，应拆分。

## 编写格式

| 工具 | 文件格式 | 扫描路径（用户级） |
|------|---------|------------------|
| Claude Code | Markdown + YAML frontmatter | `~/.claude/agents/<name>.md` |
| Codex       | TOML | `~/.codex/agents/<name>.toml` |

**Claude Code** frontmatter 必填字段：`name`（kebab-case，等于文件名 stem）、`description`（推荐触发关键词格式）。可选：`tools`（字符串列表）、`model`（`opus` / `sonnet` / `haiku`）、`readonly`（布尔，推荐 `true`）。

**Codex** TOML 必填字段：`name`、`description`、`developer_instructions`（多行字符串）。参见 <https://developers.openai.com/codex/subagents>。

跨工具支持当前需要同时提供 `.md` 和 `.toml` 两份文件。生成器尚未提供。

## Validator 行为

`scripts/validate_repo.py` 校验 Markdown agent 的 frontmatter（name 与文件名一致、description 存在、tools / readonly / model 类型）。TOML agent 文件当前不做 schema 校验。

## 参考

- `CLAUDE.md` § Agent Standards
- `CONTRIBUTING.md` § Agents
