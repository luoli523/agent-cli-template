# MCP Servers

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Model Context Protocol (MCP) servers that expose live DI service APIs as tools the AI can call at runtime. **Currently empty placeholder** — no MCP servers are shipped, and the first one requires a reviewed design before landing.

## When to contribute here

Add an MCP server when:

- An AI workflow needs to **call a real DI service** (DataMap, Scheduler, DQC, etc.) rather than just describe how to.
- A skill alone (knowledge + the user runs commands) is insufficient — the AI needs to actually invoke the API.
- The service owner is identified and has approved the integration scope.
- Authentication, side effects, and confirmation requirements are documented (per `CONTRIBUTING.md` § MCP Contributions).

## Authoring format

Each MCP server lives under `mcp/<name>/` with:

- A server implementation (stdio or SSE; Python preferred).
- A manifest declaring exposed tools, input/output schemas, side-effect classification (read-only / consuming / mutating / destructive).
- A README documenting auth model, error shape, pagination, confirmation behavior, and local-run/test instructions.

Tools are registered into AI clients via `claude mcp add` (or the equivalent for Codex). The future `di` installer will handle this; today it is manual.

## Validator

The validator does not yet check MCP server structure. CI does not run MCP servers. The first contribution should be paired with an ADR in `docs/decisions/` that captures the design decisions for the directory.

## See also

- `CONTRIBUTING.md` § MCP Contributions — required questions to answer before merging
- `CLAUDE.md` § MCP — placeholder boundary
