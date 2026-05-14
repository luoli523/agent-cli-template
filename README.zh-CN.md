# di-cli

`di-cli` 是面向 Data Infra 内部开发者、service owner 和 on-call 工程师的 DI Toolkit。

这个项目会把 DI 内部 AI 助手能力整理成一个可共同维护的仓库：skills、agents、MCP 示例、service 文档、rules、contexts，以及未来的 Python CLI 工具。当前阶段先搭建项目骨架和贡献边界，不接入真实生产服务。

## 当前状态

初始 scaffold。真实 CLI 命令、Google 个人账号认证、生产 MCP server、具体 service tools 会在后续阶段逐步加入。

## 快速开始

Python 依赖使用 `uv` 管理。依赖声明在 `pyproject.toml`，锁定版本在 `uv.lock`。

首次初始化：

```bash
uv sync
```

提交前运行仓库校验：

```bash
bash scripts/validate.sh
```

validator 依赖 `.venv/`，它由 `uv sync` 创建。不要提交 `.venv/`、本地 credential 文件或生成的 auth cache。

## 目标

- 提供一套 DI 开发者可以统一安装和更新的内部工具集。
- 让各 service owner 用统一格式贡献 skills、agents、service docs、scripts 和 MCP 示例。
- 未来通过 Python CLI 集中管理认证和凭证，避免每个 skill 重复处理登录逻辑。
- 同时兼容 Claude Code 和 Codex，并共享同一份项目指令。
- 明确 service owner、权限边界、安全要求和 review 预期。

## 目录结构

```text
cli/                 未来的 Python CLI 实现。
skills/              按需加载的 DI skills。
agents/              兼容 Claude Code 和 Codex 的 agent 定义。
mcp/sample/          MCP 示例占位目录，用于沉淀未来模式。
docs/services/       service owner 维护的服务文档。
docs/decisions/      架构决策记录。
rules/               可选安装的简短常驻规则。
contexts/            dev、review、research、oncall 等工作模式。
config/              profiles、prefixes、credential templates。
scripts/             install、validate、doctor 等脚本。
tests/               目录、规范和 scaffold 校验。
CLAUDE.md            共享项目指令。
AGENTS.md            指向 CLAUDE.md 的软链接，供 Codex 读取。
```

## 计划中的 CLI

未来 CLI 使用 Python 实现，并使用 `di` 命令命名空间。

```bash
di install
di update
di auth login
di auth status
di auth logout
di doctor
```

在这些命令真正实现之前，请把本仓库视为 scaffold，不要在文档里把未实现命令描述成可用能力。

## 贡献模型

每次贡献都应该落在一个清晰的区域：

- `skills/`：DI 任务工作流、运维知识、辅助脚本。
- `agents/`：职责明确、权限克制的 AI 子代理。
- `docs/services/`：service owner 维护的服务说明、接入文档、API 摘要和排障手册。
- `mcp/`：sample 或未来 MCP server 模式，必须清楚标注 side effect。
- `config/`：只放模板，不放真实凭证。

接入真实 service 前，需要先明确 service owner、认证模型、安全边界和测试策略。

## 安全要求

不要提交真实 token、cookie、private key、OAuth refresh token、个人凭证或生产 secret。所有 credential 示例必须使用占位符。

AI coding assistant 的工作规则见 `CLAUDE.md`。
