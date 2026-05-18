---
name: di-shared
description: >
  CRITICAL — every di-* skill depends on this. Read first to learn the
  di-cli envelope contract, exit codes, error recovery, confirmation
  gate, _notice protocol, and identity model. No service skill is
  allowed to redefine these — they are the operating protocol between
  the agent and di-cli.
  TRIGGER when: any di-cli command is about to be invoked; any di-*
  skill is being loaded; the user's request mentions `di`, the DI
  platform, or any DI internal service (DataMap, Scheduler, DQC,
  Spark, Flink, Presto, Livy, RAM, etc.).
  DO NOT TRIGGER when: the user is asking a general programming
  question that has no di-cli command involved, or is asking purely
  about git workflow / MR conventions (those have their own skill).
maintainer:
  - li.luo@shopee.com
version: 0.2.0
metadata:
  requires:
    bins: ["di"]
  cliHelp: "di --help"
---

# di-shared

The operating protocol between AI agents and di-cli. Every other
`di-*` skill begins by reading this file. Service-specific behavior
lives in those skills; **rules here apply to every di-cli call,
regardless of which service is being touched**.

> Authoritative spec: [`docs/specs/2026-05-15-di-cli-architecture.md`](../../docs/specs/2026-05-15-di-cli-architecture.md).
> Teaching companion: [`docs/explainers/contracts-for-ai-agents.md`](../../docs/explainers/contracts-for-ai-agents.md).
> This skill is the agent-facing teaching summary; when this file and
> the spec disagree, the spec wins.

---

## CRITICAL — first actions

1. **Before invoking any `di` command**, finish reading this file. The
   exit-code policy, confirmation gate, and `_notice` protocol below
   are not optional — getting them wrong destroys data, burns money,
   or silently misleads the user.
2. **Every `di` command emits JSON**. Parse stdout for success,
   stderr for errors. Never read raw `--help` text to make runtime
   decisions; that text is for humans. For machine consumption use
   `di --manifest` and `di <command> --help` field discovery.
3. **Default `--format` is `json`**. The `pretty` / `table` / `csv` /
   `ndjson` formats exist for humans; do not switch away from json.

---

## Envelope contract

Every command returns one of two JSON shapes. Memorize the keys.

### Success envelope (stdout, exit 0)

```json
{
  "ok": true,
  "identity": "<role>",
  "data":   { /* command-specific payload */ },
  "meta":   { "count": 128, "rollback": "di ram undo <op> <id>" },
  "_notice": { /* see _notice protocol below */ }
}
```

- `ok` is always `true` on success.
- `identity` echoes the resolved role (the lens the command ran
  under). Confirm it matches what you expected before consuming
  `data` — a command running under the wrong identity often
  returns "empty but successful" results.
- `data` shape is per-command; `di <command> --help` documents it.
- `meta.count` appears on list-style results.
- `meta.rollback` appears on reversible writes — it is the
  inverse command. **Run it verbatim** to undo; do not compose
  your own undo.

### Error envelope (stderr, exit ≠ 0)

```json
{
  "ok": false,
  "identity": "<role>",
  "error": {
    "type":    "permission",
    "code":    99991679,
    "message": "missing scope: datamap:lineage:read",
    "hint":    "run `di ram request --scope datamap:lineage:read`",
    "permission_violations": ["datamap:lineage:read"],
    "console_url": "https://ram.internal/scope-apply?scope=...",
    "retry_after_ms": 30000,
    "risk":   { "level": "high-risk-write", "action": "datamap +delete" },
    "detail": { /* raw service response or extra fields */ }
  },
  "meta":   { /* same as success */ },
  "_notice": { /* same as success */ }
}
```

- `ok` is always `false` on error.
- `error.type` is the coarse class. Branch on it.
- `error.hint`, when present, is **the next command to run**. Trust
  it before composing your own.
- `error.console_url`, when present, is what to surface to the user
  when the issue requires manual console action.
- Other fields are populated only when applicable.

### stdout vs stderr

- **stdout = data.** Success envelopes go here. Pipe-safe.
- **stderr = everything else.** Error envelopes, progress, warnings.
- Mixing the two corrupts pipe chains. Treat stdout as a contract
  to downstream parsers.

---

## Exit code → action

| Exit | Type slug it usually carries | Agent action |
|------|-----------------------------|--------------|
| `0`  | (success)                    | Consume `data`. |
| `1`  | `api`                        | Read `error.type` / `error.hint`. Often transient — surface to user. |
| `2`  | `validation`                 | The arguments you sent are wrong. Re-read `--help` / `--manifest`, fix, retry. |
| `3`  | `auth`                       | Token invalid / expired. Run the `hint` command (typically `di auth login --scope <s>`) or surface `console_url` to user. |
| `4`  | `network`                    | Retry with backoff. If `retry_after_ms` present, respect it. |
| `5`  | `internal`                   | Bug in di-cli. Report to maintainer; do not silently retry. |
| `6`  | `cost_gate`                  | Operation refused because compute cost exceeds policy. Show cost to user, request explicit consent, retry with `--yes`. |
| `10` | `confirmation_required`      | See **exit 10 protocol** below. Do **NOT** auto-retry with `--yes`. |
| `11` | `deadline`                   | Operation hit `--timeout`. Decide whether to extend timeout or escalate. |

