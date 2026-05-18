# The di-shared skill — what it is, who reads it, why it exists

> **Language**: [English](the-di-shared-skill.md) | [中文](the-di-shared-skill.zh-CN.md)

This document explains the **artifact** `skills/di-shared/SKILL.md` — what it is, who consumes it, and how sub-teams relate to it. It does *not* duplicate the skill's content; for the actual rules an agent follows, open the skill itself.

If you are an AI agent loaded with di-cli skills, you do not need this document — read [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md) directly.

## What it is

`di-shared` is a skill — Markdown + YAML frontmatter — that teaches AI agents how to consume the di-cli operating protocol: envelope shape, exit codes, error recovery, the `_notice` channel, the `exit 10` confirmation gate, and identity sanity-check. It is the **implicit dependency of every other `di-*` skill**.

Think of it as the cross-service base class: every service skill begins by saying "CRITICAL — read `../di-shared/SKILL.md` first", and then only documents its own service-specific concerns.

## Who reads it

| Reader | When |
|--------|------|
| **AI agent** | At runtime, before invoking any `di` command. This is the primary and intended consumer. |
| Sub-team contributor | Once, while learning what the protocol is — to understand what their service skill must defer to. |
| di-cli maintainer | When updating the protocol contracts, to keep teaching in sync. |

It is **not** a copy-paste source for new skills, and it is **not** the document a human reads to understand *why* the contracts are shaped the way they are — that's [`contracts-for-ai-agents.md`](contracts-for-ai-agents.md).

## Why it exists

The cross-cutting contracts (envelope, exit codes, risk class, `_notice`, identity) are **identical across every service**. Without `di-shared`:

- Every service skill would re-explain the same protocol from scratch.
- Drift between skills would be inevitable — one would say "exit 10 means X", the next would say something subtly different.
- Updating the protocol would mean editing N skills instead of one.

`di-shared` solves this by being the **single teaching point**. Service skills link to it; they do not duplicate it. Update the protocol → update one file → every skill propagates the change by reference.

## What's in it

The skill ships 13 sections. Use this as a table of contents to decide which to consult; open the file itself for the actual content.

| Section | One-line summary |
|---------|------------------|
| CRITICAL — first actions | Read this skill before any `di` call; default to `--format json`. |
| Envelope contract | success / error envelope shapes; `stdout = data, stderr = everything else`. |
| Exit code → action | Lookup table mapping each exit code to the recovery move. |
| Error.type catalogue | Coarse classification — `validation`, `permission`, `auth`, etc. — and the recovery strategy per type. |
| Permission errors — recovery protocol | Read `permission_violations` + `hint`; pass `console_url` verbatim. |
| exit 10 protocol | The most-violated rule. Confirmation gate behavior + an explicit *forbidden* list. |
| `_notice` protocol | Out-of-band signals; never interrupt the current task; address afterwards. |
| Identity (`--as`) — sanity check | `identity` echoed in every envelope is the lens-confirmation anchor. |
| Three-layer command surface | Shortcut > resource.method > raw `di api`; preference order for agents. |
| Available infrastructure commands (v0.2) | Table of the five v0.2 commands and their risk classes. |
| Common AI failure modes | Accumulating registry of observed agent mistakes. F-001 seeded; more added as observed. |
| When to stop and ask the user | Default-to-confirm checklist. |
| Glossary | Envelope / identity / risk / handle / `_notice` / manifest. |

## How sub-teams interact with it

Three rules.

1. **Link, don't duplicate.** Every new skill begins with a `CRITICAL — read ../di-shared/SKILL.md first` notice. Do not paste protocol rules into the new skill — they will drift.
2. **Defer to its terminology.** If your service has a concept that overlaps with envelope / identity / risk / handle, use the terms `di-shared` uses. Inventing new vocabulary fragments the agent's mental model.
3. **If you need a rule that contradicts di-shared, file an ADR.** Do not fork the rule into your skill. The protocol surface is governed (see [`CLAUDE.md`](../../CLAUDE.md) § Project Boundaries) — a contract change is a project-level decision, not a skill-level one.

