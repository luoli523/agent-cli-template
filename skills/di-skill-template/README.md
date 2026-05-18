# di-skill-template — how to fork

This directory is the **starting point** for a new di-* skill. It is
*not* installed by `di install` (it's listed in `EXCLUDED_FROM_INSTALL`
inside `src/di/core/_sync.py`), and it's not loaded by AI agents at
runtime. Its only job is to give a sub-team a compliant skeleton to
copy.

For the wider onboarding flow (service ADR, schema delivery, etc.)
see [`docs/explainers/onboarding-sub-team.md`](../../docs/explainers/onboarding-sub-team.md).

## 5-step quick start

1. **Copy** the entire directory:
   ```bash
   cp -r skills/di-skill-template skills/di-<service>-<purpose>
   ```
   Name pattern: `di-<service>-<purpose>` (kebab-case, must start with
   `di-`). Examples: `di-datamap-lineage`, `di-scheduler-task-debug`,
   `di-dqc-rule-check`.

2. **Edit `SKILL.md` frontmatter**:
   - `name`: set to the new directory name (must match exactly — the
     validator enforces this).
   - `description`: rewrite with your service's real trigger summary;
     keep both `TRIGGER when:` and `DO NOT TRIGGER when:` markers
     (the validator enforces these too).
   - `maintainer`: list real owners (`@shopee.com` emails).
   - `metadata.cliHelp`: point at your service's `--help`, e.g.
     `"di datamap --help"`.

3. **Edit `SKILL.md` body**: walk top-to-bottom and replace every
   `<replace-me>`. The structure is correct; only the content is
   yours to fill. Pay extra attention to:
   - **Prerequisites** — list every scope and identity requirement.
   - **Identity & permission** — fill the table; ambiguity here
     leads to runtime confusion for agents.
   - **Common AI failure modes** — start with at least one observed
     failure once your skill has been exercised. Empty placeholders
     are fine on day one.

4. **Edit `references/`**: replace the `example-workflow.md` with
   real per-shortcut workflow docs (one file per shortcut is the
   convention from feishu-cli). Keep file names matching the
   shortcut name (`lark-calendar-create.md` style).

5. **Validate before opening the MR**:
   ```bash
   di validate --scope skills
   ```
   The skill must come up `ok`. Then run the full repo audit:
   ```bash
   di validate
   ```
   Overall must be `healthy`.

## Compliance checklist

Use this before requesting review:

- [ ] Directory name matches `name` in frontmatter
- [ ] `description` contains both `TRIGGER when:` and `DO NOT TRIGGER when:` markers
- [ ] `description` ≤ 1024 chars
- [ ] `maintainer` lists ≥1 real email
- [ ] Body starts with `# H1`
- [ ] At least one section pointing the agent at `../di-shared/SKILL.md`
- [ ] At least one entry under "Common AI failure modes" (or an explicit "no failures observed yet" note)
- [ ] `Identity & permission` lists every required RAM scope
- [ ] `See also` includes a link to the service ADR (or a TODO marker if the ADR is in flight)
- [ ] `di validate` returns `healthy` against the live repo

## What NOT to do

- **Don't** copy `di-shared` content into your new skill — your skill
  must *link* to `di-shared`, never duplicate its rules. If di-shared
  changes, you'd be left with stale guidance.
- **Don't** put business logic in the skill. Skills *teach*; the CLI
  *runs*. If your service needs orchestration code, it lives in
  `src/di/shortcuts/<service>/`, not in the SKILL.md.
- **Don't** rename or delete `<replace-me>` placeholders without
  filling them — leftover placeholders are easy to miss in review
  and end up shipped.
- **Don't** add the new skill to `EXCLUDED_FROM_INSTALL` unless it
  is genuinely template-shaped. Most skills get installed.
