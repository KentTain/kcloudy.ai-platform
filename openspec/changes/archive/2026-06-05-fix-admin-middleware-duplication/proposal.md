## 为什么

管理员认证中间件存在重复代码和设计失误，导致维护困难、代码混淆和潜在的运行时错误。具体问题包括：

1. **代码重复**：`iam/middlewares/admin_auth_middleware.py` 和 `tenant/middlewares/admin_auth_middleware.py` 完全重复，但只有 tenant 版本被注册使用
2. **错误导入**：部分控制器和测试导入了未使用的 IAM 版本中间件
3. **设计失误**：租户管理员控制器错误假设管理员具有 `tenant_id`，导致所有系统设置错误归类到 "default" 租户

这些问题需要立即修复，以确保代码清晰、维护性良好，并避免未来的混淆。

## 变更内容

### 代码清理
- **删除**：`iam/middlewares/admin_auth_middleware.py`（死代码）
- **修复导入**：将所有对 IAM 版本中间件的导入改为 tenant 版本
- **修正逻辑**：移除 `system_setting_controller.py` 中错误的 `tenant_id` 假设

### 受影响文件
- `server/python/src/iam/middlewares/admin_auth_middleware.py`（删除）
- `server/python/src/iam/controllers/admin/system_setting_controller.py`（修复导入和逻辑）
- `server/python/tests/framework/integration/tenant/test_tenant_admin_api.py`（修复导入）

## 功能 (Capabilities)

### 新增功能
无新增功能。

### 修改功能
- `admin-authentication`: 修正管理员认证中间件的组织结构，统一使用 tenant 模块版本，移除 IAM 模块的重复实现。需求变更：明确中间件的唯一来源为 `tenant.middlewares.admin_auth_middleware`。

## 影响

### 受影响的代码
- **中间件**：统一使用 `tenant.middlewares.admin_auth_middleware`
- **控制器**：`iam/controllers/admin/system_setting_controller.py` 需要修复导入和移除 tenant_id 逻辑
- **测试**：`tests/framework/integration/tenant/test_tenant_admin_api.py` 需要修复导入

### API 端点
- `/admin/v1/system-settings/*` - 移除错误的 tenant_id 逻辑，系统设置应为平台级配置

### 兼容性
- **无破坏性变更**：此次修复仅清理死代码和修正错误逻辑，不影响现有 API 行为
- **向后兼容**：所有现有功能保持不变

### 数据库
- 无数据库变更
