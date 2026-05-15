# Agents

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Sub-agents with scoped tool permissions, invoked explicitly by users or auto-delegated by AI tools. **Currently empty placeholder** — no sample sub-agents are shipped while the cross-tool format story is unresolved (see [`docs/architecture.md`](../docs/architecture.md) § agents/).

## When to contribute here

Add a sub-agent when:

- A focused, repeatable task benefits from a separate agent with its own system prompt and restricted tool access.
- The agent has a concrete consumer in DI workflows. Do not add demos to "show the format" — write an agent when there's a user.
- The agent's responsibility is single — one job per agent. If the description becomes "X and also Y", split it.

## Authoring format

| Tool | File format | Scanned path (user) |
|------|-------------|---------------------|
| Claude Code | Markdown + YAML frontmatter | `~/.claude/agents/<name>.md` |
| Codex       | TOML | `~/.codex/agents/<name>.toml` |

**Claude Code** frontmatter required fields: `name` (kebab-case, equals filename stem), `description` (trigger keyword format recommended). Optional: `tools` (list of strings), `model` (`opus` / `sonnet` / `haiku`), `readonly` (boolean — recommended `true`).

**Codex** TOML required fields: `name`, `description`, `developer_instructions` (multi-line string). See <https://developers.openai.com/codex/subagents>.

Cross-tool support today requires shipping parallel `.md` and `.toml` files. A generator is not yet provided.

## Validator

`scripts/validate_repo.py` checks Markdown agent frontmatter (name match, description present, tools/readonly/model types). TOML agent files are currently passed through without schema validation.

## See also

- `CLAUDE.md` § Agent Standards
- `CONTRIBUTING.md` § Agents
