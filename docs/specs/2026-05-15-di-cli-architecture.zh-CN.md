# Spec: di-cli — 面向 AI Agent 的 DI 操作层

> **Language**: [English](2026-05-15-di-cli-architecture.md) | [中文](2026-05-15-di-cli-architecture.zh-CN.md)

Status: Accepted（spec-driven 工作流的 Phase 1 — Plan / Tasks / Implement 尚未完成）
Author: li.luo@shopee.com
Date: 2026-05-15

## 使命

di-cli 是 AI Agent 与 DI 开放平台 之间的**操作层**。它把这套**复杂、分散、权限敏感**的 API
包装成一套统一的命令体系，让机器能够**理解（Understand）、规划（Plan）、执行（Execute）
与纠错（Correct errors）**。

DI 开放平台在结构上分为两个不可融合的族：

- **Group A — 查询/计算引擎**：Spark、Flink、Presto、StarRocks、Kafka、ClickHouse、
  HBase、YARN、Livy。操作语义是作业 / 查询：提交 → 轮询 → 流式 → 取消。**长任务是常态**，
  不是高级特性。**算力成本是一等风险**。
- **Group B — 平台服务**：DataMap、DataService、Scheduler、DQC、SLA Manager、
  Diana、DataHub、RAM。操作语义是查询 / 注册 / 配置 / 审批。**权限治理与生命周期管理**
  主导一切，RAM 把守其它服务的入口。

这两族在命令形态、错误模型、时序语义上完全不同。di-cli **不假装它们是同一个 surface**。

## 主要消费者

AI Agent。每一条命令的输出、错误消息、退出码都会被机器解析以决定下一步动作。
DI 工程师是**次要使用者**，在直接阅读时退回到 `--format pretty`。

这条定位推导出唯一的硬规则：**一条命令在其失败路径不可被机器处理之前不算完工**。
"permission denied" 这种空错误是 bug —— 错误必须告诉 agent **缺哪个 scope/role、用哪条命令去申请**。

## 四个设计维度（AI 操作可供性）

整套架构围绕 AI 操作平台时需要什么来组织。下面所有的契约都回溯到这四条之一。

### 1. 理解（Understand）—— 不依赖外部文档发现能力

- `di --help`、`di <service> --help`、`di schema <service>.<resource>.<method>`
  暴露用途、参数、scope、风险等级、输出结构。
- `--manifest` 命令输出整个 CLI surface 的机器可读地图，供 agent 建立索引。
- 领域术语在 skill 文件里锚定，对歧义术语给出明确的判别规则
  （例如 Scheduler 的 "task" 与 DQC 的 "task" 含义不同）。

### 2. 规划（Plan）—— 可预测地串联命令

- 每条命令遵守同一套 envelope 与 exit-code 契约 —— agent 不需要按服务重新学习形状。
- 每条命令声明**前置条件**（例如 `events.patch` 声明 agent 必须先定位 `event_id`）。
- 异步操作返回**handle envelope**（见下），把"下一步是什么"写出来而不是让 agent 猜。

### 3. 执行（Execute）—— 可靠调用

- 默认 JSON 输出。`--format pretty` 仅服务于人类阅读，绝不是默认值。
- 退出码是确定性的，不被 shell 错误字符串包装。
- `--dry-run` 预览请求而不执行 —— 既检查正确性，也预览算力成本。
- `--yes` 是高风险操作（写入或算力消耗）的显式同意 token。

### 4. 纠错（Correct errors）—— 用结构化信号恢复

- 错误 envelope 的 `hint` 在适用时给出可运行的命令建议。
- 权限错误携带 `permission_violations`（缺失的 scope）、`console_url`（去哪里申请）、
  以及按身份分流的补救路径。
- 限流 / 可重试错误携带重试间隔元数据。
- 不可恢复的错误携带服务方指定的上报渠道。

## 横切契约（项目真正的产品 surface）

### 输出 envelope

成功（stdout）：

```json
{
  "ok": true,
  "identity": "<role>",
  "data": <object|array>,
  "meta": {"count": N, "rollback": "..."},
  "_notice": {"update": {...}, "skills": {...}, "deprecation": {...}}
}
```

错误（stderr）：

