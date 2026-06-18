## 为什么

本项目 AI 模块目前仅有 model、plugin 两个组件，缺少加密、数据源连接、代码执行和知识图谱检索等关键能力。Alon 项目中已有成熟的实现且组件间耦合极低，迁移至本项目可快速补齐能力短板。

## 变更内容

从 Alon 项目迁移 4 个独立组件至 `server/python/src/ai/components/`，同时补齐配套基础设施配置和单元测试：

- **新增** `encryption` 组件 — AES/RSA 加密解密、加密管理器、密钥配置
- **新增** `datasource` 组件 — 多数据库连接器（MySQL/PostgreSQL/Oracle/MSSQL/SQLite/ClickHouse/DM）
- **新增** `code_executor` 组件 — 远程沙箱代码执行（Python3/JavaScript/Jinja2）
- **新增** `graphrag` 组件 — 微软 GraphRAG 知识图谱（索引构建 + 查询 + 提示词调优 + Web 服务）
- **新增** sandbox 服务至 Docker Compose 编排
- **新增** 各组件单元测试

## 功能 (Capabilities)

### 新增功能

- `encryption`: 提供 AES/RSA 加解密能力，支持落库加密、前端输入加密、前端输出解密等多种场景，密钥配置通过 YAML 文件管理
- `datasource`: 提供多数据库（MySQL、PostgreSQL、Oracle、MSSQL、SQLite、ClickHouse、达梦）统一连接与方言适配能力
- `code-executor`: 提供远程沙箱代码执行能力，支持 Python3、JavaScript、Jinja2 三种语言，通过 HTTP 调用 Dify Sandbox 服务
- `graphrag`: 提供基于微软 GraphRAG 的知识图谱构建与检索能力，包含索引构建（index）、结构化查询（query）、提示词调优（prompt_tune）和 Web 服务（webserver）四个子系统

### 修改功能

无。本次为纯新增，不影响现有功能。

## 影响

| 影响范围 | 详情 |
|---------|------|
| `server/python/src/ai/components/` | 新增 4 个组件目录，约 495 个文件 |
| `server/python/src/framework/configs/` | 新增 encryption 基础设施配置模型 |
| `server/python/src/framework/common/exceptions.py` | 可能需补齐 BadRequestError 异常类 |
| `docker/docker-compose.backend.yml` | 新增 sandbox 服务定义 |
| `server/python/pyproject.toml` | 补充依赖：pycryptodome、datashaper、tiktoken 等 |
| `server/python/tests/ai/unit/components/` | 新增 4 个组件的单元测试目录 |
