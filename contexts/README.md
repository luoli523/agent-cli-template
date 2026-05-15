# Contexts

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Work-mode presets injected at session start, setting an AI assistant's priorities, approach, and safety defaults for the duration of one session. **Currently empty placeholder** — no contexts are shipped yet.

## When to contribute here

Add a context when:

- A specific mode of working (e.g. development, code review, on-call investigation, research) needs **consistent AI behavior across an entire session**, not just for one task.
- The behavior cannot be captured by a rule (always-on) or a skill (on-demand by topic) — it specifically describes "what mode am I in right now".
- The team will actually invoke it. A context that nobody uses is pure overhead.

## Authoring format

A context is **plain markdown** — no YAML frontmatter, no validator-required fields. Treat it as a system prompt: direct, action-oriented, concise.

Recommended structure:

```markdown
# Context: <Mode Name>

<One paragraph describing this mode and when to use it>

## Priorities
1. <highest priority behavior>
2. ...

## Approach
- <how to act in this mode>

## Safety
- <what to avoid or double-check in this mode>
```

Keep each context under ~100 lines. Anything longer becomes noise the AI tends to skim.

## How users activate a context

Contexts are not auto-installed. Users opt in by injecting them at session start.

**Claude Code**:

```bash
claude --system-prompt "$(cat ~/.di/repos/di-cli/contexts/<mode>.md)"
```

A shell alias makes it ergonomic. **Codex** does not support runtime system-prompt injection; paste the content into the first message or workspace prompt.

## Validator

The validator does not check contexts — no structural requirements are enforced.

## See also

- `CLAUDE.md` for the rules/contexts/skills taxonomy
