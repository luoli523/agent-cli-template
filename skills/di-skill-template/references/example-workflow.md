# Example workflow — replace this file

This file demonstrates **the format** for per-workflow reference docs.
The convention (borrowed from feishu-cli's lark-calendar references)
is one file per shortcut, named to mirror the shortcut's verb. When
you fork the template, delete this file and create your own:

```
skills/di-<service>/
├── SKILL.md
└── references/
    ├── di-<service>-<verb1>.md
    ├── di-<service>-<verb2>.md
    └── ...
```

Each reference doc walks the agent through one workflow end-to-end.
Below is the structure to copy.

---

## di-<service>-<verb> — `<one-line purpose>`

### Trigger

(One paragraph: when does the agent decide to use this specific
shortcut? Avoid overlap with sibling reference docs.)

> Example: "User asks 'what tables does fact_order depend on' or
> 'who owns dim_user' or any other lineage / ownership query against
> a specific table identifier."

### Pre-conditions

(Bullet list: what must be true before invoking. Identity, scope,
upstream artifacts the agent must have located.)

- Identity is `<role>` (run `di auth login --scope <s>` if missing).
- The agent has already resolved `<entity-id>` from the user's
  phrasing (free-text → canonical id is a separate step; document
  it in `references/<service>-resolve-entity.md`).

### Step-by-step

```bash
# 1. <human-readable step description>
di <service> +<verb> --flag-1 value-1 --flag-2 value-2

# 2. Read the envelope, branch on identity. If <condition>:
di <service> +<follow-up> ...
```

Annotate decisions inline. The agent reads this file top-to-bottom;
the format must mirror how the agent will reason.

### Common failure modes (skill-local)

(Failures specific to this workflow. General di-cli failures live in
the parent SKILL.md's `Common AI failure modes` section; only put
*this-workflow's* failures here.)

- **<symptom>** → **<recovery>**

### Output shape

(What the agent should see in `data` on success. Helps it know when
to short-circuit further calls.)

```json
{
  "ok": true,
  "data": {
    "<key-1>": "...",
    "<key-2>": [...]
  }
}
```

### Cross-references

- Parent skill: [`../SKILL.md`](../SKILL.md)
- Sibling workflows: `<list-other-references-here>`
- Service ADR: `<replace-me>`
