## 1. 文档准备

- [ ] 1.1 更新 `server/python/src/CLAUDE.md`（模块导航、依赖边界含 document）
- [ ] 1.2 创建 `server/python/src/document/CLAUDE.md`（模块定位、目录职责、接口分层）
- [ ] 1.3 更新 `server/python/src/ai/CLAUDE.md`（补充知识库/工具库/平台设置）
- [ ] 1.4 更新 `server/python/src/iam/CLAUDE.md`（补充站内信/权限申请/Policy）
- [ ] 1.5 更新 `server/python/src/framework/CLAUDE.md`（补充权限引擎/审计写入/站内信辅助）
- [ ] 1.6 更新前端各模块 CLAUDE.md（document/ai/iam 对应文档）

## 2. framework 基础设施

- [ ] 2.1 新建 `framework/permission/engine.py`（权限判定引擎接口，编排第2层+第3层）
- [ ] 2.2 新建 `framework/permission/policy_evaluator.py`（企业 Policy 求值器，deny优先）
- [ ] 2.3 新建 `framework/permission/audit_writer.py`（审计日志统一写入辅助，延迟导入iam）
- [ ] 2.4 新建 `framework/notification/sender.py`（站内信发送辅助）
- [ ] 2.5 framework 单元测试（权限引擎、Policy求值、审计写入、站内信发送）

## 3. iam 站内信

- [ ] 3.1 新建 `iam/models/notification.py`（Notification/NotificationRead 模型）
- [ ] 3.2 新建 `iam/schemas/notification.py`（请求/响应 DTO）
- [ ] 3.3 新建 `iam/services/notification_service.py`（发送/查询/已读）
- [ ] 3.4 新建 `iam/controllers/admin/notification_controller.py`（管理端）
- [ ] 3.5 新建 `iam/controllers/console/notification_controller.py`（用户端）
- [ ] 3.6 iam 站内信接口测试

## 4. iam 权限申请

- [ ] 4.1 新建 `iam/models/permission_request.py`（PermissionRequest/PermissionCacheEvent 模型）
- [ ] 4.2 新建 `iam/schemas/permission_request.py`（请求/响应 DTO）
- [ ] 4.3 新建 `iam/services/permission_request_service.py`（提交/审批/回调inner接口）
- [ ] 4.4 新建 `iam/controllers/admin/permission_request_controller.py`（管理端）
- [ ] 4.5 新建 `iam/controllers/console/permission_request_controller.py`（工作台我的/待审批）
- [ ] 4.6 iam 权限申请接口测试

## 5. iam 企业 Policy

- [ ] 5.1 新建 `iam/models/policy.py`（Policy 模型）
- [ ] 5.2 新建 `iam/schemas/policy.py`（请求/响应 DTO）
- [ ] 5.3 新建 `iam/services/policy_service.py`（CRUD/启用/停用/命中审计）
- [ ] 5.4 新建 `iam/controllers/admin/policy_controller.py`（管理端）
- [ ] 5.5 iam Policy 接口测试

## 6. iam 组织/用户增强

- [ ] 6.1 增强 `iam/services/organization_service.py`（人员组织选择器接口）
- [ ] 6.2 增强 `iam/services/user_service.py`（用户搜索/选择接口）
- [ ] 6.3 iam 组织/用户接口测试

## 7. iam 数据库迁移与种子

- [ ] 7.1 新建 iam 迁移脚本（notifications/notification_reads/permission_requests/permission_cache_events/policies 五张表）
- [ ] 7.2 新建 iam 种子数据（默认 Policy、权限申请类型枚举）
- [ ] 7.3 执行迁移并验证表结构

## 8. iam 前端

- [ ] 8.1 新建 `web/vue/src/iam/pages/notifications.vue`（站内信页面）
- [ ] 8.2 新建 `web/vue/src/iam/pages/permission-requests.vue`（权限申请页面）
- [ ] 8.3 新建 `web/vue/src/iam/pages/policies.vue`（企业 Policy 页面）
- [ ] 8.4 迁移适配站内信组件（列表+详情+跳转）
- [ ] 8.5 迁移适配权限排障面板组件
- [ ] 8.6 iam 前端单元测试 + E2E 基础流程
