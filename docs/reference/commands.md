# di-cli command reference

> **Language**: [English](commands.md) | [中文](commands.zh-CN.md)

The catalogue of every command di-cli ships. v0.2 ships only the five infrastructure commands listed under "Infrastructure commands"; the "Service commands" section is the placeholder structure for future sub-team contributions.

For machine-readable discovery, prefer `di --manifest`. This page is the human-readable companion — it adds the "when to use" / "what to expect" context the manifest cannot carry.

## How to discover commands at runtime

| Tool | Use when |
|------|----------|
| `di --manifest` | An AI agent needs a structured surface map of every registered command (JSON envelope). |
| `di --help` | A human wants the top-level summary, including the standard flags. |
| `di <command> --help` | A human or agent needs the flags and arguments of a specific command. |

## Three-layer command architecture

When a sub-team's service lands, it exposes capability in one or more of three layers (full rationale in [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Command architecture):

| Layer | Shape | When |
|-------|-------|------|
| **Shortcut** | `di <service> +<verb>` | High-level agent-friendly operation; smart defaults; preferred when available. |
| **Schema-compiled** | `di <service> <resource> <method>` | 1:1 with the service API; full parameter control. |
| **Raw API** | `di api <service> <METHOD> <path>` | Escape hatch; same envelope rules apply. |

Agents prefer the highest layer that fits the task; sub-teams choose which layers to populate per operation.

## Standard flags

Every command accepts the cross-cutting flags below (defined in [`src/di/runtime/flags.py`](../../src/di/runtime/flags.py)). Not every flag has runtime behavior in v0.2 — placeholders are kept so AI agents do not need to relearn the flag set when async / paginated operations land.

| Flag | Value | Status in v0.2 |
|------|-------|----------------|
| `--format` | `json` (default), `pretty`, `table`, `ndjson`, `csv` | `json`/`pretty` implemented; the rest render as compact JSON. |
| `--dry-run` | bool | Implemented by `install` / `update` / future service writes. |
| `--yes` | bool | Wired; no v0.2 command currently has `high-risk-write` risk. |
| `--as` | `<role>` | Accepted; no v0.2 command resolves identity (no real services yet). |
| `--profile` | `<name>` | Placeholder for multi-profile config. |
| `--watch` | bool | Placeholder for read-side polling. |
| `--follow` | bool | Placeholder for streamed long-running ops. |
| `--timeout` | `<duration>` | Placeholder; future deadline enforcement returns exit 11. |
| `--page-all` | bool | Placeholder for auto-pagination. |
| `--page-size` | `<N>` | Placeholder. |
| `--page-limit` | `<N>` | Placeholder. |

Standard convention: pass flags **after** the subcommand (`di version --format pretty`). The reverse order works for top-level flags only (`--manifest`, `--version`).

---

## Infrastructure commands (v0.2)

Listed in lifecycle order: how a typical user encounters them. All five operate on the local machine or on di-cli itself; none reaches a DI service yet.

### `di version`

**Synopsis** — `di version [--format json|pretty]`

**Purpose** — Show CLI version, Python interpreter version, and host platform.

**Risk** read · **Identity required** no · **Source** [`src/di/core/version.py`](../../src/di/core/version.py)

**Behaviors**
- Pure read; no side effects.
- Always exits 0 on a built install.

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

**See also** — `di --manifest` for the registered command catalogue including `version` itself.

---

### `di install`

**Synopsis** — `di install [--target claude|codex|all] [--dry-run] [--format json|pretty]`

**Purpose** — Symlink `<repo>/skills/di-*/` into `~/.claude/skills/<name>` and `~/.codex/skills/<name>` so the bundled skills appear in AI tool directories.

**Risk** write · **Identity required** no · **Source** [`src/di/core/install.py`](../../src/di/core/install.py)

**Behaviors**
- **Zero-state ownership model**: a target entry is "managed by di" iff it is a symlink resolving into our source `skills/` tree. Real directories, files, and foreign symlinks are left untouched.
- **Atomic conflict policy**: any conflict (real directory, foreign symlink) aborts the whole run with exit 2 and a structured error envelope. No partial success mode.
- **Idempotent**: running again is a no-op when state matches.
- **Excludes `di-skill-template`**: the template is a fork starting point, never installed.

**Source resolution**: `DI_SKILLS_DIR` env var > walk up from `di.__file__` looking for a `pyproject.toml` sibling with `skills/`.

**Data shape (success)**

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

**Data shape (conflict → error)**

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

