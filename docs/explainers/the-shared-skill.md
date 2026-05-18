# The shared skill — what it is, who reads it, why it exists

This document explains the artifact `skills/mycli-shared/SKILL.md` — what
it is, who consumes it, and how other skills relate to it. It does *not*
duplicate the skill's content; for the actual rules an agent follows, open
the skill directly.

If you are an AI agent loaded with mycli skills, you do not need this
document — read [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md) directly.

## What it is

`mycli-shared` is a skill — Markdown + YAML frontmatter — that teaches AI
agents how to consume the CLI's operating protocol: envelope shape, exit
codes, error recovery, the `_notice` channel, the `exit 10` confirmation
gate, and identity sanity-check.

It is the **implicit dependency of every other `mycli-*` skill**. Every
service skill begins by saying "CRITICAL — read `../mycli-shared/SKILL.md`
first", then only documents its own service-specific concerns.

## Who reads it

| Reader | When |
|--------|------|
| **AI agent** | At runtime, before invoking any `mycli` command. Primary and intended consumer. |
| Sub-team contributor | Once, while learning the protocol — to understand what their service skill must defer to. |
| Reviewer | When auditing a skill PR — to check the skill doesn't redefine shared rules. |

## What it is NOT

- **Not a specification.** The normative spec is `docs/specs/2026-05-18-agent-cli-protocol.md`.
  When they conflict, the spec wins.
- **Not a service skill.** It teaches no service-specific commands.
- **Not installed as a separate skill at runtime.** It is installed along with all other
  `mycli-*` skills by `mycli install`; agents read it as part of their context load.

## The relationship between mycli-shared and service skills

```
mycli-shared/SKILL.md
  ↑ "read first" dependency
  │
  ├── mycli-<service-a>/SKILL.md
  ├── mycli-<service-b>/SKILL.md
  └── mycli-<service-c>/SKILL.md
```

Service skills are **additive**: they document what is unique about their
service (commands, identity, scopes, failure modes) without repeating the
shared protocol. This keeps service skills short and prevents the shared
rules from silently diverging across skills.

## When to update mycli-shared

Update `mycli-shared/SKILL.md` when:
- The envelope shape changes (contract change — requires approval).
- A new exit code or error type is added.
- A new standard flag is added.
- A new cross-cutting failure mode is discovered in production.

Do **not** add service-specific content to `mycli-shared`.

## See also

- [`docs/specs/2026-05-18-agent-cli-protocol.md`](../specs/2026-05-18-agent-cli-protocol.md) — normative spec
- [`skills/mycli-shared/SKILL.md`](../../skills/mycli-shared/SKILL.md) — the skill itself
- [`docs/explainers/onboarding-a-service.md`](onboarding-a-service.md) — how sub-teams build on this
