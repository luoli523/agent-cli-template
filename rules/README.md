# Rules

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Rules are **always-loaded guidelines** — short conventions injected into every AI assistant conversation, regardless of what the user is working on. Unlike skills (on-demand, matched by task description), rules are present all the time.

## Rules vs Skills vs Contexts

| | Rules | Skills | Contexts |
|---|-------|--------|----------|
| **Loading** | Every conversation (after manual install) | On-demand — matched by task | Session start — injected via CLI |
| **Scope** | Universal conventions | Domain knowledge for a specific topic | Work-mode mindset for a session |
| **Content** | Short "always do / never do" norms | Platform APIs, query templates, runbooks | Priorities and approach for dev / review / oncall |
| **Use for** | Commit format, branch naming, safety invariants | Service-specific workflows | Setting the AI's mode for a whole session |

Write a rule when a convention is short, universal, and must be active in **every** conversation — not just when a certain topic comes up.

If the guideline is long, topic-specific, or only applies occasionally, put it in a skill instead.

## Installation

Rules are **not auto-installed**. Each user opts in by symlinking or copying to their AI tool's rules directory:

```bash
# Claude Code (user-level)
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.claude/rules/git-workflow.md

# Codex (user-level)
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.codex/rules/git-workflow.md
```

Replace `/path/to/di-cli` with the actual clone path (`~/.sra/repos/di-cli` if installed via the future `di` CLI, or wherever you cloned it).

For project-level installation (applies only inside one repo):

```bash
# Claude Code project-level
mkdir -p .claude/rules
cp /path/to/di-cli/rules/git-workflow.md .claude/rules/
```

## Available Rules

| Rule | Description |
|------|-------------|
| `git-workflow.md` | Commit message format, branch naming, and MR checklist for di-cli contributors. |

## Creating a New Rule

A good rule is:

- **Short** — fits in one or two screens. Longer guidelines belong in a skill or a doc.
- **Universal** — applies to all di-cli work, not just one service or scenario.
- **Actionable** — tells the AI exactly what to do or avoid, not vague principles.
- **Non-redundant** — does not repeat what is already in `CLAUDE.md`.

Template:

```markdown
# Rule: <name>

<one-paragraph purpose>

## Always
- <concrete action>

## Never
- <concrete prohibition>

## Examples
<short before/after if helpful>
```

Before opening a PR for a new rule, ask: "Would every di-cli contributor benefit from this in every conversation?" If the answer is "only sometimes," write a skill instead.
