---
name: di-skill-template
description: >
  Template for new di-* skills. NOT a runtime teaching aid — di-cli
  install/update intentionally skip this directory. Sub-teams fork
  this directory, rename it, and replace every <replace-me> with real
  content.
  TRIGGER when: a sub-team is creating a new di-* skill and needs a
  compliant starting point.
  DO NOT TRIGGER when: an AI agent is running di-cli commands — this
  skill teaches nothing about runtime behavior. Read ../di-shared/
  SKILL.md for runtime protocol.
maintainer:
  - li.luo@shopee.com
version: 0.2.0
metadata:
  requires:
    bins: ["di"]
  cliHelp: "di --help"
---

# di-skill-template

> **HEAD CONTRIBUTORS READ THIS FIRST**: this file *is* the template.
> Fork the whole directory, rename it to `di-<service>-<purpose>`,
> then walk top-to-bottom and replace every `<replace-me>` and
> bracketed instruction. The framing is correct as a model; the
> business content is yours to fill.
>
> Run `di validate --scope skills` after editing to confirm your fork
> still passes the gate.

## CRITICAL — first action for any agent loading this skill's clone

(Keep this section as-is when forking, only changing `<service>`.)

**Read [`../di-shared/SKILL.md`](../di-shared/SKILL.md) before invoking
any `di` command.** Envelope contract, exit-code policy, exit-10
confirmation gate, `_notice` protocol, and identity sanity-check all
live there. This file does not repeat them.

## Trigger summary

<replace-me — one or two sentences that name the user-visible problem
this skill solves. The frontmatter `description` is the machine-facing
trigger; this prose is for human contributors who scan the file. Keep
it specific, not "various tasks related to X".>

Example for a hypothetical `di-datamap-lineage` fork:

> Look up table lineage, owners, and governance hints in DataMap.
> Triggered by user mentions of "DataMap", "lineage", "table owner",
> or "血缘".

## Prerequisites

- [`../di-shared/SKILL.md`](../di-shared/SKILL.md) — runtime protocol
- `<replace-me — list any other di-* skill this one depends on, e.g.
  ../di-ram-permissions/SKILL.md when permission resolution needs it>`
- `<replace-me — list the RAM scopes the agent needs before invoking
  this skill's commands, e.g. datamap:lineage:read>`

## Key concepts

(Anchor the user's spoken language to the canonical service terms.
DataMap calls them "tables", Scheduler calls them "jobs", DQC calls
them "rules" — agents need explicit mappings so they don't shadow
each other's vocabulary.)

- **`<service-term-1>`** — `<replace-me — definition and how it maps
  to common user phrasing>`
- **`<service-term-2>`** — `<replace-me>`

## Commands

### Shortcuts (preferred when one exists)

```bash
# <replace-me — list the +verbs this service ships, one per row. Skip
# this whole subsection if the service has no shortcuts yet.>
di <service> +<verb> [flags]
```

See [`references/example-workflow.md`](references/example-workflow.md)
for a worked end-to-end shortcut walkthrough. Delete the example
under references/ and replace with real workflow docs.

### Schema-compiled commands

```bash
# 1. Discover the parameter shape first — never guess fields.
di schema <service>.<resource>.<method>

# 2. Then invoke.
di <service> <resource> <method> [flags]
```

### Raw API (escape hatch)

Use only when neither a shortcut nor a compiled command covers the
case. Same envelope rules apply.

```bash
di api <service> <METHOD> <path> [--data ...] [--params ...]
```

## Identity & permission

| Identity | Required for | Notes |
|----------|--------------|-------|
| `<replace-me — user/bot/auto>` | `<replace-me — which commands>` | `<replace-me — why this identity>` |

Required RAM scopes (sub-team owners: keep this current — agents
parse it):

- `<replace-me — scope-1>` — `<replace-me — what it grants>`
- `<replace-me — scope-2>` — `<replace-me>`

## Common AI failure modes

(Accumulate observed agent mistakes here. Each entry must include
symptom, root cause, correct behavior, and how to spot it in
transcripts. F-001 below is the format model — replace the content
when you observe the first real failure in your service.)

### F-001 — <replace-me — short failure name>

**Symptom**: `<replace-me — what the agent does wrong>`

**Why it is wrong**: `<replace-me — the actual constraint being
violated>`

**Correct behavior**: `<replace-me — the action the agent should take
instead>`

**Spotting it in review**: `<replace-me — what to look for in agent
transcripts that reveals this failure>`

## See also

- Runtime protocol: [`../di-shared/SKILL.md`](../di-shared/SKILL.md)
- Architecture spec: [`../../docs/specs/2026-05-15-di-cli-architecture.md`](../../docs/specs/2026-05-15-di-cli-architecture.md)
- Sub-team onboarding guide: [`../../docs/explainers/onboarding-sub-team.md`](../../docs/explainers/onboarding-sub-team.md)
- Service ADR: `<replace-me — link to docs/decisions/NNNN-<service>.md once filed>`