**See also** — [`di update`](#di-update) for the same flow plus orphan removal; [`di doctor`](#di-doctor) to inspect sync state without mutating.

---

### `di update`

**Synopsis** — `di update [--target claude|codex|all] [--dry-run] [--format json|pretty]`

**Purpose** — Re-sync skills (install missing + refresh stale + **remove orphans**). Run after `pipx upgrade di-cli` or `git pull` to bring the AI tool directories back in line with what ships under `skills/`.

**Risk** write · **Identity required** no · **Source** [`src/di/core/update.py`](../../src/di/core/update.py)

**Behaviors**
- Everything `di install` does, plus:
- **Orphan removal**: a symlink is removed when it is (a) a symlink, (b) resolves into our source skills tree, (c) has the `di-` prefix, (d) has no matching source skill today, (e) is not in `EXCLUDED_FROM_INSTALL`. User-managed template symlinks and foreign symlinks are never touched.
- Atomic conflict policy carries over from install — any conflict aborts both forward and reverse sync.

**Data shape** — identical to `di install`; `removed` bucket is populated.

**See also** — [`di install`](#di-install); [`di doctor`](#di-doctor).

---

### `di doctor`

**Synopsis** — `di doctor [--target claude|codex|all] [--format json|pretty]`

**Purpose** — Read-only health check of the local di-cli setup.

**Risk** read · **Identity required** no · **Source** [`src/di/core/doctor.py`](../../src/di/core/doctor.py)

**Behaviors**
- Four checks run in order: `python`, `source`, `target_dirs`, `sync_status`.
- Reduces to one of three grades — `healthy` (all `ok`), `degraded` (any `warn`), `unhealthy` (any `fail`).
- **Exit code policy**: `healthy` / `degraded` exit 0 (envelope on stdout); `unhealthy` exits 5 (envelope on stderr). `degraded` is "works, worth fixing" — agents should mention it after the current task, not interrupt for it.

**Data shape (success — healthy or degraded)**

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

**Data shape (unhealthy → error)** — the same `checks` list, carried inside `error.detail`. Agents read the same key (`checks`) in both success and failure paths.

**See also** — [`di validate`](#di-validate) — same envelope shape, different audit (authoring conventions vs runtime state).

---

### `di validate`

**Synopsis** — `di validate [--scope all|skills|repo] [--skills-dir <path>] [--format json|pretty]`

**Purpose** — Audit skill authoring conventions and repo shape. Used by CI as the convention gate before merge.

**Risk** read · **Identity required** no · **Source** [`src/di/core/validate.py`](../../src/di/core/validate.py)

**Behaviors**
- **`--scope skills`** walks every directory under `skills/`, validating SKILL.md frontmatter + body and forbidding nested skills.
- **`--scope repo`** runs four shape checks: AGENTS.md → CLAUDE.md symlink, pyproject.toml present, skills/ present, docs/{specs,decisions,explainers}/ present.
- **`--scope all`** (default) runs both.
- Same `healthy` / `degraded` / `unhealthy` grade as `doctor`; same exit-code policy.
- Authoring conventions (required: `TRIGGER when:` / `DO NOT TRIGGER when:` markers; `di-` prefix; ≤ 1024-char `description`; H1 body heading; `maintainer` looks like emails) are enforced at fail level. Style (line length > 200) is warn.

**Data shape** — identical envelope to `doctor`; `checks` list contains `skills/<name>` and `repo/*` entries.

**See also** — [`di doctor`](#di-doctor); [`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md) for the compliance checklist authors run through before opening an MR.

---

## Service commands (post-v0.2)

**Empty in v0.2.** As sub-teams onboard, services appear here, organized by service family. Each entry follows the same card format as the infrastructure commands above.

### Group A — Query / Compute engines

Future: `di spark`, `di flink`, `di presto`, `di livy`, `di starrocks`, `di kafka`, `di clickhouse`, `di hbase`, `di yarn`.

Group A operations are jobs / queries with `submit → poll → logs → cancel` lifecycles. Long-running is the norm; commands return [handle envelopes](../explainers/contracts-for-ai-agents.md#5-handle-long-jobs-without-guessing) instead of inline results.

### Group B — Platform services

Future: `di datamap`, `di scheduler`, `di dqc`, `di sla`, `di diana`, `di datahub`, `di ram`, `di dataservice`.

Group B operations are `lookup / decide / mutate / recover` lifecycles. Permission and lifecycle management dominate; RAM gates the others.

Each service that lands ships some mix of shortcuts (`di <service> +<verb>`) and schema-compiled commands (`di <service> <resource> <method>`). The service's SKILL.md under `skills/di-<service>-*/` is the authoritative usage guide for AI agents.

---

## Raw API escape hatch

**Synopsis (future)** — `di api <service> <METHOD> <path> [--data ...] [--params ...]`

Bypasses both shortcuts and schema-compiled commands. Same envelope, exit-code, and risk rules apply. Use only when neither layer covers the case — for example, when a service ships a brand-new endpoint that hasn't been folded into the schema yet.

The raw API surface is not registered in `di --manifest` (it is open-ended by design), but its envelope output and error shape match every other di-cli command.

---

## See also

- Protocol design: [`docs/explainers/contracts-for-ai-agents.md`](../explainers/contracts-for-ai-agents.md)
- Normative spec: [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md)
- Agent-facing protocol reference: [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)
- Sub-team onboarding: [`docs/explainers/onboarding-sub-team.md`](../explainers/onboarding-sub-team.md)
- Skill template: [`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md)
