## 1. Tenant 模块并行查询优化

- [x] 1.1 修改 `build_tenant_vo()` 函数使用 `asyncio.gather` 并行查询 5 个资源配置
- [x] 1.2 修改 `get_tenant_resources()` 函数使用 `asyncio.gather` 并行查询
- [x] 1.3 修改 `update_tenant_resources()` 函数使用 `asyncio.gather` 并行查询
- [x] 1.4 修改 `list_tenants()` 函数使用 `asyncio.gather` 并行构建租户响应列表
- [x] 1.5 添加 Tenant 模块并行查询单元测试

## 2. Tenant 模块 Schema 层改进

- [x] 2.1 创建 `TenantDetailResponse` 聚合响应 Schema
- [x] 2.2 实现 `TenantDetailResponse.from_tenant()` 类方法
- [x] 2.3 创建 `ResourceConfigReferenceResponse` Schema
- [x] 2.4 重构 `build_tenant_vo()` 使用新 Schema 转换方法

## 3. IAM 模块 Schema 层改进

- [x] 3.1 创建 `UserRoleItem` Schema 及 `from_role()` 方法
- [x] 3.2 创建 `UserRolesResponse` Schema 及 `from_roles()` 方法
- [x] 3.3 创建 `DepartmentListItem` Schema 及 `from_department()` 方法
- [x] 3.4 创建 `DepartmentListResponse` Schema 及 `from_departments()` 方法
- [x] 3.5 添加 IAM Schema 转换单元测试

## 4. IAM 模块 Controller 层重构

- [x] 4.1 重构 `user_controller.py` 的 `get_user_roles()` 使用 `UserRolesResponse`
- [x] 4.2 重构 `department_controller.py` 的 `list_departments()` 使用 `DepartmentListResponse`
- [x] 4.3 验证 IAM API 响应格式兼容性

## 5. AI 模块 ConversationService 创建

- [x] 5.1 创建 `ai/services/conversation_service.py` 文件
- [x] 5.2 实现 `ConversationService.list_with_message_count()` 聚合方法
- [x] 5.3 实现 `ConversationService.get_or_create()` 聚合方法
- [x] 5.4 实现 `ConversationService.soft_delete()` 聚合方法
- [x] 5.5 实现 `ConversationService.update_name()` 聚合方法
- [x] 5.6 添加 ConversationService 单元测试

## 6. AI 模块 ChatService 创建

- [x] 6.1 创建 `ai/services/chat_service.py` 文件
- [x] 6.2 实现 `ChatService.create_messages()` 聚合方法
- [x] 6.3 实现 `ChatService.update_assistant_message()` 聚合方法
- [x] 6.4 实现 `ChatService.update_conversation_name()` 聚合方法
- [x] 6.5 添加 ChatService 单元测试

## 7. AI 模块 Controller 层重构

- [x] 7.1 重构 `conversation.py` Controller 使用 `ConversationService`
- [x] 7.2 重构 `llm.py` Controller 使用 `ConversationService` 和 `ChatService`
- [x] 7.3 移除 Controller 中的直接数据库操作代码
- [x] 7.4 验证 AI 模块流式响应完整性

## 8. 测试验证与文档更新

- [x] 8.1 运行全量测试套件验证功能正确性
- [x] 8.2 更新 `server/python/CLAUDE.md` 开发规范文档
- [x] 8.3 更新 `server/CLAUDE.md` Service 层规范说明
- [x] 8.4 提交代码并创建 commit message

## 任务依赖关系

```
1.x Tenant 并行优化 ──┐
                     ├──▶ 8.x 测试验证
2.x Tenant Schema ───┘

3.x IAM Schema ──────┐
                     ├──▶ 8.x 测试验证
4.x IAM Controller ──┘

5.x ConversationService ──┐
                          ├──▶ 7.x Controller 重构 ──▶ 8.x 测试验证
6.x ChatService ──────────┘
```

## 风险提示

| 任务组 | 风险等级 | 说明 |
|--------|----------|------|
| 1.x, 2.x | 低 | Tenant 模块改动仅涉及内部优化，API 不变 |
| 3.x, 4.x | 低 | IAM 模块仅改进代码风格，API 不变 |
| 5.x, 6.x, 7.x | 中 | AI 模块涉及流式响应，需仔细验证 |
