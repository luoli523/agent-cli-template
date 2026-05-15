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

Rules are **not auto-installed**. Each user opts in. Below are two installation styles — pick one.

Replace `/path/to/di-cli` in the snippets below with the actual clone path (`~/.sra/repos/di-cli` if installed via the future `di` CLI, or wherever you cloned it).

### Style A: explicit symlink (recommended)

Link **named files**, not the whole directory:

```bash
# Claude Code (user-level)
ln -sf /path/to/di-cli/rules/git-workflow.md \
       ~/.claude/rules/git-workflow.md
```

**Do not do this:**

```bash
# Wrong — would also link README.md, polluting every conversation
ln -sf /path/to/di-cli/rules/*  ~/.claude/rules/
```

`~/.claude/rules/` is auto-scanned by Claude Code, so any `.md` file dropped there is loaded into every session. README files in this repo are convention docs, not rules — keep them out of `~/.claude/rules/`.

For project-level installation (applies only inside one repo):

```bash
mkdir -p .claude/rules
cp /path/to/di-cli/rules/git-workflow.md .claude/rules/
```

### Style B: `@import` from your CLAUDE.md (Claude Code only)

Edit your `~/.claude/CLAUDE.md` (create it if absent) and add:

```markdown
@~/.di/repos/di-cli/rules/git-workflow.md
```

Claude Code resolves and loads the imported file (up to 5 hops of recursion). The first time, Claude Code asks for approval — accept it. The benefit over symlinks: the import is **explicit and visible** when you open your CLAUDE.md, and a deleted repo produces a clear error rather than a silent dangling symlink.

### Codex (user-level)

Codex uses a single instruction file — `~/.codex/AGENTS.md` — and **does not** scan a `rules/` subdirectory or support `@import`. (`~/.codex/rules/` is Codex's execpolicy/sandbox directory and serves a completely different purpose; do not put rule files there.)

To use di-cli rules under Codex, either:

**Codex option 1 — append the rule content** to `~/.codex/AGENTS.md`:

```bash
cat /path/to/di-cli/rules/git-workflow.md >> ~/.codex/AGENTS.md
```

Trade-off: upstream rule changes do not flow through automatically; re-run when the rule is updated.

**Codex option 2 — symlink `AGENTS.md`** when you have no other Codex instructions:

```bash
ln -sf /path/to/di-cli/rules/git-workflow.md ~/.codex/AGENTS.md
```

Trade-off: this is your only Codex instruction file; combine multiple sources by hand or use option 1.

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
