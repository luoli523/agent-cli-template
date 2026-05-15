# MCP Servers（MCP 服务器）

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

Model Context Protocol (MCP) 服务器——把真实 DI 服务 API 暴露成 AI 在运行时可调用的工具。**当前为空占位**——暂未附 MCP 服务器；第一个 MCP 必须先有 reviewed design 才能落地。

## 什么时候在这里贡献

什么时候该加 MCP server：

- 某个 AI 工作流需要**真实调用** DI 服务（DataMap、Scheduler、DQC 等），不只是"告诉用户怎么调"。
- 仅靠 skill（知识 + 用户自己跑命令）不够——AI 需要**自己**调 API。
- 服务 owner 已确认并同意集成范围。
- 认证、副作用、确认行为已按 `CONTRIBUTING.md` § MCP Contributions 写好。

## 编写格式

每个 MCP 服务器位于 `mcp/<name>/`：

- server 实现（stdio 或 SSE；Python 优先）。
- manifest 声明：暴露的 tools、输入输出 schema、副作用等级（只读 / 消耗资源 / 修改状态 / 破坏性）。
- README 说明：认证模型、error shape、分页、确认行为、本地运行 / 测试方式。

工具通过 `claude mcp add`（或 Codex 对应命令）注册到 AI 工具。未来 `di` 安装器会自动处理；当前手动。

## Validator 行为

validator 暂不检查 MCP server 结构，CI 不运行 MCP server。第一个 MCP 贡献应**配套一份 ADR** 落在 `docs/decisions/`，确立本目录的设计决策。

## 参考

- `CONTRIBUTING.md` § MCP Contributions —— 合入前必须回答的问题清单
- `CLAUDE.md` § MCP —— 占位边界说明
