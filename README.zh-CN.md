# di-cli

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

DI 团队内部 CLI —— 为 Data Infra 工程师与 AI agent 提供面向 DI 开放平台的统一操作层。

**状态：v0.2 ready** —— 协议表面、基础命令、skill 模板、CI 全部就位。真实服务接入会在 v0.2 之后逐步引入。

---

## 是什么

DI 开放平台分两个结构不同的族：

- **Group A —— 查询 / 计算引擎**：Spark、Flink、Presto、StarRocks、Kafka、ClickHouse、HBase、YARN、Livy。生命周期典型是 `submit → poll → logs → cancel`。长任务是常态。
- **Group B —— 平台服务**：DataMap、DataService、Scheduler、DQC、SLA Manager、Diana、DataHub、RAM。生命周期是 `lookup → decide → mutate → recover`。权限敏感，RAM 守门。

AI agent 目前无法可靠操作这个面。di-cli 是把它包装统一的 CLI。完整架构（三层命令模型、冻结的协议面、子团队贡献模型）见 [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md)。

**主要消费者**：AI agent。每条命令的输出、错误消息、退出码都被机器解析。DI 工程师是次要使用者，直接阅读时退回到 `--format pretty`。

---

## v0.2 ship 了什么

v0.2 表面是**面向 agent 的协议 + 工具链**，不是服务接入。下表所有内容都已在 `main` 上，每个 MR 都被 CI 演练过。

| 层 | 提供 |
|----|------|
| 横切协议面 | Envelope、退出码、错误类型、handle、风险等级、`_notice` 通道 |
| 基础命令 | `di install` / `update` / `doctor` / `validate` / `version` |
| Skill validator（`di validate`） | 校验 SKILL.md frontmatter、正文形态、仓库约定 |
| `di-shared` skill | 每个未来 skill 共享的运行时协议 |
| `di-skill-template` | 子团队 skill 的合规 fork 起点 |
| CI 流水线 | `lint` + `typecheck` + `test` + `validate` × Python 3.9, 3.13 |
| 双语文档 | spec / decisions / explainers / reference，EN + 中文 |

## v0.2 **没**有什么

明确写出来，省得子团队浪费时间找：

| 能力 | 状态 |
|------|------|
| 真实服务接入（DataMap、Scheduler 等） | v0.2 之后 —— 第一个子团队 co-design schema 格式。 |
| `di auth login` / Google OAuth | v0.2 之后 —— 写代码前需要先 ADR 评审。 |
| MCP server 模式 | 推迟 —— 需要按 [`CLAUDE.md`](CLAUDE.md) § MCP 走 ADR 评审。 |
| `_notice.update` 版本检查器 | 推迟 —— 等 PyPI / 内部 index 策略定下来。 |
| PyPI / 内部 index 发布 | 跟 v0.2 之后的 release 工具一起。 |
| Cursor / Trae / Gemini 支持 | 暂不在范围内，等 Claude Code + Codex 用稳后再说。 |

---

## 仓库布局

```text
di-cli/
├── src/di/
│   ├── contracts/         Envelope、退出码、错误类型、handle、风险、_notice
│   ├── core/              基础命令（install/update/doctor/validate/version）
│   ├── runtime/           标准 flag、output 层、Check 原语
│   ├── manifest/          --manifest 表面 emitter
│   ├── validators/        SKILL.md frontmatter、skill 形状、仓库形状校验
│   ├── shortcuts/         （v0.2 之后）每个服务手写的 shortcut
│   ├── commands/          （v0.2 之后）schema 编译出的命令
│   ├── compiler/          （v0.2 之后）schema → 命令注册
│   └── api/               （v0.2 之后）裸 API 出口
├── skills/
│   ├── di-shared/         每个 di-* skill 共享的运行时协议
│   └── di-skill-template/ fork 起点（`di install` 不会装它）
├── docs/
│   ├── specs/             架构 spec（规范）
│   ├── decisions/         ADR
│   ├── explainers/        教学文档 —— "协议为什么是这样"
│   └── reference/         查询表 —— "ship 了哪些命令、做什么"
├── tests/                 contracts / runtime / core / validators
├── .gitlab-ci.yml         CI: lint + typecheck + test + validate
├── CLAUDE.md              AI 助手项目说明
├── AGENTS.md              软链 → CLAUDE.md（Codex 和 Claude 共用一份）
└── pyproject.toml
```

---

## 已有命令（v0.2）

五条基础命令。操作的是本地机器或 di-cli 自身，**还没有任何一条触达 DI 服务**。

| 命令 | 做什么 | 风险 |
|------|--------|------|
| `di version` | 显示 CLI 版本、Python 解释器、宿主平台 | read |
| `di install [--target ...]` | 把 `skills/di-*/` symlink 到 `~/.claude/skills` 和 `~/.codex/skills` | write |
| `di update [--target ...]` | re-sync skills + 删孤儿 | write |
| `di doctor [--target ...]` | 健康检查 —— source / target dirs / 同步漂移 | read |
| `di validate [--scope ...]` | 仓库 + skill 约定审计（CI 门禁） | read |

