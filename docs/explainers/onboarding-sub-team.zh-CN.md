# 子团队接入 di-cli 指南

> **Language**: [English](onboarding-sub-team.md) | [中文](onboarding-sub-team.zh-CN.md)

本指南把一个 DI 子团队从「我们有个服务想给 AI agent 用」带到「我们的 skill 已合并、`di <service>` 命令面已上线」。开始前请先读：

- [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) — di-cli 是什么
- [`docs/explainers/contracts-for-ai-agents.zh-CN.md`](contracts-for-ai-agents.zh-CN.md) — 为什么 contracts 长这样
- [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md) — 每个 skill 共享的运行时协议（英文）

如果这些概念还不熟，先读完它们。本文是**流程层**，盖在它们之上。

## 子团队 vs di-cli 核心 各管什么

| 子团队负责 | di-cli 核心负责 |
|---|---|
| 服务 schema（端点、参数、scope、身份、风险等级、异步 handle 声明） | Schema → 命令编译器 |
| `skills/di-<service>-<purpose>/` —— SKILL.md 与 references | Skill validator、install/update/doctor 工具链 |
| 服务专属的 shortcut，在 `src/di/shortcuts/<service>/`（按需） | 三层命令架构、envelope 契约 |
| `docs/decisions/` 下的服务 ADR | 横切契约、退出码、`_notice`、风险等级 |
| 服务的 RAM scope 目录 | Credential provider chain 接口 |

这样划分是为了让子团队**只考虑自己的服务**。协议表面（envelope shape / error types / exit codes / `_notice` / `--yes` gate）由 di-cli 核心钉死，永远不会因服务而异。

## 6 步流程

### 1. 起一份服务 ADR

新建 `docs/decisions/NNNN-<service>.md`（取下一个序号）。它记录 spec 没规定的决策：

- 服务负责人和 on-call 升级渠道
- 身份模型：哪些 RAM role 或 scope 组适用、默认 `--as`、是否支持 `bot`
- 已知操作的风险等级：哪些 `read` / `write` / `high-risk-write` / `destructive-cost`
- 异步 handle 策略：哪些操作返回 handle、agent 怎么轮询
- 成本 / 配额（Group A 计算引擎尤其重要）
- Schema 真相源（API 定义住哪里、怎么刷新）

**写代码前先评审 ADR**。被这份 ADR 强行倒逼出的讨论本身就是价值。

### 2. 交付 schema

把 schema 文件放到 `<repo>/schemas/<service>.<format>`。v0.2 尚未敲定 schema 格式 —— 你的子团队作为第一个真实接入方，会跟 di-cli 核心一起定。候选：OpenAPI 3、轻量 YAML、服务自定义 descriptor。

Schema 是自动注册命令层（`di <service> <resource> <method>`）的真相源。每个方法必须声明：

- `risk`（`read` / `write` / `high-risk-write` / `destructive-cost`）
- `identity_required` 和支持的 `--as` 值
- `scopes`（RAM scope 名）
- 异步 handle 声明（如适用）

### 3. Fork skill 模板

按 [`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md) 走：

```bash
cp -r skills/di-skill-template skills/di-<service>-<purpose>
```

改 frontmatter、填光所有 SKILL.md 里的 `<replace-me>`、按每个 shortcut 一个文件的惯例在 `references/` 下补 workflow 文档。模板 README 里有合规 checklist —— 提交评审前过一遍。

### 4.（可选）写手工 shortcut

如果你的服务有多步流程值得让 agent 当成一个操作（典型例子是 feishu-cli 日历的 `+create` 串起 `+room-find` + `+freebusy` + `+suggestion`），在 `src/di/shortcuts/<service>/` 下用 Python 实现。约定：

- 每个 `+verb` 一个模块
- Shortcut 返回的 envelope shape 与 schema 命令完全一致（不允许特例）
- 注册时声明 risk
- 必须支持 dry-run（`--dry-run` 打印请求并返回）

如果操作本来就是单次调用，**不要**写 shortcut 包一层 schema 方法 —— 那只是表面上的"封装"，对 agent 没有任何附加值。

### 5.（可选）扩展凭据 provider chain

di-cli 默认 credential provider 走标准 Google OAuth（`--as user`）。如果你的服务有非常规鉴权模型（service account、sidecar daemon、vault 集成等），实现一个 `CredentialProvider` 并注册。这种情况很少 —— 大多数服务直接复用默认。

### 6. 测试、校验、上线

提 MR 前：

```bash
# 1. Skill 自检
di validate --scope skills

# 2. 仓库整体审计（你的 skill 必须让仓库保持 healthy）
di validate

# 3. 本地 install dry-run —— 确认 install 能捡到新 skill
di install --dry-run

# 4. Manifest 包含新命令（如果加了 Python shortcut）
di --manifest

# 5. Python 测试通过
uv run pytest -q
```

MR 内容：

- 标题：`feat(skills): add <service> skill and shortcuts`
- 描述：链到服务 ADR、总结身份/scope 决策、列出 ship 的 `+verbs`、列出已知限制
- 评审：1 名 di-cli 维护者 + 你的服务 owner

## 合并门禁

评审在批准前会确认：

- 服务 owner + on-call 渠道在 SKILL.md frontmatter 和 ADR 都写明
- 每个方法都声明了 risk（不允许 `unknown`）
- 写操作和破坏性操作走 `--yes` 确认门禁（exit 10 协议）
- 身份要求已记录、`--as` 示例与现实一致
- "Common AI failure modes" 至少一条，或显式注明"暂未观察到失败"
- 测试通过、`di validate` 返回 healthy
- Skill 遵守 di-shared 协议 —— 不重复也不矛盾 di-shared 内容

## 合并后的维护

Skill 是活文档。每次发现一类新的 agent 错误，就往 "Common AI failure modes" 加一条。长期价值就在这种积累 —— skill 变成"AI agent 在你服务上踩过哪些坑、怎么提前防"的机构记忆。

不要让 `skills/<name>/SKILL.md` 膨胀到 500 行以上。接近时，把专题指导拆到 `references/`，主 SKILL.md 留作入口索引。

## 拿不准时

- **协议问题**（envelope shape、退出码、`--yes` 语义）→ 回看 [`docs/explainers/contracts-for-ai-agents.zh-CN.md`](contracts-for-ai-agents.zh-CN.md)。如果协议真的覆盖不了你的场景，那是 di-cli 核心 ADR，不是子团队决策。
- **Skill 风格**问题 → 参考 [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)（英文）和已有的服务 skill。
- **"我该不该写 shortcut？"** → 先用慢路（schema 编译命令、让 agent 自己拼）。当同一个多步编排在真实 agent trace 里反复出现，再升级成 shortcut。

最快的子团队接入路径是：**小 skill、一个 shortcut、ADR 早评审**。上线前堆一堆 shortcut 的大 skill 往往在错的方向上深耕，要等真实 agent 用过才暴露问题。
