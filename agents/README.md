# Agents

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Agents are **specialized sub-agents** with scoped tool permissions and focused expertise. Unlike skills (knowledge loaded into the main conversation), agents run as separate entities with their own system prompt and restricted tool access.

## File Layout

Each agent is a single markdown file: `agents/<name>.md`. The same file is consumed by Claude Code and Codex; each tool reads the frontmatter fields it understands and ignores the rest.

| Tool | User-level path | Project-level path |
|------|-----------------|--------------------|
| Claude Code | `~/.claude/agents/` | `.claude/agents/` |
| Codex | `~/.codex/agents/` | `.codex/agents/` |

The future `di` installer will symlink each `agents/*.md` into both directories. Today, contributors and users can copy or symlink the files by hand.

## Frontmatter

```yaml
---
name: planner                       # required; kebab-case; equals filename without .md
description: >                      # required; trigger keyword format recommended
  Read-only implementation planner.
  TRIGGER when: user asks for a step-by-step plan touching multiple files.
  DO NOT TRIGGER when: change is a typo or single-line fix.
tools:                              # Claude Code only — restricts available tools
  - Read
  - Grep
  - Glob
model: opus                         # Claude Code only — opus | sonnet | haiku
readonly: true                      # Codex only — restricts write/exec permissions
---
```

| Field | Required | Claude Code | Codex | Notes |
|-------|----------|-------------|-------|-------|
| `name` | **yes** | yes | yes | kebab-case; must equal the filename stem |
| `description` | **yes** | yes | yes | drives auto-delegation; use the trigger keyword format |
| `tools` | no | **yes** | ignored | least-privilege list; omit to inherit the main agent's tool set |
| `model` | no | yes | ignored | `opus` for reasoning, `sonnet`/`haiku` for throughput |
| `readonly` | no | ignored | **yes** | recommended `true` unless the agent must write |

The validator emits a warning when `readonly: true` is missing — granting write access is an explicit choice, not a default.

Although the trigger keyword format is not validator-enforced for agents (only for skills), it is still strongly recommended: AI tools use the `description` to decide whether to auto-delegate to the agent, and the same `TRIGGER when:` / `DO NOT TRIGGER when:` shape that works for skills works here.

## Agents vs Skills

| | Agents | Skills |
|---|--------|--------|
| File | `agents/<name>.md` | `skills/<name>/SKILL.md` (plus optional `references/`, `scripts/`) |
| Loading | explicit — user invokes with `@name`, or AI tool auto-delegates | automatic — matched by `description` keywords |
| Tool access | restricted by `tools` / `readonly` | same as the main conversation |
| Token cost | independent context when running | consumes main context when loaded |
| Use for | **capabilities** — structured workflow, approval logic | **knowledge** — APIs, query templates, runbooks |

A useful mental model: a skill is "knowledge loaded into your head"; an agent is "an expert you can call who has their own desk and access badge."

## Design Principles

1. **Least privilege.** Start with `readonly: true` and `tools: [Read, Grep, Glob]`. Add `Bash` only with a written reason in the agent body. Add `Edit` / `Write` only for agents whose entire purpose is to modify files.
2. **Single responsibility.** One agent per job. A planner plans; a reviewer reviews. If an agent's description grows into "X and also Y," split it.
3. **Model selection.** Use `opus` for reasoning-heavy planning, review, or design work. Use `sonnet` or `haiku` for high-throughput repetitive work where latency or cost matters.
4. **No vapor-ware.** Do not reference di-cli commands or services that do not currently exist. If the agent depends on a planned capability, mark it explicitly as planned and degrade gracefully when absent.

## How to Use

```text
> Use the planner agent to plan adding a new skill.
> @planner Plan the rollout of convention X.
> @code-reviewer Review the changes on this branch.
```

Tools may also auto-delegate to an agent when the user's prompt matches its `description`. To stop auto-delegation, name the agent you want explicitly.

## Creating a New Agent

1. Create `agents/<name>.md` and add the frontmatter shown above.
2. Write the body in three sections: **Role**, **Process**, **Output format**.
3. Keep tool access narrow. For each non-default tool, explain in the body why the agent needs it.
4. Run `bash scripts/validate.sh` before opening a PR.

See `CONTRIBUTING.md` for the full review checklist.
