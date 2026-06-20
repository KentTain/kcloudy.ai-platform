## 为什么

当前数据库迁移历史混乱，包含多个增量迁移文件，且 Department 模型命名与业务语义不符。RBAC 角色定义分散在各模块中，缺乏统一的全局角色管理，导致用户需要为每个模块单独分配角色。需要一次性重构数据库初始化流程，建立清晰的数据模型和权限体系。

## 变更内容

1. **删除所有迁移文件**，创建单一初始化迁移
2. **Department 彻底重构为 Organization**（**BREAKING**）
   - 模型、表名、API 路径、前端页面全部重命名
   - `departments` → `organizations`，`user_departments` → `user_organizations`
3. **共享全局角色**（**BREAKING**）
   - 移除各模块独立的角色定义
   - 新增全局角色：`sysAdmin`（所有权限）、`normalUser`（只读权限）
   - 角色通过 `code` 识别，不再依赖模块级 `id`
4. **重构初始化数据流程**
   - tenant 模块：资源配置、模块注册、全局角色、菜单/权限（按 sort_order 排序）、默认租户、默认管理员
   - iam 模块：默认组织、RBAC 同步、默认用户、用户-组织-角色关联

## 功能 (Capabilities)

### 新增功能

- `global-roles`: 全局共享角色（sysAdmin、normalUser），权限编码使用通配符（`*:*:*`、`*:*:read`）
- `organization-management`: 组织管理功能，替代原部门管理，支持树形结构和负责人设置

### 修改功能

- `tenant-initialization`: 租户模块初始化流程重构，新增全局角色和菜单排序
- `iam-initialization`: IAM 模块初始化流程重构，新增默认组织和用户-组织关联
- `rbac-sync`: RBAC 同步逻辑更新，支持全局角色同步

## 影响

### 后端影响

**模型重命名/删除**：
- `iam/models/department.py` → `iam/models/organization.py`
- `iam/schemas/department.py` → `iam/schemas/organization.py`
- `iam/services/department_service.py` → `iam/services/organization_service.py`
- `iam/controllers/admin/department_controller.py` → `organization_controller.py`
- `iam/controllers/inner/department_controller.py` → `organization_controller.py`

**模块定义变更**：
- `iam/module.py`: 移除 `default_roles`，更新菜单定义
- `tenant/module.py`: 移除 `default_roles`，更新菜单排序
- `demo/module.py`: 移除 `default_roles`
- `ai/module.py`: 移除 `default_roles`

**迁移文件**：
- 删除所有模块的 `migrations/versions/*.py`
- 创建新的单一迁移文件

**初始化 Seed**：
- `tenant/migrations/seeds/resource_config_seed.py`: 保持
- `tenant/migrations/seeds/tenant_seed.py`: 更新逻辑
- `tenant/migrations/seeds/global_role_seed.py`: 新增
- `iam/migrations/seeds/user_seed.py`: 更新组织关联逻辑
- `iam/migrations/seeds/organization_seed.py`: 新增

### 前端影响

**文件重命名**：
- `iam/api/department.ts` → `iam/api/organization.ts`
- `iam/stores/department.ts` → `iam/stores/organization.ts`
- `iam/pages/departments/` → `iam/pages/organizations/`
- `iam/components/DepartmentTree.vue` → `OrganizationTree.vue`
- `iam/components/CreateDepartmentDialog.vue` → `CreateOrganizationDialog.vue`

**类型定义**：
- `iam/types/index.ts`: `Department` → `Organization`

**路由**：
- `/iam/departments` → `/iam/organizations`

### API 变更（**BREAKING**）

| 原路径 | 新路径 |
|--------|--------|
| `/iam/admin/v1/departments` | `/iam/admin/v1/organizations` |
| `/iam/inner/v1/departments` | `/iam/inner/v1/organizations` |

### 数据库变更（**BREAKING**）

| 原表名 | 新表名 |
|--------|--------|
| `iam.departments` | `iam.organizations` |
| `iam.user_departments` | `iam.user_organizations` |

### 兼容性

- **不兼容变更**：API 路径、数据库表名、前端路由全部变更
- **迁移策略**：删除所有表重建，不保留历史数据
