## 上下文

ai 模块已有 LLM/Embedding/Rerank/插件/GraphRAG/代码执行器等基础能力，但无知识库、入库审核、工具库、平台设置功能。Phase 2 已完成 document 模块（文档库、文件管理、资源权限、inner 接口）。Phase 3 需扩展 ai 模块实现知识库管理、入库审核、工具库、平台设置，并执行整体集成验收。

知识库文档来源于 document 文件，ai 模块通过 document inner 接口回查源文件权限，不放大权限。工具库需支持 Swagger/MCP 导入和统一测试 Runtime。

## 目标 / 非目标

**目标：**
- 实现知识库管理（CRUD、文档引用、成员权限、检索测试、问答、图谱、配置、审计）
- 实现入库审核流程（申请提交、审核处理、站内信通知、引用生成）
- 实现工具库（Swagger/MCP 导入、重导入、工具管理、测试 Runtime、认证管理、参数树形）
- 实现平台设置（切片参数 + 六类模型配置）
- 实现知识库成员权限体系（不放大源文档权限的检索过滤）
- ai module.py 增补菜单和功能权限
- 整体集成验收（跨模块联调、端到端权限、审计一致性、站内信跳转校验）

**非目标：**
- 不重复实现 document 已有的文件管理（ai 通过 inner 接口回查）
- 不改动 ai 现有 LLM/插件/GraphRAG 基础能力
- 不实现企业 Policy 模型（Phase 1 已在 iam 实现，ai 调用求值器）
- 不实现权限申请审批（Phase 1 已在 iam 实现，ai 提供 apply 回调 inner 接口）

## 决策

### 决策 1：知识库权限不放大源文档权限

**选择**：问答检索前按权限生成可访问范围，检索后对召回片段再次过滤，无权限片段不进入 LLM prompt。回查源文件权限走 `GET /document/inner/v1/documents/{id}/permission?user_id=`。

**理由**：kbhub 权限依赖关系设计核心规则，安全要求。

**替代方案**：知识库成员身份即授予源文档权限 → 越权风险，否决。

### 决策 2：工具库统一 Runtime 按 protocol 分发

**选择**：`ToolRuntime` 按 `Tool.protocol`（http/mcp）分发 `HttpExecutor`/`McpExecutor`，Connection Test 和 Function Test 共用协议分发。新增协议只加 Executor，不改 Controller/Service/响应契约。

**理由**：kbhub 工具库设计方案成熟（`docs/features/14.工具库.md`），架构清晰。

### 决策 3：Swagger 用 prance + openapi-spec-validator，MCP 用官方 SDK

**选择**：Swagger 导入用 `openapi-spec-validator` 校验 + `prance` 解析 $ref；MCP 导入用官方 SDK 的 SSE/Streamable HTTP 调用 `tools/list`，不自行解析协议。

**理由**：kbhub 设计明确要求，避免自行解析 MCP 协议的风险。

### 决策 4：工具库数据模型不区分 Swagger/MCP

**选择**：统一 Tool/ToolAuth/ToolFunction/ToolParameter 模型，Swagger 和 MCP 仅作为 Tool.source 和 Tool.protocol 的不同值。

**理由**：kbhub 设计核心原则，数据库不区分来源，便于扩展 GraphQL/Workflow 等协议。

### 决策 5：平台设置保存到 ai.config_items

**选择**：平台设置保存到 `ai.config_items`（config_scope=tenant，config_key=kbhub_platform_settings），含切片参数和六类模型配置。模型选择复用 ai 模块现有模型能力。

**理由**：迁移方案 §5.2 已确认，平台设置属 AI 能力范畴。

### 决策 6：入库审核通过站内信承载

**选择**：申请提交后写 import_requests，通过 iam 站内信通知审核员；审核通过生成 knowledge_base_documents 引用。

**理由**：kbhub 设计，站内信作为消息入口，跳转后回源校验权限。

### 决策 7：重导入策略——保留 Tool/ToolAuth，删除 Function/Parameter 重建

**选择**：重导入保留 Tool 和 ToolAuth，删除 ToolFunction 和 ToolParameter 重新解析创建，按 operation_id+schema_path 暂存恢复人工维护字段（ai_description/example/sort/enabled）。

**理由**：kbhub 设计，V1 方案全删全增更简单稳定。

## 风险 / 权衡

- **[工具库外部依赖]** prance/openapi-spec-validator/MCP SDK 新增依赖 → 在 pyproject.toml 添加，版本锁定
- **[MCP 连接稳定性]** MCP Server 连接可能失败/超时 → 连接超时配置（15s 下载、SSE 读取超时），失败记录 ToolImportRecord
- **[工具测试安全]** Function Test 可能产生写操作 → 仅超管可调用，返回请求摘要脱敏（不泄露 token/api_key）
- **[知识库检索性能]** 权限过滤 + 向量检索组合 → 先按权限生成可访问范围再检索，检索后二次过滤
- **[跨模块联调]** document→ai 依赖链路 → Phase 2 已先行，inner 接口稳定；集成验收覆盖端到端
- **[图谱治理]** GraphRAG 聚合多来源文档 → 按来源过滤，不暴露无权限来源

## 迁移计划

1. ai module.py 增补菜单和权限
2. 知识库模型（KnowledgeBase/Member/Document/Acl）
3. 入库审核模型（ImportRequest/ImportRequestItem）
4. 工具库模型（Tool/ToolAuth/ToolFunction/ToolParameter/ImportRecord）
5. 平台设置模型（ConfigItem）
6. 知识库服务（含检索过滤）
7. 入库审核流程服务 + 站内信通知
8. 工具库服务（Swagger/MCP 导入 + Runtime）
9. 平台设置服务
10. 控制器（admin/console/inner）
11. 数据库迁移 + 种子
12. 监听器与定时任务
13. 前端 API/类型/stores
14. 前端页面（知识库、工具库、平台设置、智能问答）
15. 前端专用组件迁移适配
16. 前端单元测试 + E2E
17. 整体集成验收（4 项端到端）

**回滚**：全部为增量，回滚删除 ai 新增表和代码即可。

## 待解决问题

- MCP SDK 版本和接入方式细节 → 实现时确认官方 SDK 的 SSE/Streamable HTTP Client API
- 知识库问答消息格式是否复用现有 ai-elements 的 UIMessage data stream protocol → 建议复用（项目规范已采用 @ai-sdk/vue）
- 图谱治理范围（一期是否实现）→ 建议一期基础检索，图谱治理作为后续增强
