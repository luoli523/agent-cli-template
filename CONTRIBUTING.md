# Contributing to di-cli

`di-cli` is a shared DI Toolkit. Contributions should make DI development, service ownership, on-call work, or platform operations easier for other DI engineers.

This repository is still in its scaffold stage. Contributions must be conservative, explicit about ownership, and safe to review.

## Contribution Types

Supported contribution areas:

- `skills/`: DI workflows, service operations, troubleshooting playbooks, and helper scripts for AI assistants.
- `agents/`: focused assistant agents (currently empty placeholder; see `agents/README.md`).
- `docs/services/`: service owner docs, API notes, onboarding guides, and operational runbooks.
- `mcp/`: MCP server patterns (currently empty placeholder; see `mcp/README.md`). First contribution requires a reviewed ADR.
- `config/`: templates for profiles, prefixes, and credentials. Templates only.
- `scripts/`: repository maintenance, validation, install, and doctor utilities.
- `contexts/` and `rules/`: optional assistant behavior presets and always-follow rules (currently empty placeholders; see each directory's `README.md`).

If a contribution does not fit one of these areas, write a short proposal in `docs/decisions/` before implementing it.

## Required Ownership

Every service-specific contribution must name an owner or maintainer.

Use a team alias or company email that can answer questions about:

- expected workflow
- authentication and permission requirements
- data sensitivity
- side effects
- failure modes
- test or verification strategy

Unowned service integrations should not be merged.

## Required Workflow

1. Define the contribution scope.
2. Identify the owner and affected service area.
3. Document authentication, safety boundaries, and side effects.
4. Add or update validation checks when changing contribution rules.
5. Run local validation before requesting review.
6. Keep each change reviewable. If a change touches more than three files, split it into smaller batches unless the reviewer explicitly approves the larger change.

## Local Validation

Python dependencies are managed with `uv`. Run this once after cloning or whenever `pyproject.toml` / `uv.lock` changes:

```bash
uv sync
```

The validation entrypoint is:

```bash
bash scripts/validate.sh
```

The validation script uses `.venv/bin/python`, which is created by `uv sync`. It does not install dependencies automatically.

Do not claim validation has passed unless the relevant checks were actually run.

## Continuous Integration

GitLab CI runs the same checks on every merge request and on every push to `main`. The pipeline is defined in `.gitlab-ci.yml` and uses `python:3.13-slim`. Locally reproduce a CI failure with:

```bash
uv sync --frozen --extra dev
bash scripts/validate.sh
uv run pytest tests/ -q
```

If `bash scripts/validate.sh` or `uv run pytest tests/` fails locally, the pipeline will fail too. Fix the issue locally — do not push hoping the remote behaves differently.

## Skills

A real skill must live at `skills/<name>/SKILL.md`.

Minimum requirements:

- `name` matches the directory name.
- `maintainer` is present and non-empty.
- `description` explains what the skill does.
- `description` includes `TRIGGER when:` and `DO NOT TRIGGER when:`.
- The body explains the workflow the assistant should follow.
- Detailed references live under `skills/<name>/references/`.
- Helper scripts live under `skills/<name>/scripts/`.

Skill names must be kebab-case and service-oriented, such as `datamap-lineage` or `scheduler-task-debug`.

## Agents

Agents live at `agents/<name>.md`.

Minimum requirements:

- `name` is kebab-case.
- `description` states when the agent should be used.
- The body defines the agent's role, process, and output format.
- Prefer `readonly: true` unless the agent must edit files.
- Tool access must match the job. Do not grant broad write or shell access without a written reason.

## Service Documentation

Service docs live at `docs/services/<service>.md`.

Each service doc should include:

- owner or maintainer
- service purpose
- common user workflows
- authentication and permission model
- safe read-only operations
- mutating or destructive operations, if any
- known failure modes
- test or verification notes

## MCP Contributions

`mcp/` is the MCP staging area; it is currently an empty placeholder.

Before adding a real MCP server or real production service integration, first write a design note that covers:

- tool list and user workflows
- authentication and identity propagation
- side effects for each tool
- confirmation requirements
- error response shape
- pagination, truncation, and rate limits
- local run and test plan

## Configuration

Files in `config/` must be templates only. Use placeholders such as:

```json
{
  "token": "<fill-me>",
  "client_id": "<google-oauth-client-id>"
}
```

Do not include real values, even if they are read-only.

## Prohibited Content

Never commit:

- real tokens, cookies, private keys, passwords, or OAuth refresh tokens
- personal local paths such as `/Users/<name>/...` inside reusable scripts or config
- production-only secrets
- generated credential caches
- unowned service integrations
- scripts that mutate production state without explicit confirmation behavior
- docs that describe planned commands or integrations as already available

## Review Expectations

Reviewers should check:

- the owner is clear
- the contribution fits the repository structure
- user-facing docs match implemented behavior
- safety boundaries are explicit
- validation was run or the missing validation is explained
- no credentials or personal environment assumptions are present

Contribution rules are part of the product. If you change the rules, update the docs and validator in the same approved batch.

## Git Hooks (Optional)

The `.githooks/` directory contains a `pre-commit` hook that runs `bash scripts/validate.sh` before every commit. It is **opt-in** — git does not load it automatically.

To enable:

```bash
git config core.hooksPath .githooks
```

To disable:

```bash
git config --unset core.hooksPath
```

If `.venv` is not present when the hook runs, it prints a warning and exits 0 (does not block the commit). Run `uv sync` to enable the full check.

Do not use `git commit --no-verify` to bypass the hook. If the hook fails, fix the root cause and recommit.
