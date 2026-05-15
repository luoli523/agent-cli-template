# Skills

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Skills are **on-demand knowledge modules** loaded into an AI assistant's conversation when the user's task matches the skill's description. Each skill is a directory containing a `SKILL.md` file with YAML frontmatter and a markdown body.

## Directory Layout

```text
skills/
  datamap-lineage/
    SKILL.md              # required — skill definition
    references/           # optional — long-form docs, schemas
    scripts/              # optional — helper scripts (uv run / bash)
  scheduler-task-debug/
    SKILL.md
  ...
```

### Flat structure only

All skill directories must be direct children of `skills/`. Nested directories (for example `skills/platform/datamap-lineage/`) are **not allowed** and are rejected by the validator. Reasons:

1. AI tools scan one level deep and silently ignore nested skill directories.
2. The future installer assumes a 1:1 mapping between `skills/<name>/` and `~/.agents/skills/<name>` symlinks.
3. A flat layout keeps skill discovery, naming collisions, and ownership reviews trivial.

## SKILL.md Format

Every `SKILL.md` starts with YAML frontmatter, followed by a markdown body.

### Required fields

```yaml
---
name: datamap-lineage
maintainer:
  - owner@shopee.com
description: >
  DataMap lineage (DataMap 血缘) — query table metadata, lineage, owners, and governance hints.
  TRIGGER when: user asks about "DataMap", "lineage", "血缘", "table owner", "schema", or "metadata".
  DO NOT TRIGGER when: the task is general SQL writing without metadata lookup.
---
```

| Field | Rule |
|-------|------|
| `name` | kebab-case; must equal the directory name. |
| `maintainer` | Non-empty array of maintainer email addresses or team aliases. A single string is also accepted but the array form is preferred. |
| `description` | Must use the three-part trigger keyword format below, and stay within **1024 characters** after YAML folding. |

### Trigger keyword description

The `description` field is the **primary mechanism** AI tools use to match a task to a skill. A poorly written description means the skill is never triggered when it should be — or is triggered when it shouldn't.

Required structure (three parts, in this order):

```text
<what the skill does — one sentence, with bilingual proper nouns>.
TRIGGER when: <specific keywords and phrases, in English and Chinese, that should activate this skill>.
DO NOT TRIGGER when: <common false-positive scenarios>.
```

Rules:

- Use YAML folded block scalar (`>`) for multi-line descriptions.
- Quote exact terms — `"DataMap"`, `"血缘"` — so they stand out as triggers.
- The validator reports a missing `TRIGGER when:` or `DO NOT TRIGGER when:` as an error.

### Optional fields (sra-toolkit-compatible reference)

The validator does not require these, but vendors and downstream tools often expect them. Use them when relevant:

```yaml
category: platform           # high-level grouping (platform | data | qa | ...)
tags: [datamap, lineage]     # free-form tags for search and analytics
cli: scripts/datamap.py      # entry point inside this skill, if any
credentials:                 # credentials the skill expects in ~/.config/di/credentials.json
  - name: datamap.token
    description: "Bearer token for DataMap API"
```

If you add `credentials`, the future installer will look up matching entries in `config/credentials.template.json` and prompt the user to fill them in.

### Body guidelines

- Body under ~500 lines. Move long reference material to `references/` and helper scripts to `scripts/`.
- No absolute paths (skills are symlinked to different locations in the future installer).
- English primary; bilingual annotation for proper nouns: `Feature Store Engine (特征存储引擎)`.

## Naming Convention

Names must be **kebab-case** and **service-oriented**. Prefer the shape:

```text
<prefix>-<domain>[-<object>][-<action>]
```

Examples: `datamap-lineage`, `scheduler-task-debug`, `dqc-rule-check`, `ram-permission-debug`.

### Prefixes

Prefixes are declared in [`config/prefixes.json`](../config/prefixes.json), which is the single source of truth. Scaffold-stage prefixes:

| Scope | Prefix | Owner |
|-------|--------|-------|
| Department | `di-` | Data Infra |

`config/prefixes.json` carries a `policy.enforce` field:

- `"warn"` (current default) — unknown prefix is a validator warning, not an error.
- `"error"` — unknown prefix fails the build. Switch only after the prefix taxonomy stabilizes.

To add a new prefix, open a proposal in `docs/decisions/` first; do not modify `config/prefixes.json` unilaterally.

## Available Skills

| Skill | Purpose |
|-------|---------|
| [`di-mr-flow`](di-mr-flow/SKILL.md) | Branch → commit → push → GitLab MR → CI → squash-merge → cleanup. Triggered by "open MR", "提 MR", "merge this". |

## Validation

```bash
bash scripts/validate.sh
```

Skills-related checks include:

- `name` matches the directory name.
- `maintainer` is present and non-empty.
- `description` contains `TRIGGER when:` and `DO NOT TRIGGER when:`.
- No nested skill-like directories.
- Prefix appears in `config/prefixes.json` (per `policy.enforce`).

See `CONTRIBUTING.md` for the full checklist before opening a PR.
