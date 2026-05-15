# Contexts

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Contexts are **work-mode presets** injected at session start. They set the AI's priorities, approach, and safety defaults for a specific type of task — for the duration of that session only.

## Contexts vs Rules vs Skills

| | Contexts | Rules | Skills |
|---|----------|-------|--------|
| **Loading** | Manual — CLI flag at session start | Auto — every conversation (after install) | Auto — matched by task description |
| **Scope** | Current session only | Every session | When the topic is relevant |
| **Content** | Work mode: priorities, approach, safety stance | Universal conventions | Domain knowledge, APIs, runbooks |
| **Use for** | "How the AI should think" for this session | "What to always follow" | "What the AI should know" about a platform |

A context answers "what kind of work am I doing right now?". Rules and skills remain active regardless of context.

## Available Contexts

| Context | Mode | When to use |
|---------|------|-------------|
| `dev.md` | Development | Active coding — ship working code, explain after |
| `review.md` | Code review | PR review — quality, safety, convention compliance |
| `oncall.md` | Oncall investigation | Incident response — evidence chain, read-only by default |

## How to Use

### Claude Code

Use `--system-prompt` to inject a context at session start:

```bash
claude --system-prompt "$(cat ~/.claude/skills/di-cli/contexts/dev.md)"
```

Set up shell aliases for convenience. Add to `~/.zshrc` or `~/.bashrc`:

```bash
DI_CONTEXTS="$HOME/.claude/skills/di-cli/contexts"   # adjust path to your install

alias claude-dev='claude --system-prompt "$(cat $DI_CONTEXTS/dev.md)"'
alias claude-review='claude --system-prompt "$(cat $DI_CONTEXTS/review.md)"'
alias claude-oncall='claude --system-prompt "$(cat $DI_CONTEXTS/oncall.md)"'
```

Then start a session:

```bash
claude-oncall     # oncall investigation mode
claude-dev        # development mode
claude-review     # code review mode
```

### Codex

Codex does not support dynamic system-prompt injection at session start. Manually prepend the context content to your first message, or paste it into your workspace system prompt configuration.

## Creating a New Context

A context is a plain markdown file — no YAML frontmatter required. Write it as a system prompt: direct, concise, action-oriented.

Structure:

```markdown
# Context: <Mode Name>

<One-paragraph framing: what mode this is and when to use it.>

## Priorities
1. <highest priority behaviour>
2. ...

## Approach
- <how to act in this mode>

## Safety
- <what to avoid or double-check in this mode>
```

Keep it under ~100 lines. A context that tries to cover everything becomes noise. If a convention belongs in every session, write a rule instead. If it is domain-specific, write a skill.
