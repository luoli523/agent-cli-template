# Rules

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Always-loaded guidelines — short conventions injected into every AI conversation after the user opts in. **Currently empty placeholder** — no rules are shipped yet.

## When to contribute here

Add a rule when:

- A convention is **short, universal, and must be active in every conversation** — not just when a topic comes up.
- The rule is genuinely non-redundant with `CLAUDE.md` (which is already always-loaded for Claude Code).
- Every DI contributor in every conversation benefits. If the answer is "only sometimes" or "only for one service", write a skill instead.

A good rule fits in one or two screens. Anything longer should be a skill or a doc.

## Authoring format

A rule is a single markdown file: `rules/<name>.md`. No YAML frontmatter required.

Suggested structure:

```markdown
# Rule: <name>

<one-paragraph purpose>

## Always
- <concrete action>

## Never
- <concrete prohibition>
```

Keep each rule under ~50 lines.

## How users install a rule

Rules are **not auto-installed**. Users opt in. Two installation styles for **Claude Code**:

```bash
# Style A — explicit symlink (link named files, not the directory)
ln -sf /path/to/di-cli/rules/<name>.md ~/.claude/rules/<name>.md

# Style B — @import in ~/.claude/CLAUDE.md (more explicit)
echo "@/path/to/di-cli/rules/<name>.md" >> ~/.claude/CLAUDE.md
```

`~/.claude/rules/` is auto-scanned by Claude Code. **Do not** blanket-link the directory (`ln -sf rules/* ~/.claude/rules/`) — that would also load `README.md` as a rule.

**Codex** uses a single `~/.codex/AGENTS.md` and does not scan a rules subdirectory or support `@import`. To use a di-cli rule under Codex, append its content to `~/.codex/AGENTS.md` manually. `~/.codex/rules/` is Codex's execpolicy directory — do **not** put rule files there.

## Validator

The validator does not check rules — no structural requirements are enforced.

## See also

- `CLAUDE.md` for the rules/contexts/skills taxonomy
