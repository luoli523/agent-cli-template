# agent-cli-template

> **Language**: [English](README.md) | [中文](README.zh-CN.md)

A scaffold for building **agent-facing CLIs** — command-line tools whose
primary consumer is an AI agent, not a human.

Fork this repo to get a working CLI with a frozen protocol surface
(envelope, exit codes, handle, risk classification, `_notice`) and
standard flags, all exercised by CI from day one.

**Status: v0.1.0** — protocol surface, infrastructure commands, skill
system, rename wizard, and CI are all in place. Real service integrations
are what you add on top.

---

## What you get

| Layer | What it provides |
|-------|-----------------|
| Protocol surface | Envelope, exit codes, error types, handle, risk classification, `_notice` channel |
| Infrastructure commands | `install` / `update` / `doctor` / `validate` / `version` / `hello` |
| Skill validator | Enforces SKILL.md frontmatter + repo conventions |
| `mycli-shared` skill | Runtime protocol that every future service skill inherits |
| `mycli-skill-template` | Fork starting point for sub-team skills |
| `init.py` wizard | Rename `mycli` → your CLI name in ~1 minute |
| CI pipeline | Lint + typecheck + test + validate, Python 3.9 & 3.13 (GitHub Actions + GitLab CI) |

---

## 5-step quickstart

```bash
# 1. Fork + clone
gh repo create my-service-cli --template <this-repo-url> --clone
cd my-service-cli

# 2. Rename (interactive: asks for CLI name, author, email, repo URL)
python init.py

# 3. Install dependencies
uv sync --extra dev

# 4. Smoke test
uv run mycli hello --name World
# → {"ok": true, "identity": "local", "data": {"greeting": "Hello, World!"}}

# 5. Validate the repo
uv run mycli validate
# → {"ok": true, ...}
```

After that: delete `src/mycli/core/hello.py` (and its test), then add
your first real service command.

---

## What this template does NOT include

| Capability | Status |
|-----------|--------|
| Real service integrations | You add those — see [Onboarding a service](docs/explainers/onboarding-a-service.md) |
| `mycli auth login` / OAuth | Pending — design your credential provider chain first |
| MCP server pattern | Deferred — requires a reviewed ADR before code lands |
| PyPI / internal index publish | Add your own release tooling |

---

## Repository layout

```
agent-cli-template/
├── src/mycli/
│   ├── contracts/     Envelope, exit codes, error types, handle, risk, _notice
│   ├── core/          Infrastructure commands (install/update/doctor/validate/version/hello)
│   ├── runtime/       Standard flags, output layer
│   ├── manifest/      --manifest surface emitter
│   └── validators/    SKILL.md frontmatter + repo shape checks
├── skills/
│   ├── mycli-shared/         Runtime protocol every mycli-* skill inherits
│   └── mycli-skill-template/ Fork starting point (NOT installed by `mycli install`)
├── docs/
│   ├── specs/         Normative spec
│   ├── decisions/     ADRs
│   ├── explainers/    Teaching docs
│   └── reference/     Lookup tables
├── tests/             contracts / runtime / core / validators
├── init.py            Rename wizard
├── CLAUDE.md          AI assistant instructions
└── AGENTS.md          Symlink → CLAUDE.md (Codex + Claude Code share one file)
```

---

## Running CI checks locally

```bash
uv run ruff check src tests   # lint
uv run mypy --strict src      # types
uv run pytest -q              # tests
uv run mycli validate         # repo + skills conventions
```

---

## License

MIT — see [LICENSE](LICENSE).
