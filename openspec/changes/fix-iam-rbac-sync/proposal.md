## 为什么

当前 IAM RBAC 架构存在三个关键问题：

1. **UserTenant.role 与 RBAC 不一致**：`UserTenant.role` 是独立的字符串字段（owner/admin/member），与正式的 RBAC `Role` 模型完全隔离，导致用户有两套角色体系，权限检查只查 `UserRole`，租户身份不参与权限判定。

2. **MenuPermission 缺少数据来源**：模块定义层缺少 `ModuleMenuPermission` 模型，导致租户实例层的 `MenuPermission` 表没有数据来源，菜单权限控制功能实际上不完整。

3. **ModuleRolePermission 同步缺失**：`ModuleRolePermission` → `RolePermission` 的同步逻辑未实现，导致角色-权限关联无法从模块定义层同步到租户实例层。

这些问题导致菜单可见性控制失效、租户管理员权限需要两处维护、角色权限变更无法自动同步。

## 变更内容

### 新增功能

1. **ModuleMenuPermission 模型**
   - 新增 `tenant/models/module_menu_permission.py` 模块菜单-权限关联模型
   - 实现模块定义层的菜单权限关联定义

2. **同步逻辑完善**
   - 实现 `sync_module_role_permission_created()` - 角色-权限关联同步
   - 实现 `sync_module_menu_permission_created()` - 菜单-权限关联同步
   - 实现更新、删除事件的同步处理

3. **租户角色 RBAC 化**
   - 创建租户时自动创建 owner/admin/member 三个租户级角色
   - 新用户加入租户时通过 UserRole 分配角色
   - 废弃 `UserTenant.role` 字段（保留向后兼容）

### 修改功能

- **BREAKING** `UserTenant.role` 字段废弃，改用 `UserRole` 管理
- `TenantService.create()` 新增租户角色自动创建逻辑
- `TenantService.assign_module()` 新增角色-权限关联同步

### 移除功能

- 无（保留 `UserTenant.role` 字段用于向后兼容和过渡期）

## 功能 (Capabilities)

### 新增功能

- `module-menu-permission`: 模块菜单-权限关联定义功能
- `tenant-role-auto-creation`: 租户角色自动创建功能，创建租户时自动创建 owner/admin/member 角色
- `rbac-sync-enhancement`: RBAC 同步增强，包括角色-权限、菜单-权限的完整同步

### 修改功能

- `tenant-management`: 租户管理功能需求变更，创建租户时自动创建 RBAC 角色
- `module-sync`: 模块同步功能需求变更，新增角色-权限、菜单-权限同步逻辑

## 影响

### 后端影响

**模型层**：
- `tenant/models/module_menu_permission.py` - 新增模块
- `tenant/models/__init__.py` - 导出新模型

**服务层**：
- `iam/services/module_sync_service.py` - 新增同步方法
- `tenant/services/tenant_service.py` - 修改 `create()` 方法，自动创建角色
- `iam/services/permission_service.py` - 扩展缓存失效触发点

**数据库迁移**：
- 新增 `module_menu_permissions` 表
- 新增租户角色种子数据逻辑

**API 影响**：
- `POST /tenant/admin/v1/tenants` - 行为变更，自动创建角色
- `POST /tenant/admin/v1/tenants/{id}/modules` - 行为变更，同步角色权限

### 兼容性

**向后兼容**：
- `UserTenant.role` 字段保留，现有数据不受影响
- 现有 API 签名不变
- 新旧角色体系可并存过渡

**迁移策略**：
1. 新增 `module_menu_permissions` 表
2. 实现 RBAC 同步逻辑
3. 新租户使用 RBAC 角色体系
4. 现有租户可手动迁移或保持原状
