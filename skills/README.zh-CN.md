# Skills（技能）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Skill 是**按需加载的知识模块**：当用户的任务匹配某条 skill 的 `description` 时，AI 助手会把该 skill 加载到当前会话。每个 skill 是一个目录，目录内含一个带 YAML frontmatter 的 `SKILL.md` 文件和 markdown 正文。

## 目录布局

```text
skills/
  datamap-lineage/
    SKILL.md              # 必需 —— skill 定义
    references/           # 可选 —— 长篇文档、Schema
    scripts/              # 可选 —— 辅助脚本（uv run / bash）
  scheduler-task-debug/
    SKILL.md
  ...
```

### 必须扁平

所有 skill 目录必须直接挂在 `skills/` 下。**不允许嵌套**（例如 `skills/platform/datamap-lineage/`），validator 会拒。原因：

1. AI 工具只扫第一层目录，嵌套目录会被静默忽略。
2. 未来的安装器假设 `skills/<name>/` 与 `~/.agents/skills/<name>` 一一对应的 symlink 关系。
3. 扁平布局让 skill 发现、命名冲突、ownership review 都很简单。

## SKILL.md 格式

每个 `SKILL.md` 都以 YAML frontmatter 开头，正文是 markdown。

### 必填字段

```yaml
---
name: datamap-lineage
maintainer:
  - owner@shopee.com
description: >
  DataMap lineage (DataMap 血缘) — query table metadata, lineage, owners, and governance hints.
  TRIGGER when: user asks about "DataMap", "lineage", "血缘", "table owner", "schema", or "metadata".
  DO NOT TRIGGER when: the task is general SQL writing without metadata lookup.
---
```

| 字段 | 规则 |
|-------|------|
| `name` | kebab-case，必须等于所在目录名。 |
| `maintainer` | 非空的邮箱或团队 alias 数组。也接受单个字符串，但优先使用数组形式。 |
| `description` | 必须使用下文的"三段式触发关键词"格式，YAML 折叠后长度 **≤ 1024 字符**。 |

### 触发关键词描述

`description` 是 AI 工具匹配任务到 skill 的**主要依据**。写得不好，skill 该触发的时候不触发，不该触发的时候被错误触发。

必须包含三段，顺序固定：

```text
<这个 skill 是做什么的 —— 一句话，含中英双语专有名词>。
TRIGGER when: <具体的关键词与场景，中英文都列>。
DO NOT TRIGGER when: <常见的误触发场景>。
```

要点：

- 多行 description 用 YAML 折叠块标量（`>`）。
- 关键词加引号——`"DataMap"`、`"血缘"`——让触发词更醒目。
- validator 会把缺少 `TRIGGER when:` 或 `DO NOT TRIGGER when:` 视为错误。

### 可选字段（与 sra-toolkit 兼容的参考形态）

validator 不强制要求，但下游工具常用，按需添加：

```yaml
category: platform           # 高层分组（platform | data | qa | ...）
tags: [datamap, lineage]     # 自由 tag，便于搜索与统计
cli: scripts/datamap.py      # skill 内部的命令入口（如有）
credentials:                 # 该 skill 期望在 ~/.config/di/credentials.json 里出现的凭证
  - name: datamap.token
    description: "Bearer token for DataMap API"
```

若声明了 `credentials`，未来的安装器会在 `config/credentials.template.json` 里查找对应条目并提示用户填写。

### 正文规范

- 正文控制在 ~500 行内。详细参考资料放 `references/`，辅助脚本放 `scripts/`。
- **禁止绝对路径**（skill 会被安装器 symlink 到不同位置）。
- 主体语言英文；专有名词加括号注中文：`Feature Store Engine (特征存储引擎)`。

## 命名约定

名字必须 **kebab-case** 且**面向服务**。推荐形态：

```text
<prefix>-<domain>[-<object>][-<action>]
```

示例：`datamap-lineage`、`scheduler-task-debug`、`dqc-rule-check`、`ram-permission-debug`。

### 前缀

前缀单一来源是 [`config/prefixes.json`](../config/prefixes.json)。骨架阶段已声明的前缀：

| 范围 | 前缀 | Owner |
|-------|------|------|
| 部门级 | `di-` | Data Infra |

`config/prefixes.json` 的 `policy.enforce` 字段控制校验级别：

- `"warn"`（当前默认）——未知前缀仅是 validator 的 warning，不阻塞。
- `"error"`——未知前缀直接失败。等前缀分类稳定后再切换。

新增前缀请先在 `docs/decisions/` 写一份提案，**不要**直接动 `config/prefixes.json`。

## 已有 Skill

| Skill | 用途 |
|-------|------|
| [`di-mr-flow`](di-mr-flow/SKILL.md) | 分支 → commit → push → GitLab MR → CI → squash 合入 → 清理。触发词："open MR"、"提 MR"、"merge this"。 |

## 校验

```bash
bash scripts/validate.sh
```

skill 相关检查包括：

- `name` 与目录名一致。
- `maintainer` 存在且非空。
- `description` 含 `TRIGGER when:` 与 `DO NOT TRIGGER when:`。
- 不存在嵌套的 skill-like 目录。
- 前缀出现在 `config/prefixes.json` 中（按 `policy.enforce` 处理）。

PR 提交前请按 `CONTRIBUTING.md` 走完完整 checklist。
