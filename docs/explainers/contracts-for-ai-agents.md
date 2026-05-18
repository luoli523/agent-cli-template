# Contracts: The Operating Protocol Between the CLI and AI Agents

This is a **teaching document**, not a specification. Field definitions,
value sets, and enforcement rules live in
[`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md).
What this document answers is **why each contract exists**, and **what
breaks when it is missing**.

---

## 1. Why contracts are needed

AI agents cannot reliably operate APIs that return unstructured errors,
variable shapes, or ambiguous exit codes. Every failure that is not
machine-actionable forces the agent to give up or guess — both of which
are bad outcomes.

Contracts are the protocol that makes "give up or guess" go away. They
provide:

- A **stable outer shape** regardless of which command ran.
- **Machine-readable errors** with explicit hints.
- **Exit codes** that map to deterministic recovery actions.
- **Async handles** for long-running operations.
- **Risk classification** + a confirmation gate for destructive ops.

---

## 2. Envelope: telling the Agent what happened

**Every command shares the same outer shape.** The `data` field varies;
the protocol shape stays stable.

Success (stdout, exit 0):

```json
{
  "ok": true,
  "identity": "<resolved-role>",
  "data": { "...command-specific..." },
  "meta": { "count": 42, "rollback": "mycli <service> undo <id>" },
  "_notice": { "...maintenance signals..." }
}
```

Error (stderr, exit ≠ 0):

```json
{
  "ok": false,
  "identity": "<resolved-role>",
  "error": {
    "type": "permission",
    "message": "missing scope: <service>:read",
    "hint": "run `mycli auth request --scope <service>:read`",
    "detail": {}
  }
}
```

**Why stdout/stderr split?** Agents pipe stdout to the next step. Mixing
errors into stdout corrupts the pipeline. Errors on stderr are readable
to humans without polluting machine consumers.

**Why `ok` as a boolean?** Agents check one field — not the exit code,
not the presence of an `error` key. One field, two values, no ambiguity.

---

## 3. Exit codes: machine-actionable recovery

Random exit codes force agents to parse error text. Structured exit codes
let agents branch without parsing:

| Exit | Recovery action |
|------|----------------|
| `0` | Success — consume `data`. |
| `1` | API error — read `error.type` and `error.hint`. |
| `2` | Validation — fix arguments, retry. |
| `3` | Auth — run `error.hint` (re-authenticate). |
| `4` | Network — backoff and retry. |
| `5` | Internal bug — surface to user, do not retry. |
| `6` | Cost gate — show cost estimate, get user consent, retry with `--yes`. |
| `10` | Confirmation required — **show user**, get consent, retry with `--yes`. |
| `11` | Deadline exceeded — decide whether to extend `--timeout` or escalate. |

---

## 4. Error types: coarse classification for branching

`error.type` is the branch key. Agents should not parse `error.message`
to determine recovery — messages are for humans. Types are for machines.

| `type` | Recovery |
|--------|---------|
| `validation` | Fix arguments. Re-read `--help`/`--manifest`. |
| `permission` | Check `permission_violations`. Run `error.hint`. |
| `auth` | Run `error.hint` (typically re-authenticate). |
| `api` | Service-level error. Read service skill for recovery patterns. |
| `network` | Backoff + retry; respect `retry_after_ms`. |
| `internal` | CLI bug. Do not retry. Report. |
| `cost_gate` | Show cost to user; add `--yes` on consent. |
| `confirmation_required` | Show operation to user; add `--yes` on consent. |
| `deadline` | Extend `--timeout` or escalate. |

---

## 5. Handle: long-running operations

Some operations (job submission, bulk mutations) do not complete inline.
These return a **handle envelope** instead of a final result:

```json
{
  "ok": true,
  "identity": "<role>",
  "data": {
    "kind": "job",
    "id": "job-abc-123",
    "status": "running",
    "actions": {
      "poll": "mycli jobs poll --id job-abc-123",
      "cancel": "mycli jobs cancel --id job-abc-123 --yes",
      "logs": "mycli jobs logs --id job-abc-123 --follow"
    },
    "deadline": "2026-05-18T15:00:00Z"
  }
}
```

**`actions` are literal command strings.** Copy them verbatim; never
compose your own follow-up command. This is how the CLI encodes
"what you're allowed to do next" in a machine-executable form.

---

## 6. Risk classification: confirmation gates

Commands declare one of four risk levels:

| Level | Meaning | Agent behavior |
|-------|---------|----------------|
| `read` | No side effects. | Execute freely. |
| `write` | Creates or updates a resource. | Execute; log for audit. |
| `high-risk-write` | Deletes, bulk-mutates, or has wide blast radius. | Requires `--yes` (exit 10 gate). |
| `destructive-cost` | Triggers significant compute cost. | Requires `--yes` (exit 10 gate). |

**Exit 10 is not an error.** It is a protocol signal meaning "show the
user what you're about to do and get their consent." Never auto-retry
with `--yes` without an intervening user confirmation.

---

## 7. `_notice`: maintenance signals without interruption

`_notice` is an out-of-band channel for signals that are important but
should not interrupt the current task:

```json
"_notice": {
  "update":      { "message": "new version available", "command": "mycli update" },
  "deprecation": { "message": "`mycli foo` will be removed in v2.0", "url": "..." }
}
```

Rules:
1. `_notice` can appear on both success and error envelopes.
2. Do not treat it as an error or interrupt the current task for it.
3. After the task completes, mention it once and suggest the action.

---

## See also

- Normative spec: [`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md)
- Agent-facing skill: [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md)
- Command reference: [`docs/reference/commands.md`](../reference/commands.md)
