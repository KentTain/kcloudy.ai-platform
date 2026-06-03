# 仓库指南

AI Platform 是一个多技术栈 AI 助手平台演示项目。每个技术栈是独立的子项目 —— 遵循您所在技术栈的约定。

## 文档职责划分

| 文档 | 职责 | 内容 |
|------|------|------|
| **CLAUDE.md** | 技术清单 | 简洁的技术栈清单，便于快速了解技术选型 |
| **README.md** | 技术对比 | 完整技术选型对比、各维度详细对比（框架、ORM、测试框架等） |
| **AGENTS.md** | AI 助手指南 | 文档分层规范、编码约定 |

## 文档分层规范

### CLAUDE.md 层级限制

| 目录层级 | 内容 |
|----------|------|
| `server/CLAUDE.md` | 技术栈总览层 - 技术栈状态、架构概览、各技术栈链接 |
| `server/{技术栈}/CLAUDE.md` | 技术栈层 - 技术栈概述、功能模块清单、开发命令 |
| `server/{技术栈}/src/CLAUDE.md` | 开发目录层 - 各模块开发指南 |
| `server/{技术栈}/src/{模块}/CLAUDE.md` | 模块层 - 模块详细开发指南 |
| `server/{技术栈}/tests/CLAUDE.md` | 测试目录层 - 测试概述和标记 |
| `server/{技术栈}/tests/{模块}/CLAUDE.md` | 模块测试层 - 模块测试规范 |

| 目录层级 | 内容 |
|----------|------|
| `web/CLAUDE.md` | 技术栈总览层 - 技术栈状态表、项目结构概述、子目录链接 |
| `web/{技术栈}/CLAUDE.md` | 技术栈层 - 技术栈概述、功能模块清单、开发命令、子目录链接 |
| `web/{技术栈}/src/CLAUDE.md` | 开发目录层 - 目录结构、模块链接、通用开发规范 |
| `web/{技术栈}/src/{模块}/CLAUDE.md` | 模块层 - 模块详细开发指南 |
| `web/{技术栈}/tests/CLAUDE.md` | 测试目录层 - 测试概述、测试模块链接 |
| `web/{技术栈}/tests/{模块}/CLAUDE.md` | 模块测试层 - 模块测试规范 |

**禁止：** CLAUDE.md 不允许出现在子模块级目录（如 `components/`、`composables/`、`fixtures/`、`unit/`）

### README.md 层级限制

| 目录层级 | 内容 |
|----------|------|
| `server/README.md` | 根目录层 - 技术栈对比、统一架构、快速开始 |
| `server/{技术栈}/README.md` | 技术栈层 - 技术栈功能、环境要求、开发命令、项目结构 |
| `server/{技术栈}/tests/README.md` | 测试目录层 - 测试说明（可选） |

| 目录层级 | 内容 |
|----------|------|
| `web/README.md` | 根目录层 - 技术栈对比、统一架构、快速开始 |
| `web/{技术栈}/README.md` | 技术栈层 - 技术栈功能、环境要求、开发命令、项目结构 |
| `web/{技术栈}/tests/README.md` | 测试目录层 - 测试说明（可选） |

**禁止：** README.md 不允许出现在模块级目录，不深入到模块级（如 `tests/{模块}/README.md`）

### 测试目录结构

| 目录 | 说明 |
|------|------|
| `fixtures/` | 测试夹具和数据（data/ 存放 JSON/YAML，helpers.py 辅助函数） |
| `unit/` | 单元测试（使用 mock 隔离依赖，对应源码目录结构） |
| `integration/` | 集成测试（真实服务交互） |
| `examples/` | 示例代码测试 |
| `studies/` | 代码预研（非正式测试） |

**禁止：** fixtures/、unit/、integration/、studies/ 等子目录下不允许创建 README.md 或 CLAUDE.md

## 项目结构与模块组织

```text
server/python/src/      # demo/, iam/, framework/ 模块
server/python/tests/    # 镜像 src/ 结构
web/vue/src/            # components/, composables/, iam/, tenant/
web/vue/tests/          # 镜像 src/ 结构
docker/                 # Docker Compose 部署
docs/                   # 项目文档
openspec/               # OpenSpec 变更规范
```

其他技术栈（Java, .NET, Rust, React, Flutter）为占位符/计划中 —— 未经明确请求请勿修改。

## 构建、测试与开发命令

### Python 后端 (server/python/)

- `uv sync` — 安装依赖（`--group langchain` 用于 AI 依赖）
- `uv run runserver` — 启动开发服务器 (localhost:8000/docs)
- `uv run pytest` — 运行所有测试；`-m unit` 仅单元测试；`-x` 遇到首个失败即停止
- `uv run format-code` — Ruff 格式化；`uv run check-dev` — lint + 类型检查

### Vue 前端 (web/vue/)

- `pnpm install` — 安装依赖；`pnpm dev` — 开发服务器 (localhost:5173)
- `pnpm build` — 生产构建；`pnpm type-check` — vue-tsc
- `pnpm check:fix` — Biome lint + 格式化自动修复；`pnpm test:unit` — Vitest

## 编码风格与命名约定

- **Python**: Ruff (PT 规则), Python 3.12 目标版本。函数/变量使用 `snake_case`，类使用 `PascalCase`。模块遵循 controllers → services → models 分层。
- **Vue/TS**: Biome lint + 格式化。2 空格缩进，100 字符行宽，双引号，总是使用分号，ES5 尾逗号。组件使用 `PascalCase`，组合式函数使用 `camelCase`。

## 测试指南

- **Python**: pytest + pytest-asyncio。测试在 `tests/{module}/` 下镜像 `src/{module}/`。标记: `unit`, `integration`, `slow`, `db`, `api`, `asyncio`。单元测试不得触及真实服务。集成测试在服务不可用时跳过。测试数据放在 `fixtures/`。
- **Vue**: Vitest + @vue/test-utils。测试在 `tests/` 下镜像 `src/`。

## 提交与拉取请求指南

- **约定式提交**: `type(scope): description`。类型: `feat`, `fix`, `refactor`, `docs`, `chore`。范围: `backend`, `vue`, `database`, `iam`, `framework`, `docker`, `openspec`。
- 已配置 commitizen；使用 `cz commit` 进行引导式提交。
- PR 应引用 issue 并包含清晰描述。
