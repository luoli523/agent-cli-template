# Command reference

The catalogue of every command this CLI ships. For machine-readable
discovery, prefer `mycli --manifest`. This page adds the "when to use"
context the manifest cannot carry.

## How to discover commands at runtime

| Tool | Use when |
|------|----------|
| `mycli --manifest` | Agent needs a structured surface map (JSON envelope). |
| `mycli --help` | Human wants the top-level summary + standard flags. |
| `mycli <command> --help` | Human or agent needs flags for a specific command. |

## Three-layer command architecture

| Layer | Shape | When |
|-------|-------|------|
| **Shortcut** | `mycli <service> +<verb>` | High-level, smart defaults; preferred when available. |
| **Schema-compiled** | `mycli <service> <resource> <method>` | 1:1 with the service API; full parameter control. |
| **Raw API** | `mycli api <service> <METHOD> <path>` | Escape hatch; same envelope rules apply. |

## Standard flags

Every command accepts these cross-cutting flags
(defined in [`src/mycli/runtime/flags.py`](../../src/mycli/runtime/flags.py)):

| Flag | Value | Status |
|------|-------|--------|
| `--format` | `json` (default), `pretty`, `table`, `ndjson`, `csv` | `json`/`pretty` implemented; rest render as compact JSON. |
| `--dry-run` | bool | Implemented by `install` / `update` / future service writes. |
| `--yes` | bool | Required for `high-risk-write` and `destructive-cost` commands. |
| `--as` | `<role>` | Identity override (passed through to credential layer). |
| `--profile` | `<name>` | Placeholder for multi-profile config. |
| `--watch` | bool | Placeholder for read-side polling. |
| `--follow` | bool | Placeholder for streamed long-running ops. |
| `--timeout` | `<duration>` | Placeholder; future deadline enforcement exits 11. |
| `--page-all` | bool | Placeholder for auto-pagination. |
| `--page-size` | `<N>` | Placeholder. |
| `--page-limit` | `<N>` | Placeholder. |

Convention: pass flags **after** the subcommand (`mycli version --format pretty`).

---

## Infrastructure commands

All operate on the local machine; none reaches an external service.

### `mycli hello`

**Synopsis** — `mycli hello --name <name> [--format json|pretty]`

**Purpose** — Demo command. Shows envelope/exit-code/--format in action.
Delete this command once you've added your first real service command.

**Risk** read · **Identity required** no

**Data shape**

```json
{"ok": true, "identity": "local", "data": {"greeting": "Hello, World!"}}
```

---

### `mycli version`

**Synopsis** — `mycli version [--format json|pretty]`

**Purpose** — Show CLI version, Python interpreter version, and host platform.

**Risk** read · **Identity required** no

**Data shape**

```json
{"ok": true, "identity": "local", "data": {"version": "0.1.0", "python": "3.13.5", "platform": "darwin"}}
```

---

### `mycli install`

**Synopsis** — `mycli install [--target claude|codex|all] [--dry-run]`

**Purpose** — Symlink `skills/mycli-*/` into `~/.claude/skills/` and
`~/.codex/skills/`.

**Risk** write · **Identity required** no

**Behaviors**
- Idempotent (re-run is a no-op when state matches).
- Atomic conflict abort — any conflict exits 2 with a structured error.
- Excludes `mycli-skill-template` (fork starting point, not a runtime skill).

---

### `mycli update`

**Synopsis** — `mycli update [--target claude|codex|all] [--dry-run]`

**Purpose** — Re-sync skills: install missing + refresh stale + remove orphans.
Run after upgrading the CLI or pulling new skills.

**Risk** write · **Identity required** no

---

### `mycli doctor`

**Synopsis** — `mycli doctor [--target claude|codex|all]`

**Purpose** — Read-only health check of the local setup.

**Risk** read · **Identity required** no

**Exit codes**: `healthy`/`degraded` → exit 0 (stdout); `unhealthy` → exit 5 (stderr).

---

### `mycli validate`

**Synopsis** — `mycli validate [--scope all|skills|repo] [--skills-dir <path>]`

**Purpose** — Audit skill authoring conventions and repo shape. Used as a CI gate.

**Risk** read · **Identity required** no

**`--scope skills`** — validates every `skills/` directory (frontmatter, body, prefix).
**`--scope repo`** — validates repo shape (AGENTS.md symlink, pyproject, docs layout).
**`--scope all`** — both (default).

---

## Service commands (post-template)

Empty in the template. Add your service commands here as sub-teams onboard.

---

## See also

- Protocol design: [`docs/explainers/contracts-for-ai-agents.md`](../explainers/contracts-for-ai-agents.md)
- Normative spec: [`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md)
- Agent-facing protocol reference: [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md)
- Service onboarding: [`docs/explainers/onboarding-a-service.md`](../explainers/onboarding-a-service.md)
- Skill template: [`skills/mycli-skill-template/README.md`](../../skills/mycli-skill-template/README.md)
