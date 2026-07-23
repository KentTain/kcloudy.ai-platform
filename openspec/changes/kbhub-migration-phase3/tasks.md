## 1. 模块声明增补

- [ ] 1.1 ai `module.py` 增补菜单（知识库/工具库/平台设置/入库审核）
- [ ] 1.2 ai `module.py` 增补功能权限 PermissionDef（knowledge_base/tool/platform_settings/import）
- [ ] 1.3 验证权限码同步到租户实例层

## 2. 知识库模型

- [ ] 2.1 新建 `ai/models/knowledge_base.py`（KnowledgeBase/Member/Document/Acl 模型）
- [ ] 2.2 新建 `ai/models/enums.py` 增补知识库相关枚举（成员角色、引用状态等）
- [ ] 2.3 验证模型可映射

## 3. 入库审核模型

- [ ] 3.1 新建 `ai/models/import_request.py`（ImportRequest/ImportRequestItem 模型）
- [ ] 3.2 验证模型可映射

## 4. 工具库模型

- [ ] 4.1 新建 `ai/models/tool.py`（Tool/ToolAuth/ToolFunction/ToolParameter/ToolImportRecord 模型）
- [ ] 4.2 ToolParameter 支持树形结构（parent_id）
- [ ] 4.3 验证模型可映射

## 5. 平台设置模型

- [ ] 5.1 新建 `ai/models/config_item.py`（ConfigItem 模型，config_scope/config_key/config_value）
- [ ] 5.2 验证模型可映射

## 6. 知识库服务

- [ ] 6.1 新建 `ai/services/knowledge_base/kb_service.py`（知识库 CRUD）
- [ ] 6.2 新建 `ai/services/knowledge_base/member_service.py`（成员权限管理）
- [ ] 6.3 新建 `ai/services/knowledge_base/document_service.py`（文档引用管理）
- [ ] 6.4 新建 `ai/services/knowledge_base/retrieval_service.py`（检索测试+权限过滤）
- [ ] 6.5 新建 `ai/services/knowledge_base/chat_service.py`（知识库问答，不放大源文档权限）
- [ ] 6.6 实现检索前后双重权限过滤（前生成可访问范围，后过滤召回片段）
- [ ] 6.7 回查源文件权限走 document inner 接口
- [ ] 6.8 知识库服务单元测试

## 7. 入库审核服务

- [ ] 7.1 新建 `ai/services/import_review/import_service.py`（申请提交+审核流程）
- [ ] 7.2 审核通过生成知识库文档引用
- [ ] 7.3 通过 framework 站内信辅助通知审核员/申请人
- [ ] 7.4 入库审核流程测试

## 8. 工具库服务

- [ ] 8.1 新建 `ai/services/tool/tool_service.py`（工具管理 CRUD）
- [ ] 8.2 新建 `ai/services/tool/swagger_import.py`（Swagger 导入，prance + openapi-spec-validator）
- [ ] 8.3 新建 `ai/services/tool/mcp_import.py`（MCP 导入，官方 SDK SSE/Streamable HTTP）
- [ ] 8.4 新建 `ai/services/tool/tool_runtime.py`（测试 Runtime，HttpExecutor/McpExecutor）
- [ ] 8.5 实现重导入策略（保留Tool/ToolAuth，删除Function/Parameter重建，恢复人工字段）
- [ ] 8.6 实现敏感信息脱敏（token/api_key/password 替换为 ******）
- [ ] 8.7 工具库服务单元测试（导入/重导入/测试Runtime/脱敏）

## 9. 平台设置服务

- [ ] 9.1 新建 `ai/services/platform_settings.py`（切片参数+六类模型配置）
- [ ] 9.2 切片参数校验（最大重合长度 < 切片最大长度）
- [ ] 9.3 模型配置保存规则（LLM/Vision/Video保留completion_params，其他不保存）
- [ ] 9.4 平台设置服务测试

## 10. 控制器

- [ ] 10.1 新建 `ai/controllers/admin/knowledge_base.py`（知识库管理端）
- [ ] 10.2 新建 `ai/controllers/console/knowledge_base.py`（知识库问答/检索/入库用户端）
- [ ] 10.3 新建 `ai/controllers/admin/tool.py`（工具库管理端）
- [ ] 10.4 新建 `ai/controllers/console/tool.py`（工具库测试用户端）
- [ ] 10.5 新建 `ai/controllers/console/platform_settings.py`（平台设置）
- [ ] 10.6 新建 `ai/controllers/inner/`（权限申请apply回调、知识库文档引用查询）
- [ ] 10.7 新建 schemas（请求/响应 DTO）
- [ ] 10.8 控制器接口测试

## 11. 监听器与定时任务

- [ ] 11.1 新建 `ai/listeners/`（入库审核消息、索引任务回调）
- [ ] 11.2 新建 `ai/tasks/`（索引恢复补偿、审核超时监控）
- [ ] 11.3 任务可调度验证

## 12. 数据库迁移与种子

- [ ] 12.1 新建 ai 迁移脚本（14张表）
- [ ] 12.2 新建 ai 种子数据（默认知识库配置、工具导入枚举）
- [ ] 12.3 执行迁移并验证表结构

## 13. 前端基础

- [ ] 13.1 新建 `web/vue/src/ai/api/` 增补知识库/工具库/平台设置 API
- [ ] 13.2 新建 `web/vue/src/ai/types/` 增补类型定义
- [ ] 13.3 新建 `web/vue/src/ai/stores/` 增补状态
- [ ] 13.4 类型校验通过

## 14. 前端页面

- [ ] 14.1 新建知识库列表页（`/ai/knowledge-base`）
- [ ] 14.2 新建知识库详情页（概览/文档/成员/检索/图谱/审批/配置/审计）
- [ ] 14.3 新建工具库页面（`/ai/tools`，导入/列表/详情/测试）
- [ ] 14.4 新建平台设置页面（`/ai/platform-settings`）
- [ ] 14.5 新建智能问答页面（复用 ai-elements）
- [ ] 14.6 页面联调接口通过

## 15. 前端专用组件

- [ ] 15.1 迁移适配知识库布局组件
- [ ] 15.2 迁移适配入库审核组件（申请列表+审核详情）
- [ ] 15.3 迁移适配检索测试组件
- [ ] 15.4 迁移适配工具库组件（导入/列表/详情/测试）
- [ ] 15.5 迁移适配模型选择组件（AlonLargeModel → 适配本项目模型能力）
- [ ] 15.6 组件复用本项目 UI 规范

## 16. 前端测试

- [ ] 16.1 前端单元测试
- [ ] 16.2 E2E 基础流程（知识库问答、工具导入、平台设置）

## 17. 整体集成验收

- [ ] 17.1 document→ai 文档引用链路端到端验证（入库审核→知识库文档可见→问答）
- [ ] 17.2 三层权限端到端验证（RBAC+资源权限+Policy协同）
- [ ] 17.3 权限申请审批落地验证（iam→document/ai回调授权）
- [ ] 17.4 审计日志跨模块查询一致验证
- [ ] 17.5 站内信跳转回源校验验证
- [ ] 17.6 知识库不放大源文档权限验证
- [ ] 17.7 企业 Policy 跨模块生效验证