完整的命令行为、envelope 形态、示例 → [**命令参考**](docs/reference/commands.zh-CN.md)。机器可读表面 → `di --manifest`。

---

## 按角色从哪开始

### 🔧 子团队服务负责人 —— "我怎么把服务接入给 AI agent？"

1. [`docs/explainers/onboarding-sub-team.zh-CN.md`](docs/explainers/onboarding-sub-team.zh-CN.md) —— 6 步流程（先读这个）。
2. [`docs/explainers/the-di-shared-skill.zh-CN.md`](docs/explainers/the-di-shared-skill.zh-CN.md) —— 你的 skill 必须 defer 给什么。
3. [`docs/explainers/contracts-for-ai-agents.zh-CN.md`](docs/explainers/contracts-for-ai-agents.zh-CN.md) —— 协议为什么这样设计。
4. [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md)（英文）—— 浏览即可；这是 agent 运行时真正读的东西。
5. [`skills/di-skill-template/README.md`](skills/di-skill-template/README.md) —— fork 开始干。

### 🤖 AI agent 作者 / di-cli 运行时用户

1. [`docs/explainers/contracts-for-ai-agents.zh-CN.md`](docs/explainers/contracts-for-ai-agents.zh-CN.md) —— 你的 agent 要消费的协议。
2. [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md)（英文）—— 权威的运行时指令。
3. [`docs/reference/commands.zh-CN.md`](docs/reference/commands.zh-CN.md) —— 命令目录。
4. `di --manifest` —— 运行时机器可读表面。

### 🛠 di-cli 核心维护者

1. [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md) —— 规范定义。
2. [`docs/decisions/`](docs/decisions/) —— ADR（重点是 [`0002-architecture-reset.md`](docs/decisions/0002-architecture-reset.md)）。
3. [`CLAUDE.md`](CLAUDE.md) —— 项目边界、工作规则。
4. `src/di/contracts/` —— 冻结的协议表面。
5. `tests/contracts/` —— 守护协议的契约测试。

### 🧪 想本地试一下

```bash
git clone <this-repo> && cd di-cli-internal
uv tool install --editable .
di --manifest
di doctor
```

如果你没装 Claude Code 或 Codex，`di doctor` 会把 `target_dirs` 标成 `warn` —— 这是正常的。

---

## 本地开发

跟 CI 跑的命令一致（见 [`.gitlab-ci.yml`](.gitlab-ci.yml)）：

```bash
uv sync --frozen --extra dev
uv run ruff check src tests
uv run mypy --strict src
uv run pytest -q
uv run di validate
```

仓库约定、工作规则、项目边界见 [`CLAUDE.md`](CLAUDE.md)。

---

## 文档地图

| 受众 | 文档 |
|------|------|
| 项目维护者 | [Architecture spec](docs/specs/2026-05-15-di-cli-architecture.md) · [架构 spec](docs/specs/2026-05-15-di-cli-architecture.zh-CN.md) |
| 项目维护者 | [`docs/decisions/`](docs/decisions/) —— ADR |
| 学习项目的工程师 | [Contracts: why this protocol shape](docs/explainers/contracts-for-ai-agents.md) · [中文](docs/explainers/contracts-for-ai-agents.zh-CN.md) |
| 子团队贡献者 | [Onboarding a sub-team](docs/explainers/onboarding-sub-team.md) · [中文](docs/explainers/onboarding-sub-team.zh-CN.md) |
| 子团队贡献者 | [The di-shared skill explained](docs/explainers/the-di-shared-skill.md) · [中文](docs/explainers/the-di-shared-skill.zh-CN.md) |
| 运行时 AI agent | [`skills/di-shared/SKILL.md`](skills/di-shared/SKILL.md)（英文） |
| 子团队贡献者 | [`skills/di-skill-template/README.md`](skills/di-skill-template/README.md) —— fork 起点 |
| 任何要查命令的人 | [Command reference](docs/reference/commands.md) · [中文](docs/reference/commands.zh-CN.md) |
| AI 助手（Claude Code / Codex） | [`CLAUDE.md`](CLAUDE.md) —— 工作规则、边界 |

---

## 项目边界

di-cli ship 出一个**冻结的协议表面**（envelope、退出码、handle 结构、风险等级）。这些的改动需要显式批准 + ADR。完整的 "always do / ask first / never do" 列表见 [`CLAUDE.md`](CLAUDE.md) § Project Boundaries。

---

## 下一步

v0.2 之后的工作是**服务驱动**：

- **第一个真实服务 skill** —— 挑一个高痛点工作流（DataMap 血缘查询、Scheduler 任务调试是可能候选），完整走一遍接入流程，端到端验证设计。
- **`di auth login`** —— Google OAuth device flow + keyring 存储。当第一个需要身份的服务准备好时上线。
- **Schema 编译器** —— 跟第一个子团队 co-design schema 格式，然后 ship `src/di/compiler/` 和 `src/di/commands/`。
- **PyPI / 内部 index 发布** —— 这样 `pipx install di-cli` 不需要 `--editable` 也能跑。

通过 v0.2.0 tag 和后续 release tag 跟踪进展。
