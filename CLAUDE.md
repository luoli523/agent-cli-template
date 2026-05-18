# agent-cli-template Project Instructions

This is a scaffold for building agent-facing CLIs. After running `init.py`,
this file describes the AI assistant guidance for your specific CLI project.

These instructions are shared by Claude Code and Codex. `AGENTS.md` must
remain a symlink to this file.

## Primary Consumer

AI Agent. Every command's output, error message, and exit code is parsed by
a machine to decide its next action. Human engineers are a secondary consumer
who fall back to `--format pretty` when reading directly.

## Working Rules

1. Before writing code or changing project structure, describe the approach and wait for approval.
2. If requirements are ambiguous, ask clarifying questions before editing files.
3. For bugs, write or identify a reproducing test before fixing the behavior.
4. After code changes, list important edge cases and suggest tests.
5. If corrected by the user, state what was wrong and how the next attempt will avoid the same issue.

## Project Boundaries

- Do not add runtime dependencies beyond stdlib + PyYAML + keyring without approval.
- Do not implement real service calls until the relevant service ADR is reviewed.
- Do not implement authentication / OAuth / token storage until the credential provider chain interface is frozen.
- Do not change the envelope, exit-code, or handle schema — these are the frozen protocol surface; contract change requires explicit approval.
- Do not implement production MCP servers before the sample pattern and safety rules are agreed.
- Do not split assistant instructions across competing root files; update `CLAUDE.md` and keep `AGENTS.md` linked to it.

## Directory Responsibilities

```text
src/mycli/          Python CLI source.
  contracts/        Envelope, exit codes, error types, handle, risk classification.
  credential/       Credential provider Protocol + chain executor.
  runtime/          Standard flag plumbing, output layer, --watch/--follow/--timeout.
  shortcuts/        Per-service hand-written shortcuts.
  commands/         Schema-compiled commands.
  api/              Raw API escape hatch.
  core/             install / update / doctor / validate / version / hello.
  compiler/         Schema → command registration.
  manifest/         Surface map emitter.
skills/             AI teaching layer (Markdown).
  mycli-shared/     Runtime protocol; every other skill inherits it.
  mycli-skill-template/ Fork target for sub-teams.
  mycli-<service>/  Per-service skill.
docs/
  specs/            Normative spec.
  decisions/        Architecture Decision Records.
  explainers/       Teaching docs.
  reference/        Lookup tables.
tests/
  contracts/        Envelope / exit-code / handle / risk contract tests.
  runtime/          --watch / --follow / pagination / --timeout behavior.
```

## Cross-Cutting Contracts (Protocol Surface)

The protocol surface is frozen: envelope schema, exit codes, error types,
handle envelope, risk classification, `_notice` channel. These are the
contract with AI agents.

Any change to envelope, exit codes, or handle structure is a contract change
and requires explicit approval.

## Three-Layer Command Architecture

```
mycli <service> +<verb>                Curated shortcut — high-level, smart defaults
mycli <service> <resource> <method>    Compiled from service schema — 1:1 platform API
mycli api <service> <METHOD> <path>    Raw escape hatch — any endpoint, no curation
```

AI prefers the highest level; degrades only when forced.

## Skills

**Skills do not execute.** They teach AI how to use CLI commands.

Skills live directly under `skills/<name>/`. Nested skill directories are not
allowed because AI tools discover only the first directory level.

All skill names must start with the configured `skill_prefix`
(default: `mycli-`, set in `pyproject.toml [tool.agent-cli]`).

Each real skill must include `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: mycli-<service>-<purpose>
maintainer:
  - owner@example.com
description: >
  <Service> skill — <what it does>.
  TRIGGER when: <user phrases that should activate this skill>.
  DO NOT TRIGGER when: <cases where this skill does not apply>.
---
```

Every service skill begins with `CRITICAL — first read ../mycli-shared/SKILL.md`.
The "Common AI Failure Modes" section is required.

## Validation Expectations

Before opening a PR, run the same checks CI runs:

```bash
uv run ruff check src tests   # lint
uv run mypy --strict src      # types
uv run pytest -q              # tests
uv run mycli validate         # repo + skills conventions
```

`mycli validate` emits the standard envelope on stdout (healthy / degraded)
or stderr (unhealthy). Walk the `checks` list when a step is not `ok`.

## Naming

Use kebab-case for skill / agent / decision filenames.

All skill names must start with the configured `skill_prefix`. Prefer
service-oriented names:

- `mycli-<service>-<purpose>`
- `mycli-scheduler-task-debug`
- `mycli-auth-permission-debug`

Use clear nouns before actions. Avoid vague names like `helper`, `tool`, `misc`.

## Boundaries

### Always do

- Output JSON envelope from every command (including errors)
- Declare `risk` and identity requirements in every command's schema
- Return `handle` envelopes from any async operation
- Return structured errors with `hint` whenever a remediation exists
- Test envelope / exit-code / handle / risk contracts

### Ask first

- Adding runtime dependencies
- Adding the first real service integration
- Implementing OAuth / token storage
- Changing envelope, exit-code, or handle schema (contract change!)

### Never do

- Commit secrets, tokens, refresh tokens
- Silently bypass `--yes` (exit 10) protocol
- Have a skill execute API calls — skills teach, they don't run
- Default to `--format pretty` (agents aren't the primary consumer)
