## 为什么

kbhub 迁移方案 Phase 1：为 document 和 ai 模块的迁移奠定基础设施。当前项目缺少权限判定引擎、审计统一写入、站内信、权限申请、企业 Policy 等基础能力，这些是 Phase 2（document）和 Phase 3（ai）的前置依赖。同时各模块的 CLAUDE.md 文档需要更新以反映迁移后的架构。

## 变更内容

- framework 新增权限判定引擎接口、企业 Policy 求值器、审计日志统一写入辅助、站内信发送辅助
- iam 新增站内信模型与服务（Notification / NotificationRead）
- iam 新增权限申请模型与服务（PermissionRequest，含审批回调 inner 接口）
- iam 新增企业 Policy 模型与服务
- iam 增强组织/用户服务（对接人员组织选择器需求）
- 更新各模块 CLAUDE.md 文档（document/ai/iam/framework + 前端对应模块）
- iam 数据库迁移 + 种子数据

## 功能 (Capabilities)

### 新增功能

- `permission-engine`: framework 权限判定引擎接口与 Policy 求值器，供各业务模块接入三层权限架构
- `audit-writer`: framework 审计日志统一写入辅助，封装 iam.audit_logs 写入逻辑
- `notification-sender`: framework 站内信发送辅助，供各模块调用发送通知
- `iam-notification`: iam 站内信完整功能（模型、服务、控制器、前端页面）
- `iam-permission-request`: iam 权限申请审批功能（模型、服务、控制器、审批回调、前端页面）
- `iam-policy`: iam 企业 Policy 功能（模型、服务、控制器、前端页面）
- `iam-org-user-enhance`: iam 组织/用户服务增强（人员组织选择器接口）

### 修改功能

（无现有功能规范级行为变更）

## 影响

- **后端**：framework 新增 `permission/`、`notification/` 目录；iam 新增 3 个模型文件、3+ 个服务文件、5+ 个控制器文件
- **数据库**：iam schema 新增 `notifications`、`notification_reads`、`permission_requests`、`permission_cache_events`、`policies` 五张表
- **API**：新增 `/iam/admin/v1/notifications`、`/iam/console/v1/notifications`、`/iam/admin/v1/permission-requests`、`/iam/console/v1/permission-requests`、`/iam/admin/v1/policies` 等端点
- **前端**：iam 模块新增站内信、权限申请、Policy 页面及组件
- **依赖**：无新增外部依赖，复用现有 Redis（站内信实时推送可选）和 PostgreSQL
- **兼容性**：无破坏性变更，所有新增为增量