```json
{
  "ok": false,
  "identity": "<role>",
  "error": {
    "type": "validation|permission|auth|api|network|internal|cost_gate|confirmation_required|deadline",
    "code": <int>,
    "message": "...",
    "hint": "run `di ram request --scope X`",
    "console_url": "https://...",
    "permission_violations": ["scope:..."],
    "retry_after_ms": <int|null>,
    "detail": {...}
  }
}
```

### 退出码

| Code | 含义 |
|------|------|
| 0 | 成功 |
| 1 | API / 通用错误 |
| 2 | 参数校验错误 |
| 3 | 认证错误 |
| 4 | 网络错误 |
| 5 | 内部错误 |
| 6 | 成本门禁（消耗算力超过配置阈值） |
| 10 | 需要确认 —— 写入或高成本操作需要 `--yes` |
| 11 | 超时 / 截止时间到达 |

### 风险分级

每条命令在 schema 中声明 `risk`。AI 在调用前读取。

| 等级 | 含义 | 确认门禁 |
|------|------|----------|
| `read` | 无副作用 | 无 |
| `write` | 修改状态、可恢复 | 无 —— 但 agent 仍应向用户预告 |
| `high-risk-write` | 修改状态、难以或无法恢复 | 需要 `--yes`（exit 10） |
| `destructive-cost` | 触发超阈值的算力消耗 | 需要 `--yes`（exit 10）—— 阈值是策略，不是逐命令配置 |

### 身份模型

`--as <role>` 覆盖解析后的身份。**合法 role 的集合由 RAM 定义**，di-cli 核心不硬编码。
CLI 透传 credential provider 返回的 role 名。严格模式（per-profile lock）防止 CI
里意外的跨身份执行。

这意味着 v1 把 `--as` 作为透传 flag 来实现，不含硬编码的 role 枚举。

### Credential provider 接口

Protocol 风格的抽象接口。实现形成链：

```
env vars  →  内部 SSO extension  →  RAM token resolver  →  默认
```

每个 provider 返回 `Account` 与/或针对某个 `TokenSpec` 的 `Token`，或者发出
"跳过"（交给下一个）/"阻断"（终止链并附原因）。

这是 v1 唯一**必须冻结**的契约；默认实现可以是空 stub。

### 标准 flag（每条命令）

| Flag | 用途 |
|------|------|
| `--as <role>` | 身份覆盖（透传到 credential 层） |
| `--profile <name>` | 在已配置的 profile 之间切换 |
| `--format json\|pretty\|table\|ndjson\|csv` | 输出格式（默认：json） |
| `--dry-run` | 预览请求，不执行 |
| `--yes` | 确认 `high-risk-write` 或 `destructive-cost` 操作 |
| `--watch` | 按间隔重复命令（读端轮询） |
| `--follow` | 流式输出（长任务的日志、状态、结果） |
| `--timeout <duration>` | 客户端截止时间；超时退出码 11 |
| `--page-all`、`--page-limit`、`--page-size` | 分页控制 |

`--watch` 与 `--follow` 是一等公民，因为 Group A 的命令返回的是 **handle** 而非结果，
agent 必须能跟踪。

### Handle envelope（异步 / 长任务）

发起长任务的命令返回：

```json
{
  "ok": true,
  "identity": "<role>",
  "data": {
    "handle": {
      "kind": "spark.job",
      "id": "application_1735200000_0042",
      "status": "submitted",
      "actions": {
        "poll":   "di spark jobs status --id application_1735200000_0042",
        "follow": "di spark jobs status --id application_1735200000_0042 --follow",
        "logs":   "di spark jobs logs   --id application_1735200000_0042 --follow",
        "cancel": "di spark jobs cancel --id application_1735200000_0042"
      },
      "deadline": "2026-05-15T16:30:00Z"
    }
  }
}
```

AI 不需要推断下一步命令 —— 读 `actions` 即可。这把每一类异步操作的"现在干什么"
压缩成统一形态。

### `_notice` 通道

与请求本身无关的带外信号。AI 应**完成当前任务之后**再向用户呈现 notice。
通过环境变量可屏蔽（`DI_NO_UPDATE_NOTIFIER=1` 等）。类型：`update`、`skills`、
`deprecation`、`auth_expiring`。

## 命令架构（能力优雅降级）

三层命令，按 agent 的信心水平形成兜底层级 —— 不是面向三种用户：

