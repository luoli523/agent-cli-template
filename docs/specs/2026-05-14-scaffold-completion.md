# Spec: di-cli Scaffold Completion (Tier 1 + Tier 2)

Status: Approved 2026-05-14
Owner: li.luo@shopee.com

## Objective

Bring `di-cli` from its current state (directory skeleton + basic validator + CONTRIBUTING) to a state where a new contributor can read each subdirectory's README and submit a convention-compliant PR without reading source. Match the governance water-line of `sra-toolkit`, but do not introduce runtime or service-side implementations.

Audience: future DI Toolkit contributors (service owners, on-call, platform engineers), the AI coding assistants that consume the repo (Claude Code, Codex), and the validator itself.

Why now: `CLAUDE.md` and `CONTRIBUTING.md` declare conventions (prefix, frontmatter, bilingual, flat skills layout, ...) but the repo lacks:

- per-subdirectory READMEs that make those conventions discoverable
- a single source of truth for naming prefixes (`config/prefixes.json`)
- git hooks that catch drift before it lands
- any sample agent / context / rule that proves the conventions are real
- governance files (`CHANGELOG.md`, `CODEOWNERS`, `docs/architecture.md`)

Success looks like:

- A newcomer can read READMEs + CONTRIBUTING + samples and submit a compliant skill PR.
- `bash scripts/validate.sh` passes and covers prefix, description length, and agent frontmatter type checks.
- After opting in to `.githooks/`, `pre-commit` rejects convention drift automatically.
- The repo ships at least one sample agent, sample context, and sample rule that work for both Claude Code and Codex.

## Tech Stack

- Python: version per `pyproject.toml`, managed by `uv sync`, executed via `.venv/bin/python`. Only runtime dependency: `PyYAML`.
- Tests: `pytest`. Every new validator rule lands with at least one happy-path and one failure case.
- Shell: `bash` with `set -euo pipefail` for `scripts/` and `.githooks/`.
- Docs: Markdown. User-facing docs ship both `.md` and `.zh-CN.md`; internal technical notes may be English-only.

## Commands

```bash
# One-time
uv sync                                          # install deps and build .venv
git config core.hooksPath .githooks              # opt-in hooks (documented in CONTRIBUTING)

# Daily
bash scripts/validate.sh                         # full convention check
uv run pytest tests/                             # run tests
uv run pytest tests/test_validate_repo.py -k prefix   # focused run

# CI shape (future)
uv sync && bash scripts/validate.sh && uv run pytest tests/
```

## Project Structure (target state, **bold** = new or modified)

```text
CLAUDE.md                       authoritative conventions (unchanged)
AGENTS.md                       symlink -> CLAUDE.md (unchanged)
README.md / README.zh-CN.md     unchanged
CONTRIBUTING.md                 **append git hooks opt-in section**
**CHANGELOG.md**                governance baseline (v0.1.0 = commits after cbb5e61 through this spec)
**CODEOWNERS**

agents/
  README.md                     **new**
  README.zh-CN.md               **new**
  planner.md                    **new sample** (read-only, opus)
  code-reviewer.md              **new sample** (read-only + Bash for git diff/log)

skills/
  README.md                     **new**
  README.zh-CN.md               **new**

contexts/
  README.md                     **new**
  README.zh-CN.md               **new**
  dev.md / review.md / oncall.md  **new samples**

rules/
  README.md                     **new**
  README.zh-CN.md               **new**
  git-workflow.md               **new sample**

config/
  prefixes.json                 **new** (only `di-` declared)
  credentials.template.json     **new** (placeholders only)

scripts/
  validate.sh                   unchanged
  validate_repo.py              **extended**: prefix check, description length, agent frontmatter strict types

tests/
  test_validate_repo.py         **extended** for new rules

.githooks/                      **new directory**
  pre-commit                    **new**: runs validate.sh

docs/
  architecture.md               **new**
  specs/
    2026-05-14-scaffold-completion.md   this file
  decisions/
    0001-scaffold-completion.md  **new ADR** capturing the direction of this work
  services/                     unchanged
  contribution/overview.md      unchanged
```

Roughly 22-24 new or modified files. Per project rule, work ships in batches of <= 3 files each.

## Code Style

### Agent frontmatter (Claude Code + Codex compatible)

```yaml
---
name: planner
description: >
  Read-only implementation planner for di-cli changes.
  TRIGGER when: user asks to plan a non-trivial change touching multiple files.
  DO NOT TRIGGER when: change is a typo fix or single-line tweak.
tools:
  - Read
  - Grep
  - Glob
model: opus
readonly: true
---
```

