# Spec: Agent-CLI Protocol v1

Status: Accepted
Date: 2026-05-18

## Mission

This CLI is the operation layer between AI agents and one or more backend
services. It wraps the services' APIs into a uniform command system that a
machine can **understand, plan, execute, and recover from**.

**Primary consumer**: AI agent. Every command output, error message, and
exit code is parsed by a machine. Humans are a secondary consumer who
fall back to `--format pretty` when reading directly.

The single rule this implies: **no command is complete until its failure
modes are machine-actionable.** A bare "permission denied" is a bug; the
error must tell the agent which scope is missing and which command would
request it.

## Four design axes

Every contract in this spec traces back to one of these four.

### 1. Understand — discover capability without external docs

- `mycli --help`, `mycli <service> --help` expose purpose and parameters.
- `mycli --manifest` emits a machine-readable surface map for agent indexing.
- Skill files anchor domain terminology with explicit trigger/no-trigger rules.

### 2. Plan — know which commands to sequence before invoking

- Risk class (`read` / `write` / `high-risk-write` / `destructive-cost`) is
  declared per command so agents can assess consequences before executing.
- `--dry-run` returns the request shape without side effects.
- Handle envelopes for async ops encode the exact follow-up commands the
  agent is allowed to run — no guessing.

### 3. Execute — invoke correctly the first time

- Standard flags (`--format`, `--as`, `--yes`, `--timeout`, etc.) work
  the same way on every command.
- `--format json` is the default and the machine-safe choice.
- All parameters are validated before any side effect occurs.

### 4. Recover — know exactly what went wrong and how to fix it

- Every error carries `type` (coarse class for branching) and `hint`
  (the literal next command to run, when one exists).
- Exit codes map 1:1 to recovery actions (see § Exit codes).
- `meta.rollback` appears on reversible writes — run it verbatim to undo.

---

## Cross-cutting contracts

### Output envelope

Every command writes exactly one JSON object. Success → stdout, exit 0.
Error → stderr, exit ≠ 0.

**Success envelope**

```json
{
  "ok": true,
  "identity": "<resolved-role>",
  "data": { "...command-specific..." },
  "meta": {
    "count": 42,
    "rollback": "mycli <service> undo <id>"
  },
  "_notice": { "...maintenance signals..." }
}
```

**Error envelope**

```json
{
  "ok": false,
  "identity": "<resolved-role>",
  "error": {
    "type": "permission",
    "message": "missing scope: <service>:read",
    "hint": "run `mycli auth request --scope <service>:read`",
    "detail": {}
  },
  "meta": {},
  "_notice": {}
}
```

Rules:
- `ok` is always present and always a boolean.
- `identity` echoes the resolved role; confirm it before consuming `data`.
- `data` shape is per-command and documented in `--help`.
- `meta.rollback`, when present, is a literal command string.
- `_notice` may appear on both success and error envelopes.

### Exit codes

| Exit | `error.type` | Agent action |
|------|-------------|--------------|
| `0` | — | Success. Consume `data`. |
| `1` | `api` | Service-level error. Read `error.hint`. |
| `2` | `validation` | Bad arguments. Fix and retry. |
| `3` | `auth` | Authentication failure. Run `error.hint`. |
| `4` | `network` | Transport failure. Backoff + retry. |
| `5` | `internal` | CLI bug. Do not retry. Report. |
| `6` | `cost_gate` | Cost exceeds policy. Show to user, add `--yes` on consent. |
| `10` | `confirmation_required` | High-risk op without `--yes`. Show to user, add `--yes` on consent. |
| `11` | `deadline` | `--timeout` exceeded. Extend or escalate. |

### Error types

| `type` | Recovery |
|--------|---------|
| `validation` | Fix arguments. |
| `permission` | Check `permission_violations`. Run `error.hint`. |
| `auth` | Run `error.hint` (re-authenticate). |
| `api` | Service-specific. Read service skill. |
| `network` | Backoff. Respect `retry_after_ms`. |
| `internal` | Do not retry. Report. |
| `cost_gate` | Ask user. Retry with `--yes` only on consent. |
| `confirmation_required` | Ask user. Retry with `--yes` only on consent. |
| `deadline` | Extend `--timeout` or escalate. |

