# Contribution Governance Overview

This document defines the contribution governance model for `di-cli`. It is the stable reference for what contributors must provide before new DI Toolkit capabilities are accepted.

## Governance Goals

- Make contributions self-service for DI service teams.
- Keep ownership clear for every service-specific capability.
- Prevent credentials, unsafe production actions, and undocumented workflows from entering the repository.
- Keep Claude Code and Codex behavior aligned through the shared `CLAUDE.md` instruction source.
- Make local checks reusable by future CI.

## Contribution Areas

| Area | Purpose | Required Owner |
| --- | --- | --- |
| `skills/` | On-demand DI workflows and operational knowledge | Yes, for every real skill |
| `agents/` | Focused assistant roles with scoped permissions | Yes |
| `docs/services/` | Service owner documentation and runbooks | Yes |
| `mcp/` | MCP samples and future server patterns | Yes for real integrations |
| `config/` | Profiles, prefixes, and credential templates | Yes for schema changes |
| `scripts/` | Repository tooling and validators | Yes |
| `rules/` | Optional always-follow assistant rules | Yes |
| `contexts/` | Optional work-mode prompts | Yes |

## Contribution Lifecycle

```text
proposal or scoped request
  -> owner identified
  -> docs and safety boundaries written
  -> implementation or content added
  -> local validation run
  -> review
  -> merge
```

For service integrations, the owner must be able to explain the service behavior, permissions, side effects, and expected failure modes.

## Required Metadata

Every service-facing contribution should make these fields easy to find:

- owner or maintainer
- service or platform name
- intended users
- read-only operations
- mutating operations
- destructive operations, if any
- authentication model
- test or verification method

Skills and agents carry this metadata in frontmatter plus their body. Service docs carry it in Markdown sections.

## Safety Classes

Use these safety classes when documenting tools, scripts, and MCP operations:

- `read-only`: retrieves data and does not consume meaningful compute or mutate state.
- `consumes-resources`: starts jobs, queries, scans, or workloads that may consume quota or compute.
- `mutates-state`: creates, updates, approves, cancels, or changes service state.
- `destructive`: deletes data, disables resources, removes permissions, or performs irreversible actions.

Mutating and destructive operations must document confirmation behavior before implementation.

## Validation Model

The repository should have one local validation entrypoint:

```bash
bash scripts/validate.sh
```

The entrypoint may delegate to Python scripts, but contributors should not need to remember multiple commands. Future CI should call the same command.

Validation should cover:

- root scaffold integrity
- `AGENTS.md` symlink target
- required directories and docs
- skill frontmatter
- agent frontmatter
- service doc required sections
- suspicious secret patterns
- personal local path leaks
- executable script conventions

When contribution rules change, validation should change with them.

## Review Gates

A contribution is not ready for merge when:

- it has no owner
- it has unclear authentication requirements
- it can mutate production state without documented confirmation behavior
- it includes real credentials or generated auth caches
- it documents unavailable functionality as available
- it bypasses or weakens validation without a reason
- it changes repository structure without an approved design

## Future Detailed Guides

Detailed guides should be added as the repository matures:

- `docs/contribution/skills.md`
- `docs/contribution/agents.md`
- `docs/contribution/services.md`
- `docs/contribution/mcp.md`
- `docs/contribution/config.md`
- `docs/contribution/scripts.md`

Until those files exist, `CONTRIBUTING.md`, this overview, and `CLAUDE.md` are the authoritative contribution references.
