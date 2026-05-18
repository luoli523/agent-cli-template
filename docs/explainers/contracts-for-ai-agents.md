# Contracts: The Operating Protocol Between di-cli and AI Agents

> **Language**: [English](contracts-for-ai-agents.md) | [中文](contracts-for-ai-agents.zh-CN.md)

![di-cli Contracts panorama](../../infographic/di-cli-contracts-explained/di-cli-contracts-explained-guige-generated.png)

This is a **teaching document**, not a specification. Field definitions, value sets, and enforcement rules live in [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Cross-cutting contracts. What this document answers is **why each contract exists**, **which concrete agent scenarios it addresses**, and **what breaks when it is missing**.

Subtitle: **Not a field list — a set of traffic rules that lets an Agent understand, plan, execute, and recover.**

---

## 1. Why contracts are needed

The DI platform has two structurally different families:

- **Group A — Query/Compute engines**: Spark, Flink, Presto, StarRocks, Kafka, ClickHouse, HBase, YARN, Livy. Lifecycle is typically `submit → poll → logs → cancel`. Long-running is the norm, not the exception. Compute cost is a first-class risk.
- **Group B — Platform services**: DataMap, DataService, Scheduler, DQC, SLA Manager, Diana, DataHub, RAM. Lifecycle is `lookup → decide → mutate → recover`. Permission and lifecycle management dominate; RAM gates the others.

The two families have different command shapes, different error models, and different temporal semantics. di-cli does not pretend they are the same surface.

di-cli's primary consumer is the **AI Agent**. Every output, every error, every exit code is parsed by a machine. A hard corollary: **any failure that is not machine-actionable is a bug**. A bare `permission denied` is a bug — it doesn't tell the agent which scope is missing, where to request it, or how to retry once it's granted. The agent's only options are giving up or guessing, both of which are bad.

Contracts are the protocol that makes "give up or guess" go away.

---

## 2. Envelope: telling the Agent what happened

**Every command shares the same outer shape.** The business `data` field varies arbitrarily; the protocol shape must stay stable.

Success envelope (written to stdout):

```json
{
  "ok": true,
  "identity": "ram:user:alice@company.com",
  "data": { ... },
  "meta": { "count": 128, "rollback": "di ram undo <op> <id>" },
  "_notice": { ... }
}
```

Error envelope (written to stderr):

```json
{
  "ok": false,
  "identity": "ram:user:alice@company.com",
  "error": { "type": "permission", "message": "...", "hint": "...", ... },
  "meta": { ... },
  "_notice": { ... }
}
```

### Why the fields look this way

- **`identity` is always present**: Agents frequently misjudge "whose identity am I running under right now". Echoing the resolved identity is the anchor that lets the Agent confirm "is this the lens I expected?" the moment it reads the result. If `--as` requested `user` but resolution fell back to `bot` (auto-fallback), the envelope tells the Agent up front, preventing the next operation from inheriting the wrong identity.
- **`meta.rollback` gives writes a recovery path**: When a write produces a reversible change, the envelope carries the inverse command. The Agent doesn't have to compose an undo — just execute `meta.rollback`.
- **`_notice` is out-of-band**: System messages unrelated to the current task (new CLI version, skill drift, expiring token) ride a separate channel. They don't pollute `data` and don't interrupt the task chain. See § 6.
- **stdout = data, stderr = everything else**: This convention keeps pipe chains uncorrupted. `di datamap +search foo | jq .data` will only ever see envelopes, never diagnostic noise. This is the prerequisite for an Agent to consume `data` reliably.

---

## 3. Exit Code + Error Detail: coarse signal + fine signal

Two mechanisms, two consumers:

- **Exit code** → for shell and CI. Zero vs non-zero decides whether to continue. 10 vs 11 decides whether to prompt the user.
- **Error detail** → for the Agent. `error.type` selects recovery strategy. `hint` decides the next command.

### Exit code table

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | api (API / generic error) |
| 2 | validation (param / schema failure) |
| 3 | auth (token invalid or expired) |
| 4 | network (timeout, DNS failure, …) |
| 5 | internal (should not happen) |
| 6 | cost_gate (cost ceiling hit) |
| 10 | confirmation_required (missing `--yes`) |
| 11 | deadline (timeout) |

Exit codes are intentionally **coarse-grained**. Fine-grained classification (`permission` is a kind of `api`, `rate_limit` is a kind of `api`) goes in `error.type`. Shell users do not have to memorize thirty exit codes; just the handful of major branches.

### Key fields in error detail

- **`type`**: coarse classification — `validation` / `permission` / `auth` / `api` / `network` / `internal` / `cost_gate` / `confirmation_required` / `deadline`.
- **`message`**: a single human-readable + machine-parseable sentence.
- **`hint`**: must be present whenever a remediation command exists. "Permission denied" is useless; "Permission denied: missing scope `datamap:lineage:read`. Run `di ram request --scope datamap:lineage:read`." is useful.
- **`permission_violations`**: the list of missing scopes, so the Agent can request them in a batch.
- **`console_url`**: a link to manual console configuration (typical for bot-scope errors where the Agent cannot run `auth login` on behalf of a bot).
- **`retry_after_ms`**: for jitter and rate limits, so the Agent knows when to retry.
- **`risk`**: carried when `type == confirmation_required`, telling the Agent what risk class this command is.

### A concrete scenario

Agent runs `di datamap lineage --table fact_order` and receives:

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

The Agent's next step is **fully determined by the protocol**: run the `hint` command; if that still fails, hand the `console_url` to the user. **No natural-language parsing, no guessing.**

---

## 4. Risk: preventing destructive ops and runaway cost

Every command declares a `risk` in its schema. The CLI consults it at invocation time to decide whether to enforce the `--yes` confirmation gate.

| Level | Meaning | Requires `--yes`? |
|---|---|---|
| `read` | no side effects | no |
| `write` | reversible change (usually carries `meta.rollback`) | no |
| `high-risk-write` | irreversible or hard to recover | **yes** |
| `destructive-cost` | may trigger high compute / storage cost | **yes** |

### The protocol when `--yes` is missing (exit 10)

When the Agent calls a high-risk command without `--yes`, the CLI returns:

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

Exit code 10. **This is part of the Agent protocol**:

1. **Recognize**: subprocess exit code 10 and `error.type == "confirmation_required"`.
2. **Confirm with user**: show `error.risk.action` and the salient parameters; state explicitly "this is a high-risk operation".
3. **Explicit user consent** → append `--yes` to the original argv and retry.
4. **User declines** → terminate the flow.

### Agent failure modes

The following are **forbidden**:

- Auto-appending `--yes` and retrying on exit 10 (this is equivalent to disabling the gate).
- Treating `confirmation_required` as a network or permission error.
- Composing the retry command without showing the user the risk details.

`--dry-run` is the companion tool: it does not trigger the gate and prints the full request preview (URL / body / params). Agents can show the preview to the user before deciding whether to execute.

---

## 5. Handle: long jobs without guessing

Group A engines (Spark, Flink, Presto, Livy, …) each have their own state machine: Spark uses application id, Flink uses job id, Presto uses query id, Livy uses session. If every service returned a differently-shaped "job handle", Agents would need a tracking implementation per engine.

The handle envelope wraps them in a uniform shape:

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

### Why `actions` are strings, not schemas

**The Agent does not infer the next command — it copies values from `actions`.** This is the core constraint of the protocol.

- Handing the Agent a schema and asking it to figure out "what to run next" is a failure mode. The Agent will compose commands, invent flags, hallucinate parameters.
- Handing the Agent a fully-executable string leaves it nothing to do but copy. The failure mode is eliminated by the tool.

`status` gives the Agent progress; `deadline` lets it decide on timeouts; `actions` provides the next steps. The complexity of unifying Spark/Flink/Presto/Livy state machines is absorbed by di-cli; the Agent uses a single logic across all of them.

---

## 6. `_notice`: out-of-band signals

Some messages don't belong in the current request's `data` but the Agent should mention them once the current task is done:

- **`update`**: a newer di-cli is available.
- **`skills`**: local skills drift from CLI version; suggest `di update`.
- **`deprecation`**: this command will be removed in a future version; suggest migration.
- **`auth_expiring`**: the current identity's token is about to expire.

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

### Protocol constraints

- `_notice` **may** appear in both success and error envelopes.
- It **does not interrupt** the current task — the Agent must complete the user's current request first, then mention notices.
- Do not treat `_notice` as an error, and do not silently swallow it.

`_notice` is an out-of-band channel: the main response is unchanged; the additional signal lets the Agent prompt the user for follow-ups. This is one of the most elegant mechanisms in lark-cli's design, adopted directly by di-cli.

---

## 6.5. Public API: the raw escape hatch

di-cli ships one explicit bypass:

```bash
di api <service> <METHOD> <path> [--data ...] [--params ...]
```

Any endpoint not covered by shortcuts or schema-compiled commands can be invoked directly via raw HTTP.

### Why this layer still exists

- **Bypass curation when needed**: when an Agent is in an edge case that needs raw HTTP control, the tool's command orchestration shouldn't get in the way.
- **Minimal surface**: one less wrapper, one less place to introduce bugs.
- **Errors still follow the same protocol**: even via raw API, responses are wrapped in envelopes, errors are classified, exit codes follow the table. **The shape the Agent sees does not change.**

But use it carefully — shortcuts and schema commands exist for reasons (param completion, smart defaults, terminology mapping, risk declaration). Agents should prefer the higher-level wrappers and only fall back to `di api` when nothing else covers the case.

---

## 7. The Agent behavior loop

Stack the six contracts together and the Agent's work becomes a rule-driven loop:

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│ Understand│ -> │  Plan     │ -> │  Execute  │ -> │  Recover  │
└───────────┘    └───────────┘    └───────────┘    └───────────┘
   ↑                                                       │
   └───────────────────────────────────────────────────────┘
```

| Stage | What the Agent does | Contract |
|---|---|---|
| Understand | Read envelope `identity` / `data` / `meta` / `_notice` to confirm state | Envelope |
| Plan | Read manifest / `--help` / `actions` to choose the next step | Manifest, Handle |
| Execute | Decide whether to confirm based on risk; run the command | Risk |
| Recover | Branch on `exit code`; use `error.type` + `hint` + `retry_after_ms` to recover | ExitCode, ErrDetail |

Every stage has a contract behind it. The Agent never has to guess from natural language, incomplete docs, or unfamiliar API shapes.

---

## Conclusion

> **Contracts = turning the Agent's next step from guesswork into rules.**

This is why di-cli's v1 isn't "ship a few install/update commands" — it's **nail down the contracts first**. The contracts are the protocol surface, the contract with every future sub-team. Once stable:

- Every sub-team's schema compiles against this protocol.
- Every skill assumes the Agent consumes this protocol.
- Every error is structured against this protocol.
- Every long-running job wraps in this handle.
- Every cross-cutting notification rides this `_notice`.

di-cli's real product is not the commands. **It is this protocol.**

---

## References

- Normative definitions: [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Cross-cutting contracts
- Decision background: [`docs/decisions/0002-architecture-reset.md`](../decisions/0002-architecture-reset.md)
- Agent-facing teaching skill: [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)
- Implementation source: `src/di/contracts/`
- Infographic source materials: [`infographic/di-cli-contracts-explained/`](../../infographic/di-cli-contracts-explained/)