### Handle envelope (async operations)

Operations that do not complete inline return a handle inside `data`:

```json
{
  "kind": "job",
  "id": "<unique-id>",
  "status": "running",
  "actions": {
    "poll":   "mycli <service> poll --id <id>",
    "cancel": "mycli <service> cancel --id <id> --yes",
    "logs":   "mycli <service> logs --id <id> --follow"
  },
  "deadline": "<iso8601-timestamp>"
}
```

`actions` values are literal command strings. Copy verbatim; never compose
your own follow-up command.

### Risk classification

| Level | `--yes` required | Example |
|-------|-----------------|---------|
| `read` | No | Listing, querying |
| `write` | No | Creating, updating |
| `high-risk-write` | Yes (exit 10 gate) | Deleting, bulk mutation |
| `destructive-cost` | Yes (exit 10 gate) | Launching expensive compute |

**Exit 10 protocol**: on exit 10, STOP. Show the user the operation and
risk level. Wait for explicit consent. Only then append `--yes` and retry.
Never auto-retry without an intervening user message.

### `_notice` channel

Out-of-band signals that should not interrupt the current task:

```json
"_notice": {
  "update":      { "message": "new version available", "command": "mycli update" },
  "skills":      { "message": "skills out of sync", "command": "mycli update" },
  "deprecation": { "message": "`mycli foo` removed in v2", "url": "..." },
  "auth_expiring": { "message": "token expires in 7 days" }
}
```

Rules: do not interrupt for `_notice`; address it after the current task
completes; mention it once, then continue.

### Standard flags

Every command inherits these flags (defined in `src/mycli/runtime/flags.py`):

| Flag | Description |
|------|-------------|
| `--format json\|pretty\|table\|ndjson\|csv` | Output format. Default: `json`. |
| `--as <role>` | Identity override. |
| `--profile <name>` | Named credential profile. |
| `--dry-run` | Preview request; no side effects. |
| `--yes` | Confirm high-risk-write / destructive-cost operation. |
| `--watch` | Repeat on interval (read-side polling). |
| `--follow` | Stream output (long-running ops). |
| `--timeout <duration>` | Client-side deadline; exits 11 on overrun. |
| `--page-all` | Auto-paginate. |
| `--page-size <N>` | Page size. |
| `--page-limit <N>` | Max pages with `--page-all`. |

Convention: pass flags **after** the subcommand. Top-level flags
(`--manifest`, `--version`) are the only exceptions.

---

## Three-layer command architecture

```
mycli <service> +<verb>                 Shortcut — high-level, smart defaults
mycli <service> <resource> <method>     Schema-compiled — 1:1 service API
mycli api <service> <METHOD> <path>     Raw escape hatch
```

AI agents prefer the highest available layer; fall back only when needed.

---

## Skill system

**Skills do not execute.** They teach AI how to use CLI commands.

- Skills live under `skills/<name>/` with a `SKILL.md` containing YAML frontmatter.
- All skill names must start with the configured `skill_prefix` (default: `mycli-`).
- `mycli-shared` is the base skill every other skill says "read first".
- `mycli-skill-template` is a fork starting point, not installed by `mycli install`.

Required frontmatter fields: `name`, `description` (with `TRIGGER when:` and
`DO NOT TRIGGER when:` markers), `maintainer`.

---

## Identity and credentials

`--as <role>` overrides the resolved identity. Valid roles are defined by your
credential provider, not by the CLI core.

Never commit credentials: tokens, cookies, private keys, OAuth refresh tokens.

---

## Repo conventions

- `CLAUDE.md` is the AI assistant instructions file.
- `AGENTS.md` must be a symlink to `CLAUDE.md` so Claude Code and Codex share one file.
- `docs/specs/` — normative specs (this file).
- `docs/decisions/` — ADRs for hard-to-reverse decisions.
- `docs/explainers/` — teaching documents.
- `docs/reference/` — lookup tables.

`mycli validate` enforces these conventions and exits non-zero on failures.
