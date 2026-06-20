## 1. 迁移重建准备

- [x] 1.1 删除所有模块的 migrations/versions/*.py 文件（tenant、iam、demo、ai）
- [x] 1.2 删除数据库中所有 schema（DROP SCHEMA IF EXISTS tenant, iam, demo, ai CASCADE）
- [x] 1.3 创建新的单一迁移文件 001_initial_schema.py

## 2. 后端模型重构（Department → Organization）

- [x] 2.1 重命名 iam/models/department.py → iam/models/organization.py
- [x] 2.2 更新 Organization 模型类定义（类名、表名、字段注释）
- [x] 2.3 创建 UserOrganization 模型（替代 UserDepartment）
- [x] 2.4 更新 iam/models/__init__.py 导入和导出
- [x] 2.5 重命名 iam/schemas/department.py → iam/schemas/organization.py
- [x] 2.6 更新所有 Schema 类名（DepartmentXxx → OrganizationXxx）
- [x] 2.7 重命名 iam/services/department_service.py → iam/services/organization_service.py
- [x] 2.8 更新 OrganizationService 类定义和方法
- [x] 2.9 重命名 iam/controllers/admin/department_controller.py → organization_controller.py
- [x] 2.10 更新控制器路由前缀（/departments → /organizations）
- [x] 2.11 重命名 iam/controllers/inner/department_controller.py → organization_controller.py
- [x] 2.12 更新内部接口路由前缀
- [x] 2.13 更新所有导入 Department 的文件（全局替换）
- [x] 2.14 删除废弃的 department 相关文件

## 3. 全局角色实现

- [x] 3.1 创建 tenant/migrations/seeds/global_role_seed.py
- [x] 3.2 定义全局角色 sysAdmin（权限：*:*:*）
- [x] 3.3 定义全局角色 normalUser（权限：*:*:read）
- [x] 3.4 更新 tenant/module.py 移除 default_roles
- [x] 3.5 更新 iam/module.py 移除 default_roles，更新菜单定义
- [x] 3.6 更新 demo/module.py 移除 default_roles
- [x] 3.7 更新 ai/module.py 移除 default_roles
- [x] 3.8 更新 ModuleDefinitionSyncService 支持全局角色同步
- [x] 3.9 更新 ModuleSyncService.sync_module_assigned 支持全局角色
- [x] 3.10 确保角色通过 code 匹配而不是 id

## 4. 初始化数据重构

- [x] 4.1 更新 tenant/migrations/seeds/resource_config_seed.py（保持不变）
- [x] 4.2 更新 tenant/migrations/seeds/tenant_seed.py（自动分配模块、关联资源）
- [x] 4.3 更新 tenant/migrations/seeds/admin_seed.py（创建默认管理员）
- [x] 4.4 创建 iam/migrations/seeds/organization_seed.py（默认组织）
- [x] 4.5 更新 iam/migrations/seeds/user_seed.py（用户-组织关联、角色分配）
- [x] 4.6 更新模块 seed 执行顺序和依赖关系

## 5. 迁移文件创建

- [x] 5.1 创建 tenant 模块迁移（包含全局角色、资源配置、模块定义）
- [x] 5.2 创建 iam 模块迁移（包含组织、RBAC、用户表）
- [x] 5.3 创建 demo 模块迁移
- [x] 5.4 创建 ai 模块迁移
- [x] 5.5 验证迁移文件正确性（表结构、索引、约束）

## 6. 前端重构（Department → Organization）

- [x] 6.1 重命名 iam/api/department.ts → iam/api/organization.ts
- [x] 6.2 更新所有 API 函数名和路径
- [x] 6.3 重命名 iam/stores/department.ts → iam/stores/organization.ts
- [x] 6.4 更新 Store 定义和使用
- [x] 6.5 更新 iam/types/index.ts 中的 Department 类型为 Organization
- [x] 6.6 重命名 iam/pages/departments/ → iam/pages/organizations/
- [x] 6.7 重命名 DepartmentPage.vue → OrganizationPage.vue
- [x] 6.8 更新页面组件内容和引用
- [x] 6.9 重命名 iam/components/DepartmentTree.vue → OrganizationTree.vue
- [x] 6.10 重命名 iam/components/CreateDepartmentDialog.vue → CreateOrganizationDialog.vue
- [x] 6.11 更新 iam/router/index.ts 路由配置（/departments → /organizations）
- [x] 6.12 更新所有导入 Department 的文件（全局替换）

## 7. 验证和测试

- [x] 7.1 运行数据库迁移（uv run python manage.py db migrate --all）
- [x] 7.2 运行初始化数据（uv run python manage.py seed）
- [x] 7.3 验证全局角色创建正确（sysAdmin、normalUser）
- [x] 7.4 验证默认组织创建正确
- [x] 7.5 验证默认用户创建正确（admin/admin123）
- [x] 7.6 验证用户-组织-角色关联正确
- [x] 7.7 运行后端单元测试（uv run pytest tests/iam/unit/ -v）
- [x] 7.8 运行后端集成测试（uv run pytest tests/iam/integration/ -v）
- [x] 7.9 启动前端开发服务器验证页面正常（pnpm dev）
- [x] 7.10 验证前端路由正常工作（/iam/organizations）
- [x] 7.11 验证 API 请求正常（GET /iam/admin/v1/organizations）

## 8. 文档更新

- [x] 8.1 更新 CLAUDE.md 中相关描述（如果有）
- [x] 8.2 更新 API 文档（如果有）
- [x] 8.3 更新数据库设计文档（如果有）