## How it stays accurate

Three mechanisms keep `di-shared` honest:

- **Source-of-truth pinning.** The contracts it teaches are defined in [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Cross-cutting contracts. Changes to envelope shape, exit codes, error types, handle structure, or risk classification require explicit approval per CLAUDE.md.
- **Structural validation.** T8's `di validate --scope skills` runs on every MR (and locally) and rejects skills whose SKILL.md frontmatter or body shape regresses. di-shared is no exception.
- **Live-repo regression gate.** `tests/core/test_validate.py::test_validate_passes_against_live_repo_skills` runs the validator against the actual `skills/di-shared/SKILL.md` shipped in the checkout. Anyone who breaks the contract by editing the file goes red in CI immediately.

## When you'd modify it

Modifications are **rare**. Most additions to "what AI agents should know" belong in service skills, not in di-shared. Legitimate triggers:

- **A new cross-cutting AI failure mode** is observed in real production traces — add a new `F-N` entry under "Common AI failure modes". This is the most common reason to touch the file.
- **A new contract field ships** (e.g. spec adds a new `_notice` type) — propagate the teaching to di-shared.
- **A protocol field is renamed or removed** — update di-shared as part of the same MR that renames the contract.

Avoid:

- Adding service-specific guidance — that belongs in the relevant service skill.
- Adding examples that only make sense for one service — same reason.
- Rewriting in personal style — the file is consumed by AI agents, not humans optimizing for prose flow.

## The "Common AI failure modes" accumulation pattern

The long-term value of `di-shared` is not the protocol summary — that's a one-time write. It's the **accumulating list of observed AI failure modes**. Every time an agent makes a class of mistake against di-cli that *applies across services*, the fix is one new F-N entry here.

The pattern for each entry:

- **Symptom** — what the agent does wrong (concrete behavior, not vague description).
- **Why it is wrong** — the violated constraint, in plain language.
- **Correct behavior** — exactly what the agent should do instead.
- **Spotting it in review** — what a reviewer looks for in transcripts to recognize this failure.

The rule when contributing: **add, don't replace**. The list is the institutional memory of what AI agents get wrong with di-cli. An old failure that has been fixed in newer models is still worth keeping — agents downgrade, regressions happen, and the entry serves as documentation for "we tried this once".

F-001 (auto-retrying `exit 10` with `--yes`) is the seeded example. Use it as the format model when you add F-002.

## Relationship to other docs

Four documents touch this area; the table makes their roles explicit so you can pick the right one for any given question.

| Document | Audience | Answers |
|----------|----------|---------|
| [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Cross-cutting contracts | Project maintainers | *What* the contracts are (normative). |
| [`docs/explainers/contracts-for-ai-agents.md`](contracts-for-ai-agents.md) | Engineers learning the project | *Why* the contracts are shaped this way. |
| **This document** | Sub-team contributors; anyone asking "what is `di-shared`?" | What the `di-shared` artifact is and how to relate to it. |
| [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md) | **AI agents** | How to consume the protocol at runtime. |

## See also

- The skill itself: [`skills/di-shared/SKILL.md`](../../skills/di-shared/SKILL.md)
- Contracts design rationale: [`docs/explainers/contracts-for-ai-agents.md`](contracts-for-ai-agents.md)
- Normative protocol spec: [`docs/specs/2026-05-15-di-cli-architecture.md`](../specs/2026-05-15-di-cli-architecture.md) § Cross-cutting contracts
- Sub-team onboarding flow: [`docs/explainers/onboarding-sub-team.md`](onboarding-sub-team.md)
- Skill template: [`skills/di-skill-template/README.md`](../../skills/di-skill-template/README.md)
- Command reference (human-readable catalogue): [`docs/reference/commands.md`](../reference/commands.md)
