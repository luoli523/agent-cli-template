---
name: di-mr-flow
maintainer:
  - li.luo@shopee.com
description: >
  di-cli merge-request workflow (di-cli MR 流程) — branch from main, commit with hooks active, push, open a GitLab MR via glab, wait for CI, squash-merge, and clean up the local branch.
  TRIGGER when: user wants to "open MR", "create merge request", "提 MR", "提 PR", "merge this", "ship this change", "push and merge", or is on di-cli's main branch and asks to make any change (main is protected).
  DO NOT TRIGGER when: user is asking general git questions unrelated to this repo's flow (rebase basics, conflict resolution mechanics), or has already opened the MR and is asking only about debugging a CI failure.
---

# di-cli MR Flow

End-to-end runbook for landing a change in di-cli. `main` is a protected branch, so every change — even a one-line fix — flows through a feature branch and a GitLab merge request.

This skill assumes the contributor has already followed the rest of di-cli's working rules (`CLAUDE.md`, `rules/git-workflow.md`, `CONTRIBUTING.md`) for things like batch size discipline and commit-message style.

## Tools you need

- `git` — standard.
- [`glab`](https://gitlab.com/gitlab-org/cli) — GitLab CLI, used for MR creation and merge.
- A git credential helper (e.g. `osxkeychain` on macOS) or an SSH remote, so `git push` does not block on credentials.
- `glab auth status` should show you logged in to `git.garena.com` before the MR step.

## Pre-flight

Run these checks before starting. The skill assumes a clean baseline; failures here mean fix them first, not work around them.

```bash
git status -sb                  # working tree matches your intent
bash scripts/validate.sh        # validator exits 0
uv run pytest tests/ -q         # if you touched Python / validator config
glab auth status                # logged in to git.garena.com
git fetch origin && git status -sb  # local main is current
```

If `.githooks/` is not enabled, the pre-commit check at commit time becomes a no-op. Enable once with `git config core.hooksPath .githooks` so validator runs automatically.

## 1. Branch

Branch name follows `rules/git-workflow.md`:

```text
<username>/<type>/<description>
```

- `<username>` — your GitLab username, e.g. `li.luo`.
- `<type>` — `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.
- `<description>` — kebab-case, optionally with a date or ticket ID.

```bash
git checkout -b li.luo/feat/add-datamap-skill
```

Create the branch **before** editing files when possible — it keeps the working tree on `main` clean and lets you abandon work cheaply if priorities shift.

## 2. Commit

Commit format follows `rules/git-workflow.md`:

- `<type>(<scope>): <description>` or `<type>: <description>`
- Imperative mood, first line ≤ 72 characters.
- Body explains *why*, not what. Required for non-trivial changes.

```bash
git add <specific files>        # avoid `git add -A` when possible
git commit -m "feat(skills): add di-datamap-lineage skill" \
           -m "Provides table metadata, lineage, and owner lookup for the DataMap (数据地图) platform. Triggered by \"DataMap\", \"lineage\", or \"血缘\". Credentials template added under config/."
```

When `core.hooksPath` is set to `.githooks/`, `pre-commit` runs `bash scripts/validate.sh` automatically. A failing validator blocks the commit; **do not** use `--no-verify` to bypass — fix the root cause.

## 3. Push

```bash
git push -u origin li.luo/feat/add-datamap-skill
```

`-u` is required on the first push so the branch tracks the remote. Subsequent pushes are just `git push`.

If push prompts for credentials repeatedly, configure a helper once and retry:

```bash
git config --global credential.helper osxkeychain   # macOS
```

GitLab requires a Personal Access Token (with `read_repository` + `write_repository` scopes) — generate one at <https://git.garena.com/-/profile/personal_access_tokens> and use it as the password the first time. The keychain caches it after that.

## 4. Open MR via glab

```bash
glab mr create \
  --target-branch main \
  --squash-before-merge \
  --remove-source-branch \
  --title "feat(skills): add di-datamap-lineage skill" \
  --description "$(cat <<'EOF'
## Summary
- Adds skills/di-datamap-lineage with read-only metadata, lineage, and owner lookups.
- Credentials template under config/credentials.template.json gains a `datamap.token` entry.

## Why
First real skill landing on top of the v0.1 scaffold. Exercises the contribution checklist end-to-end and the prefix policy (`di-` taxonomy is enforced; the skill name conforms).

## Test plan
- [x] bash scripts/validate.sh
- [x] uv run pytest tests/
- [ ] Reviewer: spot-check SKILL.md against rules/git-workflow.md + skills/README.md
EOF
)"
```

Notes:

- `--squash-before-merge` keeps `main` history clean — one squashed commit per MR.
- `--remove-source-branch` deletes the feature branch on the remote after merge; combine with the local cleanup in step 7.
- Use a HEREDOC for the description to preserve formatting (titles, lists, checkboxes).
- The description should always include three sections: **Summary** (what changed), **Why** (motivation), **Test plan** (how to verify). Reviewers rely on these.

`glab` prints the MR URL on success — record it.

## 5. CI

The pipeline defined in `.gitlab-ci.yml` runs automatically on every MR. It installs deps via `uv sync --frozen --extra dev` and then runs `bash scripts/validate.sh` followed by `uv run pytest tests/`.

```bash
glab mr ci view <mr-id>         # tail the latest pipeline
glab mr view <mr-id>            # MR summary including CI status
```

If CI is red:

1. Read the failing job log: `glab ci trace <job-id>` or open the GitLab UI.
2. Fix locally — re-run `bash scripts/validate.sh` and `uv run pytest tests/`.
3. `git add … && git commit && git push` — a new pipeline triggers on push.
4. If multiple fix commits accumulate, that is fine; the squash-merge collapses them.

Never merge a red pipeline. If CI is failing for reasons unrelated to your change (flaky test, infra outage), pause and escalate rather than bypass.

## 6. Merge

After CI is green and the human reviewer has approved:

```bash
glab mr merge <mr-id> --squash --yes
```

- `--squash` honours the MR's `Squash-before-merge` setting and collapses commits into one.
- `--yes` skips the interactive confirmation; omit it if you want to see the squash commit message first.

The remote feature branch is auto-deleted because the MR was created with `--remove-source-branch`.

## 7. Cleanup

```bash
git checkout main
git pull
git branch -d li.luo/feat/add-datamap-skill
```

The local-branch delete is `-d` (safe, refuses if unmerged), not `-D` (force). If `-d` complains that the branch was not merged to HEAD, double-check that the squashed commit really did land — usually the message is a false alarm because of the squash flatten.

## Edge cases

- **Merge conflict against main.** `git fetch origin main && git rebase origin/main`, resolve, `git push --force-with-lease`. Never `--force` blindly on a shared branch.
- **CI fails on a flaky test.** Re-run via the GitLab UI ("Retry") rather than pushing an empty commit. If the test is genuinely flaky, file the flake; don't keep retrying.
- **Reviewer requests changes after MR is open.** Just commit + push to the same branch; the MR updates in place and the pipeline re-runs.
- **You pushed a credential by accident.** Stop, do not merge. Rotate the credential at the source, then rewrite history on the branch (`git rebase -i` + `--force-with-lease`) before the MR is merged — and tell the reviewer.
- **Wrong target branch.** Edit the MR in the GitLab UI; do not close-and-reopen — losing the MR ID also loses review history.
- **MR was opened by another contributor and you are taking over.** Push to the same branch (you need permission on it). Do **not** open a parallel MR.

## Common rejections at MR time

Match these to fixes before opening the MR, not after.

| Symptom | Likely cause | Fix |
|---|---|---|
| `validate.sh` red on CI | Missing `TRIGGER when:` / `DO NOT TRIGGER when:` in a SKILL.md, or agent frontmatter has wrong type | Run `bash scripts/validate.sh` locally — same script CI uses |
| pytest red on CI but green locally | Forgot `uv sync --frozen --extra dev` locally; pytest not installed | Re-sync with `--extra dev` and re-run |
| `pre-commit` blocked the commit | Validator caught an issue; you tried `--no-verify` | Fix the root cause, recommit |
| `glab` push rejected | Branch name does not match `<user>/<type>/<desc>` | Rename branch: `git branch -m new-name` |
| Reviewer asks "what changed and why?" | MR description missing **Summary** / **Why** / **Test plan** | Edit the MR description; reviewers should not have to read the diff to know the intent |
