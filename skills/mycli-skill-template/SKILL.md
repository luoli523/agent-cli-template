---
name: mycli-skill-template
description: >
  Template for new mycli-* skills. NOT a runtime teaching aid — mycli
  install/update intentionally skip this directory. Fork this directory,
  rename it, and replace every <replace-me> with real content.
  TRIGGER when: a sub-team is creating a new mycli-* skill and needs a
  compliant starting point.
  DO NOT TRIGGER when: an AI agent is running mycli commands — this
  skill teaches nothing about runtime behavior. Read ../mycli-shared/
  SKILL.md for runtime protocol.
maintainer:
  - maintainer@example.com
version: 0.1.0
metadata:
  requires:
    bins: ["mycli"]
  cliHelp: "mycli --help"
---

# mycli-skill-template

> **CONTRIBUTORS READ THIS FIRST**: this file *is* the template.
> Fork the whole directory, rename it to `mycli-<service>-<purpose>`,
> then walk top-to-bottom and replace every `<replace-me>` and
> bracketed instruction.
>
> Run `mycli validate --scope skills` after editing to confirm your fork
> still passes the gate.

## CRITICAL — first action for any agent loading this skill's clone

(Keep this section as-is when forking, only changing `<service>`.)

**Read [`../mycli-shared/SKILL.md`](../mycli-shared/SKILL.md) before
invoking any `mycli` command.** Envelope contract, exit-code policy,
exit-10 confirmation gate, `_notice` protocol, and identity sanity-check
all live there. This file does not repeat them.

## Trigger summary

<replace-me — one or two sentences that name the user-visible problem
this skill solves. The frontmatter `description` is the machine-facing
trigger; this prose is for human contributors who scan the file.>

## Prerequisites

- [`../mycli-shared/SKILL.md`](../mycli-shared/SKILL.md) — runtime protocol
- `<replace-me — list any other mycli-* skill this one depends on>`
- `<replace-me — list required auth scopes before invoking commands>`

## Key concepts

- **`<service-term-1>`** — `<replace-me — definition and user phrasing>`
- **`<service-term-2>`** — `<replace-me>`

## Commands

### Shortcuts (preferred when one exists)

```bash
mycli <service> +<verb> [flags]
```

See [`references/example-workflow.md`](references/example-workflow.md)
for a worked end-to-end shortcut walkthrough.

### Schema-compiled commands

```bash
# 1. Discover the parameter shape first — never guess fields.
mycli schema <service>.<resource>.<method>

# 2. Then invoke.
mycli <service> <resource> <method> [flags]
```

### Raw API (escape hatch)

```bash
mycli api <service> <METHOD> <path> [--data ...] [--params ...]
```

## Identity & permission

| Identity | Required for | Notes |
|----------|--------------|-------|
| `<replace-me>` | `<replace-me>` | `<replace-me>` |

## Common AI failure modes

### F-001 — <replace-me — short failure name>

**Symptom**: `<replace-me>`

**Why it is wrong**: `<replace-me>`

**Correct behavior**: `<replace-me>`

**Spotting it in review**: `<replace-me>`

## See also

- Runtime protocol: [`../mycli-shared/SKILL.md`](../mycli-shared/SKILL.md)
- Architecture spec: [`../../docs/specs/2026-05-18-agent-cli-protocol.md`](../../docs/specs/2026-05-18-agent-cli-protocol.md)
- Onboarding guide: [`../../docs/explainers/onboarding-a-service.md`](../../docs/explainers/onboarding-a-service.md)
- Service ADR: `<replace-me — link to docs/decisions/NNNN-<service>.md once filed>`
