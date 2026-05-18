# di-cli 命令参考

> **Language**: [English](commands.md) | [中文](commands.zh-CN.md)

di-cli ship 出的所有命令的总目录。v0.2 只 ship "Infrastructure commands" 一节列出的五条基础命令；"Service commands" 一节是给未来子团队贡献的占位结构。

需要**机器可解析**的命令清单时优先用 `di --manifest`。本页是它的人类版伴侣 —— 多了"什么时候用 / 该期待什么"这种 manifest 装不下的上下文。

## 运行时怎么发现命令

| 工具 | 适用场景 |
|------|---------|
| `di --manifest` | AI agent 要结构化的命令面地图（JSON envelope）。 |
| `di --help` | 人类要顶层概览 + 标准 flag 一览。 |
| `di <command> --help` | 人或 agent 要某条命令的 flag / 参数。 |

## 三层命令架构

子团队服务接入时，能力会出现在以下三层中的一层或多层（完整原理见 [`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § 命令架构）：

| 层 | 形态 | 何时用 |
|----|------|--------|
| **Shortcut** | `di <service> +<verb>` | 高层、agent 友好的封装；带智能默认；有就优先用。 |
| **Schema-compiled** | `di <service> <resource> <method>` | 与服务 API 1:1；参数完全可控。 |
| **Raw API** | `di api <service> <METHOD> <path>` | 兜底；envelope 规则一致。 |

Agent 优先用能匹配任务的最高层；子团队按操作类型决定铺哪几层。

## 标准 flag

每条命令都接受下列横切 flag（定义见 [`src/di/runtime/flags.py`](../../src/di/runtime/flags.py)）。v0.2 里不是每个 flag 都有运行时行为 —— 保留占位是为了 agent 不必在异步 / 分页操作上线时重新学一遍 flag 集。

| Flag | 取值 | v0.2 状态 |
|------|------|----------|
| `--format` | `json`（默认）、`pretty`、`table`、`ndjson`、`csv` | `json` / `pretty` 已实现；其余 fallback 紧凑 JSON。 |
| `--dry-run` | bool | `install` / `update` / 未来写操作已实现。 |
| `--yes` | bool | 已接线；v0.2 没有 `high-risk-write` 级命令。 |
| `--as` | `<role>` | 接受；v0.2 命令不解析身份（暂无真实服务）。 |
| `--profile` | `<name>` | 多 profile 配置占位。 |
| `--watch` | bool | 读侧轮询占位。 |
| `--follow` | bool | 流式长任务占位。 |
| `--timeout` | `<duration>` | 占位；未来超时强制返回 exit 11。 |
| `--page-all` | bool | 自动翻页占位。 |
| `--page-size` | `<N>` | 占位。 |
| `--page-limit` | `<N>` | 占位。 |

惯例：flag 写在子命令**后面**（`di version --format pretty`）。反向只对顶层 flag 有效（`--manifest`、`--version`）。

---

## 基础命令（v0.2）

按生命周期顺序排：典型用户遇到它们的顺序。这五条都操作本地机器或 di-cli 自身，**还没有任何一条触达 DI 服务**。

### `di version`

**Synopsis** — `di version [--format json|pretty]`

**Purpose** — 显示 CLI 版本、Python 解释器版本、宿主平台。

**Risk** read · **Identity required** no · **Source** [`src/di/core/version.py`](../../src/di/core/version.py)

**Behaviors**
- 纯读；无副作用。
- 编译安装后始终 exit 0。

**Data shape**

```json
{
  "ok": true,
  "identity": "local",
  "data": {
    "version": "0.2.0",
    "python": "3.13.5",
    "platform": "darwin"
  }
}
```

**See also** — `di --manifest` 看注册过的命令目录（含 `version` 自身）。

---

### `di install`

**Synopsis** — `di install [--target claude|codex|all] [--dry-run] [--format json|pretty]`

**Purpose** — 把 `<repo>/skills/di-*/` symlink 到 `~/.claude/skills/<name>` 和 `~/.codex/skills/<name>`，让 ship 出的 skill 在 AI 工具目录里出现。

**Risk** write · **Identity required** no · **Source** [`src/di/core/install.py`](../../src/di/core/install.py)

**Behaviors**
- **零状态所有权模型**：目标条目"归 di 管"当且仅当它是 symlink 且解析后落在源 `skills/` 树内。真实目录、普通文件、外来 symlink 一律不动。
- **原子冲突策略**：发现任何冲突（真实目录、外来 symlink）整次 abort，exit 2 + 结构化 error envelope。没有"部分成功"模式。
- **幂等**：状态匹配时再次运行是 no-op。
- **排除 `di-skill-template`**：模板是 fork 起点，永远不装。

**Source 解析**：`DI_SKILLS_DIR` 环境变量 > 从 `di.__file__` 往上找含 `pyproject.toml` 与 `skills/` 的目录。

**Data shape（成功）**

```json
{
  "ok": true,
  "identity": "local",
  "data": {
    "source": "/path/to/repo/skills",
    "targets": {"claude": "/Users/.../.claude/skills", "codex": "..."},
    "installed": [{"name": "di-shared", "target": "claude", "path": "..."}],
    "skipped":   [],
    "updated":   [],
    "removed":   [],
    "dry_run":   false
  }
}
```

**Data shape（冲突 → 错误）**

```json
{
  "ok": false,
  "error": {
    "type": "validation",
    "message": "install aborted: 1 conflict(s) not managed by di",
    "hint": "remove or rename the conflicting entry, then re-run `di install`",
    "detail": {
      "conflicts": [{"name": "di-shared", "reason": "real-directory", "path": "..."}]
    }
  }
}
```

**See also** — [`di update`](#di-update) 同流程 + 孤儿删除；[`di doctor`](#di-doctor) 不变更地查看同步状态。

---

### `di update`

**Synopsis** — `di update [--target claude|codex|all] [--dry-run] [--format json|pretty]`

**Purpose** — Re-sync skills（装缺失 + 刷新 stale + **删孤儿**）。`pipx upgrade di-cli` 或 `git pull` 后跑，把 AI 工具目录和 `skills/` 当前状态对齐。

**Risk** write · **Identity required** no · **Source** [`src/di/core/update.py`](../../src/di/core/update.py)

**Behaviors**
- `di install` 做的一切，加上：
- **孤儿删除**：symlink 满足 (a) 是 symlink、(b) 解析落在源 skills 树内、(c) 有 `di-` 前缀、(d) 当前源里没对应 skill、(e) 不在 `EXCLUDED_FROM_INSTALL` —— 才会被删。用户管理的模板 symlink 和外来 symlink 永远不动。
- 原子冲突策略沿用 install —— 任何冲突让 forward + reverse 都中止。

**Data shape** —— 与 `di install` 一致；`removed` bucket 会填充。

**See also** — [`di install`](#di-install)；[`di doctor`](#di-doctor)。

---

### `di doctor`

**Synopsis** — `di doctor [--target claude|codex|all] [--format json|pretty]`

**Purpose** — 只读地检查本地 di-cli 安装状态。

**Risk** read · **Identity required** no · **Source** [`src/di/core/doctor.py`](../../src/di/core/doctor.py)

**Behaviors**
- 四个 check 按顺序跑：`python`、`source`、`target_dirs`、`sync_status`。
- 归并为三档之一 —— `healthy`（全 `ok`）、`degraded`（任一 `warn`）、`unhealthy`（任一 `fail`）。
- **退出码策略**：`healthy` / `degraded` 走 stdout 出 envelope，exit 0；`unhealthy` 走 stderr，exit 5。`degraded` 含义是"能用，值得修" —— agent 应当**任务完成后**再提醒，不要打断。

**Data shape（成功 —— healthy 或 degraded）**

```json
{
  "ok": true,
  "identity": "local",
  "data": {
    "overall": "healthy",
    "checks": [
      {"name": "python", "status": "ok", "message": "Python 3.13.5 satisfies >= 3.9"},
      {"name": "source", "status": "ok", "message": "source skills/ resolved", "detail": {...}},
      {"name": "target_dirs", "status": "ok", "message": "all target skill directories exist"},
      {"name": "sync_status", "status": "ok", "message": "all skills in sync", "detail": {...}}
    ]
  }
}
```

**Data shape（unhealthy → 错误）** —— 同一份 `checks` 列表，放在 `error.detail` 里。Agent 在成功和失败两条路径上读同一个 key（`checks`）。

**See also** — [`di validate`](#di-validate) —— 同 envelope 形状、不同审计对象（authoring conventions vs 运行时状态）。

---

### `di validate`

**Synopsis** — `di validate [--scope all|skills|repo] [--skills-dir <path>] [--format json|pretty]`

**Purpose** — 审计 skill authoring conventions 和仓库形状。CI 在合并前用它作 convention gate。

**Risk** read · **Identity required** no · **Source** [`src/di/core/validate.py`](../../src/di/core/validate.py)

**Behaviors**
- **`--scope skills`** 遍历 `skills/` 下每个目录，校验 SKILL.md frontmatter + 正文、禁止嵌套 skill。
- **`--scope repo`** 跑四个形状 check：AGENTS.md → CLAUDE.md symlink、pyproject.toml 在、skills/ 在、docs/{specs,decisions,explainers}/ 在。
- **`--scope all`**（默认）两者都跑。
- 与 `doctor` 同 `healthy` / `degraded` / `unhealthy` 分档、同退出码策略。
- 必备：`TRIGGER when:` / `DO NOT TRIGGER when:` marker；`di-` 前缀；`description` ≤ 1024 字符；正文以 H1 起头；`maintainer` 看着像邮箱 —— 这些违反走 fail。风格类（行 > 200 字符）走 warn。

**Data shape** —— envelope 形状与 `doctor` 完全一致；`checks` 列表里是 `skills/<name>` 和 `repo/*` 条目。

**See also** — [`di doctor`](#di-doctor)；[`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md) 里有作者开 MR 前要走的合规 checklist。

---

## 服务命令（v0.2 之后）

**v0.2 暂空。** 子团队接入后，service 按 family 出现在这里，每条沿用上面 infrastructure 命令一样的卡片格式。

### Group A —— 查询 / 计算引擎

未来：`di spark`、`di flink`、`di presto`、`di livy`、`di starrocks`、`di kafka`、`di clickhouse`、`di hbase`、`di yarn`。

Group A 操作是 `submit → poll → logs → cancel` 生命周期的 job / query。长任务是常态；命令返回 [handle envelope](../explainers/contracts-for-ai-agents.zh-CN.md#5-handle-长任务不靠猜) 而不是直接给最终结果。

### Group B —— 平台服务

未来：`di datamap`、`di scheduler`、`di dqc`、`di sla`、`di diana`、`di datahub`、`di ram`、`di dataservice`。

Group B 操作是 `lookup / decide / mutate / recover` 生命周期。权限和生命周期管理主导，RAM 是其它服务的守门人。

每个落地的服务都会 ship 一定组合的 shortcut（`di <service> +<verb>`）和 schema-compiled 命令（`di <service> <resource> <method>`）。服务的 SKILL.md 在 `skills/di-<service>-*/` 下，是 AI agent 的权威使用指南。

---

## 裸 API 出口

**未来 Synopsis** —— `di api <service> <METHOD> <path> [--data ...] [--params ...]`

绕过 shortcut 和 schema-compiled 两层。envelope / 退出码 / 风险规则全部保留。仅在前两层都覆盖不到时使用 —— 例如服务上线了新端点但还没并到 schema 时。

裸 API 表面**不**注册到 `di --manifest`（按设计就是 open-ended），但它的 envelope 输出和错误形态与其它 di-cli 命令完全一致。

---

## 另见

- 协议设计：[`docs/explainers/contracts-for-ai-agents.zh-CN.md`](../explainers/contracts-for-ai-agents.zh-CN.md)
- 规范定义：[`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md)
- 面向 Agent 的协议参考：[`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)（英文）
- 子团队接入：[`docs/explainers/onboarding-sub-team.zh-CN.md`](../explainers/onboarding-sub-team.zh-CN.md)
- Skill 模板：[`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md)