If the exit code is unfamiliar, treat as `1`/`api` and surface the
envelope to the user.

---

## Error.type catalogue

Coarser than the per-command response codes. AI agents branch on
`type` to choose a recovery strategy.

| `type`                  | What it means | Typical recovery |
|------------------------|--------------|------------------|
| `validation`           | Bad arguments. | Inspect, fix, retry. |
| `permission`           | RAM scope missing or insufficient. | Read `permission_violations`; run `hint`; if Bot identity, surface `console_url` to user. |
| `auth`                 | Token invalid / expired. | Run `hint` (usually `di auth login …`). |
| `api`                  | Service returned a non-permission error. | Treat per service skill instructions; default to surfacing to user. |
| `network`              | Transport failed. | Backoff + retry; respect `retry_after_ms`. |
| `internal`             | di-cli bug. | Do not retry; report. |
| `cost_gate`            | Estimated cost beyond policy. | Ask user; retry with `--yes` only on explicit consent. |
| `confirmation_required`| High-risk write missing `--yes`. | See exit 10 protocol. |
| `deadline`             | Client-side timeout hit. | Decide: extend or escalate. |

---

## Permission errors — recovery protocol

When `error.type == "permission"`:

1. Parse `permission_violations` — it lists the missing scopes.
2. Run `error.hint` verbatim if present. This is typically
   `di ram request --scope <s>` (User identity) or returns a
   `console_url` (Bot identity / scopes requiring manual approval).
3. If the hint runs successfully, retry the original command.
4. If the hint still fails or the violation is bot-scope:
   - Surface `console_url` to the user **exactly as returned** by
     the CLI. Do not URL-encode, decode, wrap in Markdown link
     text, or otherwise mutate it. Render it in a fenced code
     block so the user can copy it.

Never paper over a permission failure by suggesting the user
disable a check or run a different command that bypasses the gate.

---

## exit 10 protocol — confirmation_required

The most-violated rule in agent failure modes. Read carefully.

When a command has `risk: high-risk-write` or `risk: destructive-cost`,
calling it without `--yes` returns:

```json
{
  "ok": false,
  "error": {
    "type": "confirmation_required",
    "message": "datamap +delete requires confirmation",
    "hint":    "add --yes after explicit user consent",
    "risk":    { "level": "high-risk-write", "action": "datamap +delete" }
  }
}
```

with exit code **10**. The mandated agent flow:

1. **Recognize**: subprocess exit code = 10 AND `error.type == "confirmation_required"`. This is a protocol signal, not an error.
2. **Show the user**: the operation (`error.risk.action`), the
   essential parameters you would pass, and the risk level. State
   plainly: *"this is a high-risk operation"*.
3. **Wait for explicit user consent.** Vague affirmations ("ok",
   "go on") are not consent in this branch; the user must directly
   agree to the operation you described.
4. **On consent**: append `--yes` to the original argv (the exact
   same argv you used before) and retry.
5. **On refusal**: terminate the flow. Do not loop, do not rephrase
   the operation, do not search for a non-gated equivalent.

### Forbidden in exit 10 handling

- Auto-appending `--yes` and retrying without showing the user.
  This is equivalent to disabling the gate. **Never.**
- Treating exit 10 as a network or permission error.
- Modifying the original arguments beyond appending `--yes`.
- Using shell-string composition (`sh -c "... --yes"`) to retry;
  pass argv as a list so user-supplied parameters cannot be
  reinterpreted as shell syntax.

### Preview before consent

If you want the user to see the exact request before consenting,
re-invoke with `--dry-run` first. Dry-run does not trigger the
gate; it prints the request envelope (URL, body, params) without
side effects. Show that to the user, then proceed to the gated
call when they approve.

---

## `_notice` protocol — out-of-band signals

Some envelope payloads carry an `_notice` field. It is the system's
way of nudging the agent toward maintenance actions without
interrupting the user's current task.

```json
"_notice": {
  "update":       { "message": "new di-cli available", "command": "di update" },
  "skills":       { "message": "skills drift from di-cli version", "command": "di update" },
  "deprecation":  { "message": "datamap +foo will be removed in 1.0", "url": "..." },
  "auth_expiring":{ "message": "user token expires in 7 days" }
}
```

Rules:

1. `_notice` can appear in **both** success and error envelopes.
2. **Do not** treat `_notice` as an error.
3. **Do not** interrupt the user's current task to address it.
4. **After** the current task completes, mention the notice once and
   suggest the recommended action. Then continue.
5. If multiple notice types appear, surface all of them.

Common: `update` → user runs `di update`; `auth_expiring` → user
re-runs `di auth login` later; `deprecation` → mention the migration
URL the next time the deprecated command is invoked.

---

## Identity (`--as`) — sanity check, not just a flag

Every envelope echoes `identity`. The value comes from the
credential resolver (see spec § Identity); `--as <role>` lets the
agent override the default.

