# Onboarding a sub-team into di-cli

> **Language**: [English](onboarding-sub-team.md) | [中文](onboarding-sub-team.zh-CN.md)

This guide walks a DI sub-team from "we have a service we want to expose to AI agents" to "our skill is merged and our service has a `di <service>` command surface". It assumes you've already read:

- [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) — what di-cli is
- [`docs/explainers/contracts-for-ai-agents.md`](contracts-for-ai-agents.md) — why the contracts are shaped this way
- [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md) — the runtime protocol every skill inherits

If those concepts are new, read those first. This guide is the *procedural* layer on top.

## What a sub-team owns vs what di-cli owns

| Owned by sub-team | Owned by di-cli core |
|---|---|
| Service schema (endpoints, params, scopes, identity, risk class, async-handle declaration) | Schema → command compiler |
| `skills/di-<service>-<purpose>/` — SKILL.md and references | Skill validator, install/update/doctor machinery |
| Service-specific shortcuts in `src/di/shortcuts/<service>/` (when needed) | Three-layer command architecture, envelope contract |
| Service ADR under `docs/decisions/` | Cross-cutting contracts, exit codes, `_notice`, risk |
| RAM scope catalogue for the service | Credential provider chain interface |

The split exists so a sub-team only has to think about *its service*. The protocol surface (envelope shape, error types, exit codes, `_notice`, `--yes` gate) is fixed by di-cli core and never re-negotiated per service.

## The 6-step flow

### 1. File a service ADR

Open `docs/decisions/NNNN-<service>.md` (next sequential number). It captures decisions the spec doesn't dictate:

- Service owner and on-call escalation channel
- Identity model: which RAM roles or scope groups apply, default `--as`, whether `bot` is supported
- Risk classification for known operations: which are `read` vs `write` vs `high-risk-write` vs `destructive-cost`
- Async-handle policy: which operations return handles, how the agent should poll
- Cost / quota story (Group A engines especially)
- Schema source of truth (where the API definitions live; how they're refreshed)

Get the ADR reviewed before writing code. The conversation it forces is the point.

### 2. Deliver the schema

Drop a schema file under `<repo>/schemas/<service>.<format>`. v0.2 has not finalized the schema format — when your sub-team is the first real integration, you co-design it with di-cli core. Likely candidates: OpenAPI 3, a lightweight YAML, or a service-specific descriptor.

The schema is the source of truth for the auto-registered command tier (`di <service> <resource> <method>`). It must declare per-method:

- `risk` (`read` / `write` / `high-risk-write` / `destructive-cost`)
- `identity_required` and supported `--as` values
- `scopes` (RAM scope names)
- async handle declaration if applicable

### 3. Fork the skill template

Follow [`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md):

```bash
cp -r skills/di-skill-template skills/di-<service>-<purpose>
```

Edit frontmatter, fill every `<replace-me>` in the SKILL.md body, populate `references/` with one workflow doc per shortcut you ship. The template README has a compliance checklist — go through it before requesting review.

### 4. (Optional) Write hand-curated shortcuts

If your service has multi-step flows the agent should treat as one operation (the canonical example is feishu-cli's calendar `+create` orchestrating `+room-find` + `+freebusy` + `+suggestion`), implement them as Python shortcuts under `src/di/shortcuts/<service>/`. Conventions:

- One module per `+verb`
- Shortcut returns the same envelope shape as schema commands (no special-casing)
- Risk class declared at registration time
- Dry-run is mandatory (`--dry-run` prints the request and returns)

If the operation is genuinely one-call, skip the shortcut layer — the schema-compiled command already covers it. **Don't write shortcuts as wrappers** that re-expose schema methods with no added value.

### 5. (Optional) Extend the credential provider chain

di-cli's default credential provider handles Google OAuth via the standard `--as user` flow. If your service has a non-standard auth model (service account, sidecar daemon, vault integration, etc.), implement a `CredentialProvider` and register it. This is rare — most services should reuse the default.

### 6. Test, validate, ship

Before opening the MR:

```bash
# 1. Skill self-checks against the validator
di validate --scope skills

# 2. Whole-repo audit (your skill must keep the repo healthy)
di validate

# 3. Local install dry-run — confirm install picks up the new skill
di install --dry-run

# 4. Manifest includes new commands (if you added Python shortcuts)
di --manifest

# 5. Python tests pass
uv run pytest -q
```

Open the MR with:

- Title: `feat(skills): add <service> skill and shortcuts`
- Body: link the service ADR, summarize identity / scope decisions, list `+verbs` shipped, list known limitations
- Reviewer: a di-cli maintainer plus your service owner

## Merge gates

Before approval, a reviewer confirms:

- Service owner + on-call channel named in SKILL.md frontmatter and the ADR
- Risk class is declared for every method (no `unknown`)
- Mutating and destructive operations exercise the `--yes` confirmation gate (exit 10 protocol)
- Identity requirements documented; `--as` examples reflect reality
- At least one entry under "Common AI failure modes" or an explicit "no failures observed yet" note
- Tests pass and `di validate` returns healthy
- Skill follows the di-shared protocol — does not duplicate or contradict di-shared content

## After merge: maintenance

A skill is a living document. Add a new "Common AI failure modes" entry every time an agent makes a class of mistake in production with your service. This accumulation is the long-term value — the skill becomes the institutional memory of what AI agents get wrong, and how to head them off.

Avoid `skills/<name>/SKILL.md` ballooning past ~500 lines. When that's about to happen, split topic-specific guidance into `references/` files, keeping the main SKILL.md as the entry index.

## When in doubt

- Protocol questions (envelope shape, exit codes, `--yes` semantics) → re-read [`docs/explainers/contracts-for-ai-agents.md`](contracts-for-ai-agents.md). If the protocol genuinely doesn't cover your case, that's a di-cli core ADR, not a sub-team decision.
- Skill style questions → look at [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md) and existing service skills.
- "Should I add a shortcut?" → write it the slow way first (schema-compiled commands the agent composes). Only promote to a shortcut when the same multi-step orchestration repeats in real agent traces.

The fastest path to a successful sub-team contribution is: small skill, one shortcut, ADR reviewed early. Big upfront skills with many shortcuts before the first real agent usage tend to be wrong in ways that show up only after release.
