# ADR-0001: Scaffold-First Strategy for di-cli

Date: 2026-05-15
Status: Accepted
Author: li.luo@shopee.com

## Context

di-cli is the shared DI Toolkit — a skill/agent/rule distribution system for Data Infra AI coding assistants (Claude Code, Codex). The repository was initialised with a bare directory skeleton, a validator, and a CONTRIBUTING guide, but had no actual convention documentation, no sample agents or contexts, and no enforcement mechanisms (git hooks).

Several paths were available:

1. **Jump straight to real skill integrations** — add `skills/datamap-lineage/`, `skills/scheduler-task-debug/`, etc. with live API calls.
2. **Ship a CLI first** — implement `di install`, `di doctor`, and the symlink machinery before any knowledge content.
3. **Scaffold-first** — lock down conventions, samples, validator, and git hooks before adding any real service integration.

Option 1 risks creating unowned, untested, or credential-leaking service integrations before governance is in place. Option 2 ships infrastructure with nothing to install. Option 3 builds the review surface and ownership model first, so every subsequent real contribution has a clear gate to pass through.

The spec driving this work is [`docs/specs/2026-05-14-scaffold-completion.md`](../specs/2026-05-14-scaffold-completion.md).

## Decision

Adopt the scaffold-first strategy. Before any real service integration or CLI implementation lands, the repository must have:

- Per-subdirectory READMEs that make conventions discoverable without reading source code.
- A single source of truth for naming prefixes (`config/prefixes.json`) referenced by the validator.
- Sample agents (`planner`, `code-reviewer`), contexts (`dev`, `review`, `oncall`), and a rule (`git-workflow`) that demonstrate the expected format and can be used immediately.
- A validator that checks prefix, description length, and agent frontmatter types — not just structural presence.
- An opt-in pre-commit hook that runs the validator locally.
- Governance files: `CHANGELOG.md`, `CODEOWNERS`, and this ADR.

Real service integrations may land after this baseline, provided each one satisfies the contribution gates in `CLAUDE.md` and `CONTRIBUTING.md` (owner named, auth documented, side effects classified, test plan defined).

## Consequences

**Positive:**

- New contributors have a clear, machine-checked path to a valid PR.
- The validator is the single enforcement point; conventions are not just aspirational.
- Sample agents and contexts are immediately usable by any DI engineer with Claude Code or Codex.
- The prefix taxonomy is extensible: adding a new team prefix requires only a `docs/decisions/` entry and a `config/prefixes.json` update.

**Negative / trade-offs:**

- No real skills ship in v0.1.0. Engineers who hoped to use di-cli for live service queries must wait for individual skill contributions.
- The `di` CLI (install, doctor, auth) is fully planned but not implemented. Users must symlink skills and agents manually until the CLI lands.
- `policy.enforce: "warn"` for prefixes means the validator does not yet block non-`di-` skill names. This will be tightened once the prefix taxonomy stabilises.

## What This ADR Does Not Decide

- The design of the `di` CLI (a separate decision record will cover install paths, auth model, and update strategy).
- Which services get skills first (those decisions belong to the service owners and will be tracked via contribution proposals in `docs/decisions/`).
- Whether to support Cursor (currently out of scope; revisit once Claude Code + Codex usage is established).
