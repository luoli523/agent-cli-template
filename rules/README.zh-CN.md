# Rules（规则）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

始终加载的约定——用户手动 opt-in 后，每次 AI 对话都自动注入。**当前为空占位**——暂未附 rule。

## 什么时候在这里贡献

什么时候该加 rule：

- 某个约定**短小、通用、需要在每次对话中都生效**——而不只是某个话题相关时。
- 这条 rule 与 `CLAUDE.md`（Claude Code 已经始终加载）**不重复**。
- 每个 DI 贡献者在每次对话里都需要它。如果只是"有时候用"或"只针对某个服务"，写 skill 更合适。

好的 rule 控制在一到两屏。再长该是 skill 或 doc。

## 编写格式

rule 是一个 markdown 文件：`rules/<name>.md`。不需要 YAML frontmatter。

推荐结构：

```markdown
# Rule: <名字>

<一段说明目的>

## Always
- <具体行动>

## Never
- <具体禁止>
```

每条 rule 控制在 ~50 行内。

## 用户怎么安装 rule

rule **不会自动安装**，用户手动 opt-in。**Claude Code** 两种方式：

```bash
# 方式 A —— 显式 symlink（只 link 具名文件，不要 link 整个目录）
ln -sf /path/to/di-cli/rules/<name>.md ~/.claude/rules/<name>.md

# 方式 B —— 在 ~/.claude/CLAUDE.md 里 @import（更显式）
echo "@/path/to/di-cli/rules/<name>.md" >> ~/.claude/CLAUDE.md
```

`~/.claude/rules/` 是 Claude Code 自动扫描的目录。**不要**通配 link 整个目录（`ln -sf rules/* ~/.claude/rules/`）——那样 `README.md` 也会被当 rule 加载。

**Codex** 只读 `~/.codex/AGENTS.md` 一个文件，不扫描 rules 子目录、也不支持 `@import`。要在 Codex 用 di-cli rule，把内容**追加**到 `~/.codex/AGENTS.md`。`~/.codex/rules/` 是 Codex 的 execpolicy 目录，**不要**把 rule 放进去。

## Validator 行为

validator 不检查 rules——无结构要求。

## 参考

- `CLAUDE.md` 中关于 rule / context / skill 三者关系的说明