Rules: `name` equals filename without `.md`. `tools` is read by Claude Code. `readonly: true` is read by Codex. Use `opus` for reasoning-heavy agents and `sonnet` for throughput-heavy ones. `code-reviewer` may include `Bash` to run `git diff` / `git log`, and must state that restriction explicitly in its body.

### `config/prefixes.json` shape

```json
{
  "version": 1,
  "prefixes": [
    {
      "prefix": "di-",
      "scope": "department",
      "owner": "Data Infra",
      "description": "DI department-wide skills"
    }
  ],
  "policy": {
    "enforce": "warn",
    "rationale": "Scaffold stage — unknown prefix is a warning, not an error, until the first real skill lands."
  }
}
```

Validator behavior: when `policy.enforce == "warn"`, an unknown prefix is reported as a warning. When it becomes `"error"`, the same condition fails the build.

### Shell scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
    echo "ERROR: run 'uv sync' first" >&2
    exit 1
fi
```

Use `[[ ]]` over `[ ]`, quote variables, prefer `set -euo pipefail`.

### Bilingual policy

English is primary. Proper nouns get an inline Chinese gloss, e.g. "Data Infra (数据基础设施)". `.zh-CN.md` files mirror their English counterpart's structure, not a reorganized translation.

## Testing Strategy

- Add or update tests in the same batch as the validator change.
- `tests/test_validate_repo.py` is the primary harness; new rule families may be split into focused files (e.g. `tests/test_prefixes.py`) only when they exceed ~200 lines.
- Every new validator branch needs at least one happy-path and one failure case.
- `.githooks/pre-commit` is verified manually with a forced bad commit before declaring the batch done; no automated harness is required for the hook itself.
- Entry point: `uv run pytest tests/`. CI integration is out of scope for this spec.

## Boundaries

Always do:

- Keep each batch to at most 3 changed files.
- Ship validator changes and their tests in the same batch.
- For every new user-facing doc, create the matching `.zh-CN.md` in the same batch.
- New frontmatter fields must either be already understood by the validator or be added to the validator in the same batch.
- Run `bash scripts/validate.sh` and `uv run pytest tests/` before declaring the batch done.

Ask first:

- Adding a second prefix beyond `di-`.
- Modifying existing clauses in `CLAUDE.md` (versus appending new sections).
- Adding `--no-verify` style bypass to `.githooks/`.
- Changing the `AGENTS.md` symlink target or `CLAUDE.md` structure.
- Adding any runtime or test dependency.
- Touching `.venv/` or `uv.lock` beyond what `uv sync` produces.

Never do:

- Real service integrations, real credentials, real MCP servers.
- Sample content that describes capabilities `di-cli` does not currently have (any "planned" command must be explicitly marked planned).
- Non-placeholder values in `config/credentials.template.json`.
- Make `.githooks/` mandatory — `git config core.hooksPath` stays opt-in.
- Add Cursor adaptation (out of scope; only Claude Code and Codex are supported here).

## Success Criteria

1. `bash scripts/validate.sh` exits 0 on `main`.
2. `uv run pytest tests/` is fully green.
3. With `.githooks/` opted in, breaking `agents/planner.md` (e.g. setting `name` to a non-kebab-case value) causes `pre-commit` to call the validator and reject the commit.
4. A new contributor, using `agents/README.md` plus `agents/planner.md` as a template, can author a new agent whose frontmatter passes the validator (verified by human review).
5. `config/prefixes.json` is the only place that declares prefix taxonomy; `CLAUDE.md` and `CONTRIBUTING.md` refer to it rather than hard-coding a prefix list.
6. `CLAUDE.md`, `CONTRIBUTING.md`, and the new subdirectory READMEs do not contradict each other (human spot-check plus a soft validator hint).

## Resolved Questions

- **ADR numbering**: starts at `0001-scaffold-completion.md`.
- **commit-msg hook**: out of scope for this spec; only `pre-commit` is added now.
- **`code-reviewer` permissions**: may include `Bash` for `git diff` / `git log`; the agent body must explain why a read-only agent needs shell access, in line with the least-privilege principle in `CLAUDE.md`.
- **CHANGELOG baseline**: `v0.1.0` covers commits from after `cbb5e61` through the landing of this spec; subsequent versions follow the sra-toolkit-style entry format.
