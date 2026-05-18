# Onboarding a service into the CLI

This guide walks a sub-team from "we have a service we want to expose to
AI agents" to "our skill is merged and our service has a `mycli <service>`
command surface".

Read these first if the concepts are new:

- [`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md)
- [`docs/explainers/contracts-for-ai-agents.md`](contracts-for-ai-agents.md)
- [`docs/explainers/the-shared-skill.md`](the-shared-skill.md)
- [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md)

## What a sub-team owns vs what the CLI core owns

| Owned by sub-team | Owned by CLI core |
|---|---|
| Service schema (endpoints, params, scopes, identity, risk class, async-handle declarations) | Schema → command compiler |
| `skills/mycli-<service>-<purpose>/` — SKILL.md and references/ | Skill validator, install/update/doctor machinery |
| Service-specific shortcuts in `src/mycli/shortcuts/<service>/` (optional) | Three-layer command architecture, envelope contract |
| Credential provider extension (when service auth differs from default) | Credential provider Protocol + chain executor |
| Service ADR in `docs/decisions/` | Core ADRs |

## Onboarding steps

### 1. File a service ADR

Create `docs/decisions/NNNN-<service>.md` documenting:
- Service owner and escalation channel
- Safety boundaries (what can go wrong, what is irreversible)
- Identity and authentication requirements
- Risk classification of each operation family

### 2. Write the SKILL.md

Fork `skills/mycli-skill-template/` → `skills/mycli-<service>-<purpose>/`.

Required frontmatter fields: `name`, `description` (with `TRIGGER when:`
and `DO NOT TRIGGER when:` markers), `maintainer`.

Required body sections:
- "CRITICAL — read `../mycli-shared/SKILL.md` first"
- Commands (shortcuts → schema-compiled → raw API)
- Identity & permission table
- Common AI failure modes

### 3. Define the service schema

Describe each endpoint:
- Path, method, parameters
- Risk class (`read` / `write` / `high-risk-write` / `destructive-cost`)
- Identity requirements
- Whether the operation is async (and what handle fields it returns)

### 4. Add shortcuts (optional but recommended)

Hand-written Python in `src/mycli/shortcuts/<service>/` for multi-step
orchestrations that schema-compiled commands cannot express cleanly.

### 5. Add tests

At minimum:
- Contract test: the command returns a valid envelope on success.
- Contract test: the command returns a valid error envelope on failure.
- Risk test: `high-risk-write` commands exit 10 without `--yes`.

### 6. Run the gate checks

```bash
uv run ruff check src tests
uv run mypy --strict src
uv run pytest -q
uv run mycli validate
```

All four must be green before opening a PR.

## Onboarding gates (must be satisfied before merge)

- [ ] Service owner / maintainer named in SKILL.md frontmatter and ADR
- [ ] Read / write / high-risk-write / destructive-cost operations distinguished via `risk`
- [ ] Mutating and destructive operations exhibit the `--yes` / exit 10 behavior
- [ ] Identity and scope requirements documented in the SKILL.md
- [ ] Tests or manual verification steps defined
- [ ] `mycli validate` exits 0

## See also

- [`skills/mycli-skill-template/SKILL.md`](../../skills/mycli-skill-template/SKILL.md) — fork starting point
- [`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md) — normative spec
- [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md) — shared runtime protocol
