# di-cli-internal

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

`di-cli-internal` 是面向 Data Infra 内部开发者、service owner、业务团队和 on-call 工程师的共享 DI Toolkit。

这个项目希望把 DI 内部各团队自用、各自维护的 AI 工具集逐步收拢到一个可共同维护的仓库里：skills、agents、service 文档、rules、contexts、MCP 模式，以及未来的 Python CLI 工具。认证也会集中管理，避免每个团队或每个 skill 重复实现登录和凭证处理。

把这些工具沉淀到同一个项目后，各业务团队既可以让别人用到自己的知识和流程积累，也可以直接复用其他团队已经整理好的工具。目标是减少重复开发，让排障经验、运维流程、服务知识和自动化能力在 DI 内部相互借鉴、相互赋能，而不是分散在多个仓库和私有脚本里。

## 当前状态

当前是 scaffold 阶段，但已经包含一个真实 skill：[`di-mr-flow`](skills/di-mr-flow/SKILL.md)，用于规范本仓库的 GitLab MR 流程。

当前已可用：

- skills、agents、service docs、MCP patterns、rules、contexts 和未来 CLI 的仓库约定。
- `di-mr-flow`：覆盖建分支、commit、push、创建 MR、等待 CI、squash 合入和本地清理。
- `bash scripts/validate.sh`：仓库规范和安全校验。
- `uv run pytest tests/ -q`：pytest 规范测试。
- 可选 `.githooks/pre-commit`：启用后在 commit 前自动运行校验。
- `config/prefixes.json` 中的命名前缀体系；当前 skill 名必须使用已声明的 `di-` 前缀。

尚未实现：

- 真实 `di` CLI 命令。
- 集中的 Google 个人账号认证。
- 生产 MCP server。
- 具体 service 的生产集成。
- 除占位说明外，尚未发布 agents、contexts 或 rules。

## 快速开始

Python 依赖使用 `uv` 管理。依赖声明在 `pyproject.toml`，锁定版本在 `uv.lock`。

首次初始化：

```bash
uv sync --extra dev
```

提交前运行仓库校验：

```bash
bash scripts/validate.sh
uv run pytest tests/ -q
```

validator 依赖 `.venv/`，它由 `uv sync --extra dev` 创建。不要提交 `.venv/`、本地 credential 文件或生成的 auth cache。

启用可选 pre-commit hook：

```bash
git config core.hooksPath .githooks
```

## 目标

- 提供一套 DI 开发者和业务团队可以统一安装、更新和复用的内部工具集。
- 逐步收拢各团队维护的 AI toolkit，让知识、工作流和辅助脚本能在 DI 内部复用。
- 让各 service owner 用统一格式贡献 skills、agents、service docs、scripts 和 MCP 示例。
- 未来通过 Python CLI 集中管理认证和凭证，避免每个团队 toolkit 或每个 skill 重复处理登录逻辑。
- 同时兼容 Claude Code 和 Codex，并共享同一份项目指令。
- 明确 service owner、权限边界、安全要求和 review 预期。

## 目录结构

```text
cli/                 未来 Python CLI 实现的占位目录。
skills/              按需加载的 DI skills；当前包含 di-mr-flow。
agents/              空占位目录；authoring guidance 见 agents/README.md。
mcp/                 未来 MCP server patterns 的空占位目录。
docs/services/       service owner 维护的服务文档；当前为空。
docs/decisions/      架构决策记录。
rules/               可选常驻规则的空占位目录。
contexts/            工作模式 prompt 的空占位目录。
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

鼓励业务和 service 团队把各自维护的 AI toolkit 逐步迁移到本仓库。建议先迁移稳定的知识文档、只读工作流和 scaffold skill，再考虑接入会调用生产服务的集成。

接入真实 service 前，需要先明确 service owner、认证模型、安全边界和测试策略。

## 安全要求

不要提交真实 token、cookie、private key、OAuth refresh token、个人凭证或生产 secret。所有 credential 示例必须使用占位符。

AI coding assistant 的工作规则见 `CLAUDE.md`。