```
di <service> +<verb>                精心策划的快捷命令 —— 智能默认值，多步编排
di <service> <resource> <method>    由服务 schema 编译得到 —— 与平台 API 1:1
di api <service> <METHOD> <path>    裸调兜底 —— 任意 endpoint，无策展
```

策划过的快捷命令服务于子团队选择投资的高频或多步工作流。编译得到的命令覆盖 schema
描述的一切。裸调 API 覆盖 schema 还没囊括的 endpoint。AI 优先用最高层，**被迫时**
才降级。

Group A（查询/计算）的快捷命令围绕 **submit → handle → poll/follow/cancel** 生命周期设计。
Group B（平台服务）的快捷命令围绕 **lookup → decide → mutate（用户授意）** 生命周期设计。

## Skills 作为教学层

Skills **不执行**任何 API 调用。它们教 AI：

- 何时调用本 CLI（触发关键词 + 禁止触发标记）
- 如何把领域意图映射到命令（术语对照、决策树）
- 常见失败模式与恢复方法（**Common AI Failure Modes** 章节 —— 持续累积）
- 何种操作是高风险、需要用户同意

目录结构：

```
skills/
├── di-shared/SKILL.md
│   认证、错误、_notice、退出码、handle、风险、--yes 协议 ——
│   其它 skill 都以 "先读这里" 开头
├── di-skill-template/
│   子团队 fork 的模板，含强制章节
└── di-<service>/
    ├── SKILL.md
    └── references/   多步编排文档，按需加载
```

**Common AI Failure Modes** 章节是强制项。它就是踩坑笔记 —— 项目对"agent 在哪里
把平台用错了"的累积经验。

## 子团队接入模式

DI 子团队把自己的服务接入 di-cli 的方式：

1. **服务 schema** —— endpoint、参数、scope、风险等级、身份要求、异步 handle 声明。
   格式在首个集成时选定（候选：OpenAPI 3、轻量 YAML）。