Why this matters: a command running under the wrong identity often
succeeds but returns the wrong view of the world. Example: with a
Bot identity, listing "my tasks" returns the Bot's tasks (none),
not the user's. The command exits 0, the envelope has `data: []`,
and a naive agent reports "you have no tasks" — which is wrong.

Before consuming `data` on identity-sensitive commands:

1. Read `identity` from the envelope.
2. Confirm it matches what you expected (e.g., did you pass
   `--as user` and get `identity` starting with `ram:user:`).
3. If it does not match, either retry with the correct `--as`
   or surface the mismatch to the user before drawing conclusions.

The exact role taxonomy is defined by RAM, not by di-cli core.
Each service skill documents which identity its commands expect.

---

## Three-layer command surface

When you need to invoke a service, try the layers in order. Stop at
the first one that fits.

1. **Shortcuts** — `di <service> +<verb>` (e.g. `di datamap +search`).
   Hand-written, agent-friendly, smart defaults. Strongly preferred
   when one exists for your intent.
2. **Schema-compiled commands** — `di <service> <resource> <method>`
   (e.g. `di datamap tables list`). 1:1 with the service API. Use
   `di schema <service>.<resource>.<method>` first to see the
   parameter shape — never guess fields.
3. **Raw API** — `di api <service> <METHOD> <path>`. The escape
   hatch. Same envelope rules apply: success → stdout JSON, error
   → stderr structured envelope. Use only when shortcut and
   compiled command both fail to cover the case.

> **v0.2 state**: there are no service commands yet. Only the
> infrastructure commands listed below exist. The three-layer
> model is the surface every future service will mount under.

---

## Available infrastructure commands (v0.2)

These are the only `di` commands defined in v0.2. They touch the
local machine, not any DI service.

| Command | What it does | Risk |
|---------|--------------|------|
| `di version`                | Show CLI version, Python, platform. | read |
| `di install [--target ...]` | Symlink `<repo>/skills/di-*` into `~/.claude/skills/` and `~/.codex/skills/`. Atomic conflict abort. | write |
| `di update [--target ...]`  | install + remove orphan symlinks whose source skill no longer exists. | write |
| `di doctor [--target ...]`  | Read-only diagnosis of source / target dirs / sync drift / Python version. | read |
| `di validate [--scope ...]` | Validate skill authoring conventions and repo shape (CI gate). | read |
| `di --manifest`             | Machine-readable map of all registered commands. | read |

None require `--yes`. None require `--as`. The first service to
land will add the first identity-bearing commands.

---

## Common AI failure modes

Real cases agents have hit. Read these before writing new di-* skills;
add new entries whenever you observe a fresh failure in production.

### F-001 — Auto-retrying exit 10 with `--yes`

**Symptom**: agent invokes a high-risk-write command without
`--yes`, gets exit 10 + `confirmation_required`, sees the `hint`
"add --yes", and immediately retries with `--yes` appended.

**Why it is wrong**: the gate's purpose is *not* to remind the
agent to add `--yes` — it is to force the agent to *show the user
the operation* and obtain explicit consent. Auto-retrying skips
the consent step, which is the entire reason the gate exists.

**Correct behavior**: on exit 10, *stop*. Render the operation
description (`error.risk.action`, key parameters) to the user.
Wait for direct user agreement to that specific operation. Only
then append `--yes` and retry.

**Spotting it in review**: any agent-generated transcript where
exit 10 is followed by an immediate retry without an intervening
user message is broken.

> Add new failure modes here as F-002, F-003, … Each entry should
> include symptom, root cause, correct behavior, and how to spot
> it in transcripts.

---

## When to stop and ask the user

Default to asking when any of the following are true:

- Command risk is `high-risk-write` or `destructive-cost` (the
  protocol forces this via exit 10; do not try to work around it).
- The user's intent is ambiguous about destination (which table,
  which project, which environment).
- The envelope `identity` does not match the user's stated role.
- A `_notice.auth_expiring` arrives and an authentication action
  would interrupt a long-running task.
- You would have to compose an unsupported parameter shape
  (`schema` lookup gave you a structure you cannot fill from
  the user's request).

Asking is cheaper than rolling back. The cost of a confirmation
prompt is one short user message; the cost of a wrong destructive
write can be irreversible.

---

## Glossary

- **Envelope**: the standard JSON wrapper every command returns
  (success or error).
- **Identity**: the resolved role (`--as`) under which the command
  ran; echoed in every envelope as a sanity-check anchor.
- **Risk class**: declared per command — `read`, `write`,
  `high-risk-write`, `destructive-cost`. Drives the `--yes` gate.
- **Handle**: an envelope shape returned by long-running async
  operations. Carries `kind`, `id`, `status`, `actions`, and
  `deadline`. The `actions` field is a map of literal command
  strings — copy them; never compose your own follow-up command.
- **`_notice`**: out-of-band channel for maintenance signals
  (update, skills drift, deprecation, auth expiring). Address
  after the current task, never instead of it.
- **Manifest**: `di --manifest` returns a machine-readable surface
  map of every registered command. Use it for capability
  discovery instead of parsing `--help` text.
