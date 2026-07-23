## 为什么

kbhub 迁移方案 Phase 3：完整迁移知识库、入库审核、工具库、平台设置功能到 ai 模块，并执行整体集成验收。ai 模块已有 LLM/Embedding/Rerank/插件基础能力，需要扩展知识库管理、入库审核流程、Swagger/MCP 工具库、平台设置，以及知识库成员权限体系。知识库权限不放大源文档权限（回查 document inner 接口）。最后进行跨模块端到端集成验证。

## 变更内容

- ai 模块增补 module.py 菜单和功能权限（知识库/工具/平台设置/入库审核）
- ai 模块知识库：模型、服务、控制器（含成员权限、检索过滤、问答）
- ai 模块入库审核：申请提交、审核流程、站内信通知
- ai 模块工具库：Tool/ToolAuth/ToolFunction/ToolParameter 模型、Swagger 导入（prance + openapi-spec-validator）、MCP 导入（官方 SDK）、工具测试 Runtime（HttpExecutor/McpExecutor）
- ai 模块平台设置：切片参数 + 六类模型配置
- ai 模块前端：知识库页面、工具库页面、平台设置页面、入库审核组件、智能问答页面
- ai schema 数据库迁移 + 种子数据
- 整体集成验收：document→ai 文档引用链路、三层权限端到端、权限申请审批落地、审计日志跨模块、站内信跳转回源校验

## 功能 (Capabilities)

### 新增功能

- `ai-knowledge-base`: 知识库管理（CRUD、文档引用、成员权限、检索测试、问答、图谱、配置、审计）
- `ai-import-review`: 入库审核流程（申请提交、审核处理、站内信通知、引用生成）
- `ai-tool-center`: 工具库（Swagger/MCP 导入、重导入、工具管理、工具测试 Runtime、认证管理、参数树形结构）
- `ai-platform-settings`: 平台设置（切片参数、LLM/Vision/Audio/Video/Embedding/Rerank 六类模型配置）
- `ai-kb-permission`: 知识库成员权限体系（成员角色、ACL、不放大源文档权限的检索过滤）
- `integration-verification`: 整体集成验收（跨模块联调、端到端权限验证、审计一致性、站内信跳转校验）

### 修改功能

- `ai-module-definition`: ai module.py 增补知识库/工具/平台设置/入库审核的菜单和功能权限声明

## 影响

- **后端**：ai 模块新增约 14 个模型、8+ 个服务、6+ 个控制器；module.py 增补菜单和权限
- **数据库**：ai schema 新增 14 张表（knowledge_bases、knowledge_base_members、knowledge_base_documents、knowledge_base_acls、import_requests、import_request_items、tools、tool_auths、tool_functions、tool_parameters、tool_import_records、config_items、conversations、conversation_messages）
- **API**：新增 `/ai/admin/v1/knowledge-bases/*`、`/ai/console/v1/knowledge-bases/*`、`/ai/admin/v1/tools/*`、`/ai/console/v1/platform-settings` 等端点
- **前端**：ai 模块新增 4+ 页面、6+ 专用组件
- **依赖**：ai 依赖 document（inner 接口回查源文件权限）、iam（站内信、审计写入）、framework（权限引擎）
- **外部依赖**：新增 `prance`（OpenAPI 解析）、`openapi-spec-validator`（OpenAPI 校验）、MCP 官方 SDK
- **兼容性**：无破坏性变更，所有新增为增量
