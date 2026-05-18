# agent-cli-template

> **语言**：[English](README.md) | [中文](README.zh-CN.md)

一个用于构建 **agent-facing CLI** 的脚手架模板——命令行工具的主要消费者是 AI agent，而非人类。

Fork 本 repo 即可获得一个开箱即用的 CLI，内置冻结协议层（envelope、exit codes、handle、risk 分级、`_notice` 通道）和标准 flag，所有内容从第一天起就有 CI 保障。

**状态：v0.1.0** ——协议层、基础设施命令、skill 体系、改名向导和 CI 全部就位。真正的服务集成是你在这之上叠加的内容。

---

## 你得到什么

| 层级 | 提供内容 |
|------|---------|
| 协议层 | Envelope、exit codes、error types、handle、risk 分级、`_notice` 通道 |
| 基础设施命令 | `install` / `update` / `doctor` / `validate` / `version` / `hello` |
| Skill 校验器 | 强制校验 SKILL.md frontmatter + 仓库结构规范 |
| `mycli-shared` skill | 每个未来服务 skill 继承的运行时协议 |
| `mycli-skill-template` | 子团队 skill 的 fork 起点 |
| `init.py` 向导 | 一分钟内将 `mycli` 改名为你的 CLI 名称 |
| CI 流水线 | Lint + 类型检查 + 测试 + validate，支持 Python 3.9 & 3.13（GitHub Actions + GitLab CI）|

---

## 5 步快速上手

```bash
# 1. Fork + clone
gh repo create my-service-cli --template <this-repo-url> --clone
cd my-service-cli

# 2. 改名（交互式：询问 CLI 名称、作者、邮箱、repo URL）
python init.py

# 3. 安装依赖
uv sync --extra dev

# 4. 冒烟测试
uv run mycli hello --name World
# → {"ok": true, "identity": "local", "data": {"greeting": "Hello, World!"}}

# 5. 校验仓库
uv run mycli validate
# → {"ok": true, ...}
```

之后：删除 `src/mycli/core/hello.py`（及其测试），然后添加你的第一个真实服务命令。

---

## 模板不包含的内容

| 能力 | 状态 |
|-----|------|
| 真实服务集成 | 由你添加——见[服务接入指南](docs/explainers/onboarding-a-service.md) |
| `mycli auth login` / OAuth | 待定——请先设计你的 credential provider chain |
| MCP server 模式 | 延后——需要经过审核的 ADR 才能落地 |
| PyPI / 内部 index 发布 | 自行添加发布工具链 |

---

## 仓库结构

```
agent-cli-template/
├── src/mycli/
│   ├── contracts/     Envelope、exit codes、error types、handle、risk、_notice
│   ├── core/          基础设施命令（install/update/doctor/validate/version/hello）
│   ├── runtime/       标准 flag、输出层
│   ├── manifest/      --manifest 命令
│   └── validators/    SKILL.md frontmatter + 仓库结构校验
├── skills/
│   ├── mycli-shared/         每个 mycli-* skill 继承的运行时协议
│   └── mycli-skill-template/ fork 起点（不被 `mycli install` 安装）
├── docs/
│   ├── specs/         规范文档
│   ├── decisions/     ADR
│   ├── explainers/    教学文档
│   └── reference/     查阅手册
├── tests/             contracts / runtime / core / validators
├── init.py            改名向导
├── CLAUDE.md          AI 助手指令文件
└── AGENTS.md          软链接 → CLAUDE.md（Codex 和 Claude Code 共享同一份文件）
```

---

## 本地运行 CI 检查

```bash
uv run ruff check src tests   # lint
uv run mypy --strict src      # 类型检查
uv run pytest -q              # 测试
uv run mycli validate         # 仓库 + skill 结构校验
```

---

## 许可证

MIT——见 [LICENSE](LICENSE)。
