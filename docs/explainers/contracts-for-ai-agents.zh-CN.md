# Contracts：di-cli 与 AI Agent 之间的操作协议

> **Language**: [English](contracts-for-ai-agents.md) | [中文](contracts-for-ai-agents.zh-CN.md)

![di-cli Contracts 全景图](../../infographic/di-cli-contracts-explained/di-cli-contracts-explained-guige-generated.png)

这是一份**教学性文档**，不是规范。每条 contract 的字段定义、值域、强制性都以 [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § Cross-cutting contracts 为准。本文回答的是这些 contract **为什么存在**、**对应了哪些真实 Agent 场景**、**不写会出什么事**。

副标题：**不是字段清单，是让 Agent 能理解、规划、执行、纠错的一套交通规则。**

---

## 1. 为什么需要 contracts

DI 平台同时有两个结构完全不同的家族：

- **Group A — 计算/查询引擎**：Spark、Flink、Presto、StarRocks、Kafka、ClickHouse、HBase、YARN、Livy。生命周期典型是 `submit → poll → logs → cancel`。长任务是常态、不是异常。计算成本是头等风险。
- **Group B — 平台服务**：DataMap、DataService、Scheduler、DQC、SLA Manager、Diana、DataHub、RAM。生命周期是 `lookup → decide → mutate → recover`。权限和生命周期管理主导一切，RAM 是其他服务的守门人。

两个家族命令形态不同、错误模型不同、时间语义不同。di-cli 不假装它们是同一个面。

di-cli 的主要消费者是 **AI Agent**。每个命令的输出、错误、退出码都被机器解析。一个推论很硬核：**任何无法 machine-actionable 的失败，都是 bug**。一个裸的 `permission denied` 是 bug —— 它没告诉 Agent 缺哪个 scope、去哪申请、申请下来怎么重试。Agent 唯一能做的是放弃或者瞎猜，两者都坏。

Contracts 就是让"放弃 or 瞎猜"消失的协议。

---

## 2. Envelope：让 Agent 知道发生了什么

**所有命令共享同一个外壳**。业务 `data` 字段可以千变万化，协议形状必须稳定。

成功 envelope（写到 stdout）：

```json
{
  "ok": true,
  "identity": "ram:user:alice@company.com",
  "data": { ... },
  "meta": { "count": 128, "rollback": "di ram undo <op> <id>" },
  "_notice": { ... }
}
```

错误 envelope（写到 stderr）：

```json
{
  "ok": false,
  "identity": "ram:user:alice@company.com",
  "error": { "type": "permission", "message": "...", "hint": "...", ... },
  "meta": { ... },
  "_notice": { ... }
}
```

### 为什么字段长这样

- **`identity` 必有**：Agent 经常猜错"我现在以谁的身份在跑"。回显执行身份是 Agent 看到结果后第一时间确认"这是我预期的视角吗"的锚点。如果 `--as` 指定了 user 但实际跑出来是 bot（auto-fallback），envelope 直接告诉 Agent，避免后续用错误身份做后续操作。
- **`meta.rollback` 给写操作的补救路径**：写操作如果产生了可逆变更，envelope 里附带"反操作命令"。Agent 不需要自己拼一条 undo 命令，直接跑 `meta.rollback` 就回滚。
- **`_notice` 是带外提醒**：和当前任务无关的系统消息（CLI 有新版本、skill 漂移、token 快过期）走单独通道。不污染 `data`、不打断当前任务链。详见 § 6。
- **stdout 是数据 / stderr 是错误**：这条约定让管道链不会被混淆。`di datamap +search foo | jq .data` 永远只看到 envelope，永远看不到诊断输出。这是 Agent 能稳定接收 `data` 的前提。

---

## 3. Exit Code + Error Detail：粗信号 + 细信号

两套机制各服务一个消费者：

- **Exit code** → 给 shell 和 CI。看 0 还是非 0 决定是否继续后续步骤，看 10 还是 11 决定是不是要 prompt 用户。
- **Error detail** → 给 Agent。看 `error.type` 选恢复策略，看 `hint` 决定下一条命令。

### Exit code 表

| Code | 含义 |
|---|---|
| 0 | success |
| 1 | api（API / 通用错误） |
| 2 | validation（参数 / 校验失败） |
| 3 | auth（认证失败、token 无效或过期） |
| 4 | network（连接超时、DNS 失败等） |
| 5 | internal（不应发生） |
| 6 | cost_gate（成本门禁拦截） |
| 10 | confirmation_required（缺 `--yes`） |
| 11 | deadline（超时 / 截止时间） |

Exit code 故意保持**粗粒度**。细粒度的错误分类（`permission` 是 `api` 的一种、`rate_limit` 是 `api` 的一种）通过 `error.type` 表达。Shell 用户不需要记 30 个退出码，只需要看几个大分支。

### Error detail 的几个关键字段

- **`type`**：粗分类。`validation` / `permission` / `auth` / `api` / `network` / `internal` / `cost_gate` / `confirmation_required` / `deadline`。
- **`message`**：人类可读 + 机器可解析的一句话描述。
- **`hint`**：能给出补救命令时一定要带。"Permission denied" 没用；"Permission denied: missing scope `datamap:lineage:read`. Run `di ram request --scope datamap:lineage:read`." 才有用。
- **`permission_violations`**：缺失的 scope 列表，Agent 可以批量请求。
- **`console_url`**：去后台手工配置的链接（典型是 bot 缺权限场景，Agent 不能代表 bot 跑 auth login）。
- **`retry_after_ms`**：网络抖动或 rate limit 场景，Agent 知道多久之后重试。
- **`risk`**：当 `type == confirmation_required` 时携带，告诉 Agent 这条命令是什么风险等级。

### 一个具体场景

Agent 跑 `di datamap lineage --table fact_order`，收到：

```json
{
  "ok": false,
  "error": {
    "type": "permission",
    "code": 99991679,
    "message": "missing scope: datamap:lineage:read",
    "hint": "run `di ram request --scope datamap:lineage:read`",
    "permission_violations": ["datamap:lineage:read"],
    "console_url": "https://ram.internal/scope-apply?scope=datamap:lineage:read"
  }
}
```

Agent 的下一步**完全由协议决定**：拿 `hint` 跑命令；如果 `hint` 跑完还是失败，把 `console_url` 转交用户。**不需要解析自然语言、不需要猜**。

---

## 4. Risk：阻止误操作和烧钱

每条命令在 schema 里声明 `risk`。CLI 在调用时根据 risk 决定是否强制 `--yes` 确认门禁。

| 等级 | 含义 | 需要 `--yes`？ |
|---|---|---|
| `read` | 无副作用 | 否 |
| `write` | 可逆变更（通常带 `meta.rollback`） | 否 |
| `high-risk-write` | 不可逆或难恢复 | **是** |
| `destructive-cost` | 可能触发高计算 / 存储成本 | **是** |

### 缺 `--yes` 时的协议（exit 10）

Agent 不带 `--yes` 调高风险命令，CLI 返回：

```json
{
  "ok": false,
  "error": {
    "type": "confirmation_required",
    "message": "datamap +delete requires confirmation",
    "hint": "add --yes after explicit user consent",
    "risk": { "level": "high-risk-write", "action": "datamap +delete" }
  }
}
```

退出码 10。**这是 Agent 协议的一部分**：

1. **识别**：子进程退出码 10 且 `error.type == "confirmation_required"`。
2. **向用户确认**：把 `error.risk.action` 和关键参数展示给用户，明确说"这是高风险操作"。
3. **得到用户明确同意** → 在原始 argv 末尾追加 `--yes` 后重试。
4. **用户拒绝** → 终止流程。

### Agent 失败模式

以下行为**禁止**：

- 看到 exit 10 就自动加 `--yes` 重试（这等于禁用门禁）。
- 把 `confirmation_required` 当成网络错误 / 权限错误处理。
- 不向用户展示风险细节就拼命令。

`--dry-run` 是配套工具：它不触发门禁，输出完整的 request 预览（URL / body / params），Agent 可以把预览给用户看再决定要不要真执行。

---

## 5. Handle：长任务不靠猜

Group A 的引擎（Spark、Flink、Presto、Livy……）每个都有自己的状态机：Spark 用 application id、Flink 用 job id、Presto 用 query id、Livy 用 session。如果每个服务返回不同形状的"任务句柄"，Agent 要为每个引擎写一套追踪逻辑。

Handle envelope 用一个统一形状把它们包起来：

```json
{
  "kind": "spark_application",
  "id": "application_1700000000_0042",
  "status": "running",
  "actions": {
    "poll":   "di spark jobs get --id application_1700000000_0042",
    "follow": "di spark jobs follow --id application_1700000000_0042",
    "logs":   "di spark jobs logs --id application_1700000000_0042",
    "cancel": "di spark jobs cancel --id application_1700000000_0042"
  },
  "deadline": "2026-05-15T18:00:00Z"
}
```

### 为什么 `actions` 是字符串而不是 schema

**Agent 不推断下一步命令，只复制 actions 里的值**。这是协议的核心约束。

- 给 Agent 一段 schema 让它推断"该跑什么"是失败模式 —— Agent 会编命令、编 flag、编参数。
- 给 Agent 一条完整可执行字符串，Agent 只能复制。失败模式被工具消除了。

`status` 给 Agent 看进度；`deadline` 给 Agent 决定是否超时；`actions` 给 Agent 选下一步。统一 Spark/Flink/Presto/Livy 不同状态机的复杂度被 di-cli 吃掉，Agent 一套逻辑通吃。

---

## 6. `_notice`：带外提醒

某些消息不属于当前请求的 `data`，但 Agent 应该在完成当前任务后告诉用户：

- **`update`**：di-cli 有新版本可装。
- **`skills`**：本地 skills 跟 CLI 版本漂移，建议 `di update`。
- **`deprecation`**：当前命令将在某版本移除，给出迁移路径。
- **`auth_expiring`**：当前身份 token 快过期。

```json
{
  "ok": true,
  "data": { ... },
  "_notice": {
    "update": { "message": "new di-cli available", "command": "di update" },
    "auth_expiring": { "message": "token expires in 7 days" }
  }
}
```

### 协议约束

- `_notice` **可以**出现在成功和失败的 envelope 中。
- 它**不打断**当前任务 —— Agent 必须先完成用户当前请求，再附带提醒。
- 不要把 `_notice` 当错误处理，也不要静默吞掉。

`_notice` 是带外通道：主体响应不变，附加信号让 Agent 引导用户做配套动作。这是 lark-cli 设计中最优雅的机制之一，di-cli 直接借鉴。

---

## 6.5. Public API：原始出口

di-cli 还有一条逃生通道：

```bash
di api <service> <METHOD> <path> [--data ...] [--params ...]
```

任何 shortcut 和 schema-compiled 命令都覆盖不到的端点，可以用 `di api` 裸调底层 HTTP。

### 为什么仍然要有这一层

- **绕过 CLI 策展**：Agent 在边缘场景需要原始 HTTP 控制时，不应被工具的命令编排限制。
- **最简洁**：少一层 wrapper，少一处可能出错的地方。
- **错误也走同一协议**：哪怕走 raw API，响应仍然进 envelope、错误仍然分类、退出码仍然按表走。**Agent 看到的形状不变**。

但要小心 —— shortcut 和 schema 命令的存在是有原因的（参数补全、智能默认、术语映射、风险声明）。Agent 应该优先用高层封装，只有在覆盖不到时才落到 `di api`。

---

## 7. Agent 行为闭环

把上面 6 个 contract 拼起来，Agent 的工作变成一个规则驱动的闭环：

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  理解     │ -> │  规划     │ -> │  执行     │ -> │  纠错     │
│ Understand│    │  Plan     │    │  Execute  │    │  Recover  │
└───────────┘    └───────────┘    └───────────┘    └───────────┘
   ↑                                                       │
   └───────────────────────────────────────────────────────┘
```

| 阶段 | Agent 做什么 | 对应 contract |
|---|---|---|
| 理解 | 读 envelope 的 `identity` / `data` / `meta` / `_notice` 确认状态 | Envelope |
| 规划 | 读 manifest / `--help` / `actions` 决定下一步策略 | Manifest、Handle |
| 执行 | 按 risk 等级决定是否要确认；发命令 | Risk |
| 纠错 | 看 `exit code` 选大分支；看 `error.type` + `hint` + `retry_after_ms` 恢复 | ExitCode、ErrDetail |

每个阶段都有 contract 撑腰。Agent 不需要从自然语言、不完整文档、未经训练的 API 形状里猜东西。

---

## 结论

> **Contracts = 把 Agent 的下一步从猜测变成规则。**

这就是为什么 di-cli 的 v1 不是 "install/update 几条命令"，而是**先把 contract 钉死**。Contract 是协议表面，是与所有未来子团队的契约。一旦稳定下来：

- 每个子团队的 schema 都按这套协议编译。
- 每个 skill 都假设 Agent 能消费这套协议。
- 每个错误都按这套协议结构化。
- 每个长任务都套这个 handle。
- 每条新版本提醒都走这条 `_notice`。

di-cli 真正的产品不是命令，**是这套协议本身**。

---

## 参考

- 正式定义：[`docs/specs/2026-05-15-di-cli-architecture.zh-CN.md`](../specs/2026-05-15-di-cli-architecture.zh-CN.md) § 横切契约
- 决策背景：[`docs/decisions/0002-architecture-reset.md`](../decisions/0002-architecture-reset.md)
- 面向 Agent 的教学 skill（英文）：[`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)
- 实现源码：`src/di/contracts/`
- 配图源材料：[`infographic/di-cli-contracts-explained/`](../../infographic/di-cli-contracts-explained/)