2. **SKILL.md + references/** —— 教学层。
3. **（可选）自定义快捷命令** —— 当 schema 表达不出多步编排时，用 Python 手写。
4. **（可选）Credential provider 扩展** —— 当服务认证不同于默认链时。
5. **服务 ADR** —— 负责人、安全边界、上报渠道。

di-cli 核心团队负责：schema 编译器、credential 链、输出/错误契约、di-shared、
skill template、validator、install/update/doctor。

子团队负责：schema 正确性、SKILL.md 质量、自定义快捷命令、服务特异的认证扩展。

## 项目结构

```
di-cli/
├── src/di/
│   ├── cli.py                 入口（argparse 根）
│   ├── contracts/             envelope、退出码、错误类型、handle、风险
│   ├── credential/            Provider Protocol + 链执行器
│   ├── runtime/               公共：分页、--watch、--follow、--timeout
│   ├── shortcuts/             每个服务的手写快捷命令（v1 为空）
│   ├── commands/              由服务 schema 编译得到的命令（v1 为空）
│   ├── api/                   裸调兜底
│   ├── core/                  install / update / doctor / version
│   ├── compiler/              schema → 命令注册
│   └── manifest/              surface 地图输出器
├── skills/
│   ├── di-shared/
│   └── di-skill-template/
├── docs/
│   ├── architecture.md
│   ├── decisions/             ADR
│   └── specs/                 功能/架构 spec（本文档在这里）
├── tests/
│   ├── contracts/             envelope / 退出码 / handle / 风险等级 的契约测试
│   ├── runtime/               --watch / --follow / 分页行为
│   └── conventions/           仓库形状校验
├── scripts/
├── CLAUDE.md
├── AGENTS.md → CLAUDE.md
├── README.md / README.zh-CN.md
├── pyproject.toml
└── .gitlab-ci.yml
```

## 技术栈

- 语言：Python ≥ 3.9
- CLI 框架：v1 用 stdlib `argparse`；快捷命令数超过 20 时再考虑 Typer
- 异步 / 长任务：stdlib `asyncio`；引擎本身支持时使用 SSE/WS
- 凭据存储：`keyring` 库（跨平台）
- v1 运行时依赖：stdlib + `PyYAML` + `keyring`

## 分发

分发通道是**打包关注点**，不是架构关注点。后续切换通道不会改变任何 CLI 代码。

**v1：** `uv tool install di-cli`（推荐）或 `pipx install di-cli`（等价）。两者都
从配置的 Python index 安装 wheel。uv 在用户缺少兼容 Python 时会顺带装上。

不构建单文件二进制、不写 Node.js 壳。如果后续真出现 "zero-prerequisite install"
的诉求再重新考虑。

## Commands

```
开发安装（editable）：  uv tool install --editable .   # 或: pipx install --editable .
测试：                  uv run pytest -q
Lint：                  uv run ruff check src tests
类型检查：              uv run mypy --strict src
仓库校验：              bash scripts/validate.sh
构建 wheel：            uv build
运行：                  di --help
```

## 代码风格

PEP 8，强制类型注解，`ruff format`，`mypy --strict`。值对象用冻结的 dataclass。
命令通过专用构造函数返回结构化 envelope —— **绝不**裸 raise。stdout 是数据，
stderr 是其它一切；混在一起会破坏管道。

## 测试策略

- **契约测试**（`tests/contracts/`）—— envelope schema、退出码映射、错误类型、
  handle 结构、风险等级强制。**最高优先级** —— 这是与 AI 的协议。
- **运行时测试**（`tests/runtime/`）—— `--watch`、`--follow`、分页、`--timeout`
  行为，用 mock 时钟 + mock 后端。
- **约定测试**（`tests/conventions/`）—— 仓库形状校验。
- **服务测试** —— 每个集成单独添加，默认走 dry-run；在线测试由环境变量门控、
  在 fork PR 上跳过。
- 覆盖率：`contracts/` 100%；`runtime/`、`core/` 80%+。

## 边界

### 必须做

- 每条命令输出 JSON envelope（错误也是）
- 每条命令在 schema 中声明 `risk` 与身份要求
- 任何异步操作必须返回 `handle` envelope
- 任何能给出补救路径的错误都要带 `hint`
- 测试 envelope / 退出码 / handle / 风险等级 契约（这是 AI 协议）

### 先征求许可

- 添加运行时依赖
- 接入第一个真实服务
- 实现 OAuth / token 存储
- 改动 envelope、退出码、handle schema（这是契约变更！）
- 单次改动超过 3 个文件

### 绝对不做

- 提交 secret、token、refresh token
- 静默绕过 `--yes`（exit 10）协议
- 让 skill 执行 API 调用 —— skill 只教学，不运行
- 引入 `di` 之外的命令命名空间
- 把服务业务逻辑写进 skill
- 把 `--format pretty` 设为默认（人类不是主要消费者）

## 成功标准（sign-off 条件 — 全部已满足）

- [x] 使命与两族能力面（Group A / Group B）
- [x] AI 是主要消费者的定位及其推论
- [x] 四个设计维度作为组织原则
- [x] 横切契约（envelope / exit / risk / handle / `_notice`）作为冻结的协议面，
      v1 即使没有真实服务也要实现
- [x] 身份模型推迟到 RAM 定义（核心不硬编码 role 枚举）
- [x] 子团队接入模式：schema + SKILL.md + 可选的 shortcuts/auth/ADR
- [x] v1 范围：契约 + 结构 + di-shared skill + install/update/doctor，
      零真实服务

## 待解问题（有意推迟）

1. **RAM 身份模型** —— role 分类法到底是什么？在首个使用 RAM 的集成（即任何真实
   集成）时定。这条几乎会自我回答。
2. **Schema 格式** —— OpenAPI 3 / 轻量 YAML / 自定义。在首个子团队接入时与对方一起决定。
3. **逐引擎的异步协议** —— Spark（REST + ApplicationId）、Flink（Job REST API）、
   Presto（query_id）、Livy（session）、Kafka（consumer/topic）—— 每个都有自己的
   状态机。`handle` envelope 统一了 agent 视角，但底层的轮询机制因引擎而异。
   Group A 接入开始之前需要一份调研文档。
4. **成本门禁阈值** —— `destructive-cost` 高于多少触发？这是策略问题、不是代码问题。
   很可能按引擎、按 profile 分别配置。
5. **Claude Code + Codex 之外的工具支持** —— Cursor / Trae / Gemini 等推迟到
   Claude+Codex 的使用稳固之后。
6. **MCP 层** —— 一个服务什么时候从 CLI 命令面升级为一等的 MCP server？这个问题
   变具体时再开专门的 ADR。
