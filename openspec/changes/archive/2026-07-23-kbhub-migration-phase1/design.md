## 上下文

本项目（AI Platform）是模块化单体架构，已有 framework、tenant、iam、document、ai、demo 模块。iam 已具备基础 RBAC 和审计日志（AuditLog + AuditLogService + 控制器）。kbhub（Alon 项目企业知识库）迁移方案（`docs/requirements/12.Alon知识库迁移方案.md`）定义了三层权限架构。Phase 1 是该方案的第一阶段：搭建基础设施 + iam 扩展 + 文档准备，为 Phase 2（document）和 Phase 3（ai）提供前置依赖。

当前状态：
- framework 无权限判定引擎、无审计写入辅助、无站内信发送辅助
- iam 无站内信、权限申请、企业 Policy 模型
- document 模块仅有空骨架，ai 模块有 LLM/插件基础但无知识库
- 各模块 CLAUDE.md 需要更新以反映迁移后架构

## 目标 / 非目标

**目标：**
- 在 framework 层提供权限判定引擎接口、Policy 求值器、审计写入辅助、站内信发送辅助
- 在 iam 层实现站内信、权限申请、企业 Policy 的模型、服务、控制器
- 增强 iam 组织/用户服务，提供人员组织选择器所需接口
- 更新各模块 CLAUDE.md 文档
- 审计日志复用现有 iam.audit_logs，各业务模块通过 framework 审计写入辅助记录

**非目标：**
- 不实现 document 模块业务功能（Phase 2 范围）
- 不实现 ai 模块知识库/工具库功能（Phase 3 范围）
- 不改动现有 iam RBAC、User、Organization、AuditLog 模型定义
- 不实现前端完整 UI（仅实现 iam 新增功能的页面）
- 不迁移 kbhub 的 Alon 平台特有依赖

## 决策

### 决策 1：审计日志复用现有 iam.audit_logs，不新建表

**选择**：复用现有 `iam.models.audit_log.AuditLog`（字段含 business_domain/operation_type/resource_type/before_data/after_data/detail），各业务模块通过 framework 审计写入辅助记录。

**理由**：现有字段已满足 kbhub 审计需求，避免重复造表和数据分散。

**替代方案**：各业务模块自建 audit_log 表 → 查询分散、数据不一致，否决。

### 决策 2：framework 提供审计写入辅助而非直接操作 iam schema

**选择**：framework `permission/audit_writer.py` 封装写入逻辑，业务模块调用辅助函数，不直接依赖 iam schema。

**理由**：framework 禁止依赖业务模块（依赖边界：framework ─X──▶ iam）。辅助通过 inner 接口或延迟导入写入 iam.audit_logs，保持依赖方向正确。

**替代方案**：业务模块直接导入 iam.models.AuditLog → 违反依赖边界，否决。

### 决策 3：权限申请审批通过 inner 接口回调各业务模块

**选择**：iam 维护 PermissionRequest 申请与审批状态，审批通过后通过 `/document/inner/v1/permission-requests/{id}/apply` 和 `/ai/inner/v1/permission-requests/{id}/apply` 回调各模块落地授权。

**理由**：权限申请是全局入口，落地动作属业务模块职责（创建 library_members/knowledge_base_members），通过 inner 接口解耦。

**替代方案**：iam 直接操作各模块表 → 违反模块边界，否决。

### 决策 4：企业 Policy 放 iam 模块

**选择**：iam.policies 维护租户级 Policy，`effect=deny` 优先于所有允许，通过 framework Policy 求值器跨 document/ai 生效。

**理由**：Policy 是租户级安全策略，跨业务模块，属权限治理范畴，与 iam 定位一致。

**替代方案**：放 framework → framework 不含业务数据模型，否决；放各模块 → 策略分散难统一，否决。

### 决策 5：站内信通过 framework 发送辅助 + iam 模型存储

**选择**：iam.notifications 存储站内信，framework `notification/sender.py` 提供发送辅助供各模块调用。

**理由**：站内信是跨模块通知能力，模型属 iam，发送能力放 framework 供复用。

## 风险 / 权衡

- **[审计写入性能]** 大量业务操作写入 iam.audit_logs 可能成瓶颈 → 异步写入、批量优化；当前阶段实时写入足够
- **[权限申请回调原子性]** 审批通过后回调各模块落地授权需事务一致 → 审批与回调分离，回调失败通过补偿重试，权限申请标记为 processing/applied/failed
- **[Policy 求值性能]** 每次权限判定求值 Policy 可能慢 → Policy 缓存 + 失效机制；当前阶段实时求值足够
- **[framework 延迟导入]** 审计写入辅助需延迟导入 iam 模型避免循环依赖 → 使用函数内导入

## 迁移计划

1. 先创建 framework 权限引擎/审计写入/站内信辅助（无数据库变更）
2. 再创建 iam 新增模型 + 迁移脚本（新增 5 张表）
3. 实现 iam 新增服务和控制器
4. 增强 iam 组织/用户服务
5. 更新各模块 CLAUDE.md 文档
6. 单元测试和接口测试验证

**回滚**：Phase 1 全部为增量，回滚只需删除新增表和代码，不影响现有功能。

## 待解决问题

- 站内信是否需要实时推送（Redis PubSub）还是仅存储查询？当前阶段建议仅存储查询，实时推送作为后续增强
- Policy 的条件表达式 DSL 形式需在实现时确定（建议初版用 JSON 结构化条件）
