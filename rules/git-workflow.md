# Rule: Git Workflow

This rule applies to all di-cli contributors and the AI assistants that help them. It covers commit message format, branch naming, and MR checklist. These conventions are enforced by the `.githooks/` pre-commit hook (opt-in; see `CONTRIBUTING.md`).

## Commit Messages

Format: `<type>(<scope>): <description>` or `<type>: <description>`

| Type | When to use |
|------|-------------|
| `feat` | New skill, agent, context, rule, or capability |
| `fix` | Bug fix in a script, validator, or hook |
| `docs` | Documentation only — README, spec, decision record |
| `refactor` | Code restructuring with no behavior change |
| `test` | Test additions or fixes |
| `chore` | Build, CI, dependency, or tooling changes |

### Rules

- **Imperative mood**: "add skill" not "added skill" or "adding skill".
- **First line ≤ 72 characters** (hard limit: 100).
- **Scope** is optional but recommended for larger repos: `feat(skills):`, `fix(validator):`, `docs(agents):`.
- **Body**: add a blank line after the first line, then explain *why* — not what (the diff shows what). Required for non-trivial changes.
- **No `--no-verify`**: do not bypass hooks. If a hook fails, fix the root cause.

### Examples

```
feat(skills): add datamap-lineage skill

Provides table metadata, lineage, and owner lookup for the DataMap
(数据地图) platform. Triggered by "DataMap", "lineage", or "血缘" in
the user's prompt. Credentials template added to config/.
```

```
fix(validator): allow README.md under skills/ and agents/

Validator rejected direct files under skills/ with only .gitkeep
whitelisted. READMEs are convention docs, not skill directories.
```

```
docs(agents): add planner sample
```

## Branch Naming

```
<username>/<type>/<description>
```

- `<username>`: your company username, e.g. `li.luo`.
- `<type>`: one of `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.
- `<description>`: kebab-case, optionally with a date or ticket ID.

Examples:
- `li.luo/feat/add-datamap-skill`
- `li.luo/fix/validator-readme-whitelist`
- `li.luo/docs/scaffold-completion-spec`

`revert-*` branches are also allowed.

Branch model: `main` (development, default) → `release` (stable, protected). Tags are cut from `release` only.

## MR Checklist

Before opening a merge request, confirm:

- [ ] `bash scripts/validate.sh` exits 0.
- [ ] `uv run pytest tests/` is fully green.
- [ ] Each batch touches at most 3 files (or reviewer explicitly approved a larger batch).
- [ ] User-facing docs have a matching `.zh-CN.md`.
- [ ] No credentials, secrets, or personal absolute paths.
- [ ] New frontmatter fields are either already validated or validator is updated in the same MR.
- [ ] "Planned" capabilities are explicitly labelled — not described as available.
- [ ] Ownership is clear: skill has `maintainer`, service doc names an owner.

## Always

- Run `bash scripts/validate.sh` locally before pushing.
- Use imperative mood and keep the first line under 72 characters.
- Explain *why* in the commit body for non-trivial changes.

## Never

- Use `git commit --no-verify` or `git push --force` without explicit approval.
- Commit to `main` directly for changes that affect more than 3 files — open an MR.
- Include credentials, tokens, or personal paths in any committed file.
