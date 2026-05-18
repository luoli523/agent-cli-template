---
name: mycli-shared
description: >
  CRITICAL — every mycli-* skill depends on this. Read first to learn the
  envelope contract, exit codes, error recovery, confirmation gate,
  _notice protocol, and identity model. No service skill is allowed to
  redefine these — they are the operating protocol between the agent and
  the CLI.
  TRIGGER when: any mycli command is about to be invoked; any mycli-*
  skill is being loaded; the user's request involves a service that this
  CLI wraps.
  DO NOT TRIGGER when: the user is asking a general programming question
  that has no mycli command involved.
maintainer:
  - maintainer@example.com
version: 0.1.0
metadata:
  requires:
    bins: ["mycli"]
  cliHelp: "mycli --help"
---

# mycli-shared

The operating protocol between AI agents and this CLI. Every other
`mycli-*` skill begins by reading this file. Service-specific behavior
lives in those skills; **rules here apply to every mycli call,
regardless of which service is being touched**.

> Authoritative spec: [`docs/specs/2026-05-18-agent-cli-protocol.md`](../../docs/specs/2026-05-18-agent-cli-protocol.md).
> Teaching companion: [`docs/explainers/contracts-for-ai-agents.md`](../../docs/explainers/contracts-for-ai-agents.md).
> This skill is the agent-facing teaching summary; when this file and
> the spec disagree, the spec wins.

---

## CRITICAL — first actions

1. **Before invoking any `mycli` command**, finish reading this file. The
   exit-code policy, confirmation gate, and `_notice` protocol below
   are not optional — getting them wrong destroys data, burns money,
   or silently misleads the user.
2. **Every `mycli` command emits JSON**. Parse stdout for success,
   stderr for errors. Never read raw `--help` text to make runtime
   decisions; that text is for humans. For machine consumption use
   `mycli --manifest` and `mycli <command> --help` field discovery.
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
  "meta":   { "count": 128, "rollback": "mycli <service> undo <op> <id>" },
  "_notice": { /* see _notice protocol below */ }
}
```

- `ok` is always `true` on success.
- `identity` echoes the resolved role. Confirm it matches what you
  expected before consuming `data`.
- `data` shape is per-command; `mycli <command> --help` documents it.
- `meta.count` appears on list-style results.
- `meta.rollback` appears on reversible writes — it is the inverse
  command. **Run it verbatim** to undo; do not compose your own undo.

### Error envelope (stderr, exit ≠ 0)

```json
{
  "ok": false,
  "identity": "<role>",
  "error": {
    "type":    "permission",
    "message": "missing scope: <service>:<action>:read",
    "hint":    "run `mycli auth request --scope <service>:<action>:read`",
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

### stdout vs stderr

- **stdout = data.** Success envelopes go here. Pipe-safe.
- **stderr = everything else.** Error envelopes, progress, warnings.

---

## Exit code → action

| Exit | Type slug | Agent action |
|------|-----------|--------------|
| `0`  | (success) | Consume `data`. |
| `1`  | `api` | Read `error.type` / `error.hint`. Often transient — surface to user. |
| `2`  | `validation` | Arguments are wrong. Re-read `--help` / `--manifest`, fix, retry. |
| `3`  | `auth` | Token invalid / expired. Run the `hint` command. |
| `4`  | `network` | Retry with backoff. If `retry_after_ms` present, respect it. |
| `5`  | `internal` | CLI bug. Report to maintainer; do not silently retry. |
| `6`  | `cost_gate` | Cost exceeds policy. Show cost to user, get consent, retry with `--yes`. |
| `10` | `confirmation_required` | See **exit 10 protocol** below. Do **NOT** auto-retry with `--yes`. |
| `11` | `deadline` | Hit `--timeout`. Decide whether to extend or escalate. |

---

## exit 10 protocol — confirmation_required

When a command has `risk: high-risk-write` or `risk: destructive-cost`,
calling it without `--yes` returns exit 10. The mandated agent flow:

1. **Recognize**: exit code = 10 AND `error.type == "confirmation_required"`.
2. **Show the user**: the operation, the key parameters, and the risk level.
3. **Wait for explicit user consent.** Vague affirmations are not consent.
4. **On consent**: append `--yes` to the original argv and retry.
5. **On refusal**: terminate the flow.

### Forbidden in exit 10 handling

- Auto-appending `--yes` without showing the user. **Never.**
- Treating exit 10 as a network or permission error.
- Modifying the original arguments beyond appending `--yes`.

---

## `_notice` protocol — out-of-band signals

```json
"_notice": {
  "update":      { "message": "new version available", "command": "mycli update" },
  "skills":      { "message": "skills drift detected", "command": "mycli update" },
  "deprecation": { "message": "<command> will be removed in 1.0", "url": "..." }
}
```

Rules:

1. `_notice` can appear in **both** success and error envelopes.
2. **Do not** treat `_notice` as an error.
3. **Do not** interrupt the user's current task to address it.
4. **After** the current task completes, mention the notice once.

---

## Available infrastructure commands

| Command | What it does | Risk |
|---------|--------------|------|
| `mycli version` | Show CLI version, Python, platform. | read |
| `mycli hello` | Demo command — envelope/exit-code/--format showcase. | read |
| `mycli install [--target ...]` | Symlink `skills/mycli-*` into `~/.claude/skills/` and `~/.codex/skills/`. | write |
| `mycli update [--target ...]` | install + remove orphan symlinks. | write |
| `mycli doctor [--target ...]` | Read-only diagnosis of source/target sync state. | read |
| `mycli validate [--scope ...]` | Validate skill authoring conventions and repo shape. | read |
| `mycli --manifest` | Machine-readable map of all registered commands. | read |

---

## Common AI failure modes

Real cases agents have hit. Add new entries whenever a fresh failure is
observed in production.

### F-001 — Auto-retrying exit 10 with `--yes`

**Symptom**: agent invokes a high-risk-write command without `--yes`,
gets exit 10 + `confirmation_required`, sees the `hint` "add --yes",
and immediately retries.

**Why it is wrong**: the gate forces *user consent*, not just the flag.
Auto-retrying skips the consent step entirely.

**Correct behavior**: on exit 10, stop. Render the operation to the
user. Wait for direct agreement. Only then append `--yes`.

**Spotting it in review**: any transcript where exit 10 is followed by
an immediate retry without an intervening user message is broken.

> Add new failure modes here as F-002, F-003, …

---

## Glossary

- **Envelope**: the standard JSON wrapper every command returns.
- **Identity**: the resolved role (`--as`) echoed in every envelope.
- **Risk class**: `read`, `write`, `high-risk-write`, `destructive-cost`.
- **Handle**: envelope shape for long-running async operations.
- **`_notice`**: out-of-band channel for maintenance signals.
- **Manifest**: `mycli --manifest` returns a machine-readable surface map.
