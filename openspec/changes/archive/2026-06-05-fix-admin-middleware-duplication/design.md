## 上下文

### 当前状态
项目中存在两个完全相同的 `AdminAuthMiddleware` 实现：
- `tenant/middlewares/admin_auth_middleware.py` - 实际被 `TenantModule` 注册使用
- `iam/middlewares/admin_auth_middleware.py` - 死代码，从未被注册

此外，部分代码错误地导入了 IAM 版本的中间件，导致代码来源混淆。

### 约束
- 不影响现有 API 行为
- 保持向后兼容
- 遵循项目的模块化架构原则

### 利益相关者
- 平台开发人员（维护代码清晰性）
- 租户管理员（使用 `/admin/v1/*` 端点）

## 目标 / 非目标

**目标：**
- 移除重复代码，明确中间件的唯一来源
- 修复错误的导入路径
- 修正 `system_setting_controller.py` 中的设计失误（错误的 `tenant_id` 假设）
- 确保测试导入正确

**非目标：**
- 不改变 API 行为或响应格式
- 不重构中间件的实现逻辑
- 不修改数据库模型或迁移

## 决策

### 决策 1：删除 IAM 模块的重复中间件

**选择**：删除 `iam/middlewares/admin_auth_middleware.py`

**理由**：
- 该文件从未被注册使用（`IAMModule.get_middlewares()` 返回空列表）
- 与 `tenant/middlewares/admin_auth_middleware.py` 完全重复
- 租户管理员（TenantAdmin）是全局管理员，逻辑上归属于 tenant 模块

**替代方案**：
- 保留 IAM 版本 → 会继续造成混淆，违反 DRY 原则
- 重命名为 `platform_admin` → 超出此次修复范围，应作为单独的重构任务

### 决策 2：统一导入来源

**选择**：所有代码统一从 `tenant.middlewares.admin_auth_middleware` 导入

**理由**：
- 明确单一来源
- 避免未来混淆
- 符合模块所有权原则（管理员认证属于租户管理范畴）

**受影响文件**：
- `iam/controllers/admin/system_setting_controller.py`
- `tests/framework/integration/tenant/test_tenant_admin_api.py`

### 决策 3：移除错误的 tenant_id 逻辑

**选择**：从 `system_setting_controller.py` 中移除 `tenant_id` 相关逻辑

**理由**：
- `TenantAdmin` 是全局管理员，不具有 `tenant_id`
- 当前代码错误地将所有设置归类到 "default" 租户
- 系统设置应为平台级配置，不属于任何特定租户

**替代方案**：
- 保留 tenant_id 逻辑并添加到 Token → 违反设计意图（管理员不应绑定租户）
- 创建独立的租户级设置功能 → 超出此次修复范围

## 风险 / 权衡

### 风险 1：导入变更可能影响未发现的代码
**风险**：可能存在其他文件也导入了 IAM 版本的中间件

**缓解措施**：
- 使用 `codegraph` 和 `rg` 全面搜索所有导入
- 在删除前确认所有导入已修复
- 运行完整测试套件验证

### 风险 2：系统设置逻辑变更可能影响现有数据
**风险**：移除 tenant_id 逻辑后，已有的 "default" 租户设置可能需要迁移

**缓解措施**：
- 当前系统仅为演示项目，无生产数据
- 系统设置功能的 tenant_id 本身就是设计失误，无需迁移
- 如果未来需要租户级设置，应作为新功能单独设计

### 权衡：简洁性 vs. 未来扩展性
- **选择简洁性**：直接删除重复代码和错误逻辑
- **牺牲扩展性**：如果未来需要更复杂的管理员体系（如租户级管理员），需要重新设计
- **判断**：当前架构清晰，未来扩展时重构成本可控
