<!-- CODEGRAPH_START -->
## CodeGraph

本项目已配置 CodeGraph MCP 服务器（`codegraph_*` 工具）。CodeGraph 是基于 tree-sitter 解析的知识图谱，包含所有符号、边和文件信息。读取速度在毫秒级，返回的结构化信息是 grep 无法比拟的。

### 何时优先使用 CodeGraph

使用 CodeGraph 解决**结构性**问题 —— 谁调用了谁、改动会影响什么、X 在哪里定义、X 的签名是什么。使用原生 grep/read 仅限于**字面文本**查询（字符串内容、注释、日志消息）或已有特定文件打开时。

| 问题 | 工具 |
|---|---|
| "X 在哪里定义？" / "查找名为 X 的符号" | `codegraph_search` |
| "谁调用了函数 Y？" | `codegraph_callers` |
| "Y 调用了什么？" | `codegraph_callees` |
| "X 如何到达/变成 Y？/ 追踪从 X 到 Y 的流程" | `codegraph_trace` (一次调用 = 完整路径，包括回调/React/JSX 动态跳转) |
| "如果我修改 Z 会影响什么？" | `codegraph_impact` |
| "显示 Y 的签名 / 源码 / 文档字符串" | `codegraph_node` |
| "为某个任务/区域提供聚焦的上下文" | `codegraph_context` |
| "一次性查看多个相关符号的源码" | `codegraph_explore` |
| "查看 path/ 下有哪些文件" | `codegraph_files` |
| "索引是否健康？" | `codegraph_status` |

### 使用经验法则

- **直接回答 —— 不要委托探索。** 对于 "X 如何工作" / 架构问题，使用 2-3 个 codegraph 调用：先用 `codegraph_context`，然后用一个 `codegraph_explore` 获取它展示的符号源码。对于具体的**流程**（"X 如何到达 Y"），从 from→to 开始使用 `codegraph_trace` —— 一次调用返回完整路径并桥接动态跳转 —— 然后用一个 `codegraph_explore` 获取代码体；不要用 `codegraph_search` + `codegraph_callers` 重建路径。Codegraph 已经是预构建的索引，所以启动单独的文件读取子任务/代理 —— 或运行 grep + read 循环 —— 都会重复 codegraph 已完成的工作，成本更高且结果相同。
- **信任 codegraph 结果。** 它们来自完整的 AST 解析。不要用 grep 重新验证 —— 那更慢、准确性更低，且浪费上下文。
- **查找符号名称时不要先 grep。** `codegraph_search` 更快，且一次调用返回类型 + 位置 + 签名。
- **不要链式调用 `codegraph_search` + `codegraph_node`** 当只需要上下文时 —— `codegraph_context` 一次调用即可。
- **不要对多个符号循环调用 `codegraph_node`** —— 一个 `codegraph_explore` 调用会在单次受限调用中返回多个符号的源码，而每个单独的 node/Read 调用都会重新读取整个上下文，成本高得多。
- **索引延迟**：文件监视器在写入后约 500ms 去抖；不要在同一轮次编辑文件后立即重新查询。

### 如果 `.codegraph/` 不存在

MCP 服务器会返回 "not initialized." 此时询问用户：*"我注意到本项目尚未初始化 CodeGraph。是否需要运行 `codegraph init -i` 来构建索引？"*
<!-- CODEGRAPH_END -->

# 仓库指南

InitProject 是一个多技术栈 AI 助手平台演示项目。每个技术栈是独立的子项目 —— 遵循您所在技术栈的约定。

## 文档职责划分

| 文档 | 职责 | 内容 |
|------|------|------|
| **CLAUDE.md** | 技术清单 | 简洁的技术栈清单，便于快速了解技术选型 |
| **README.md** | 技术对比 | 完整技术选型对比、各维度详细对比（框架、ORM、测试框架等） |
| **AGENTS.md** | AI 助手指南 | CodeGraph 使用规范、文档分层规范、编码约定 |

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
