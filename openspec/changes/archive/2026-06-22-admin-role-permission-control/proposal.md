## 为什么

租户管理后台当前只有粗粒度的 `requiresAdminAuth` 认证检查，所有管理员登录后拥有完全相同的权限。租户管理、模块管理、资源配置等一级菜单下的详情页、编辑页、创建页等二级页面无法进行差异化权限控制。需要引入基于角色的访问控制（RBAC），允许租户管理员（读写）和普通管理员（只读）拥有不同的操作权限。

## 变更内容

- **tenant_admins 表新增 `role` 字段**：存储管理员的角色编码（如 `tenantAdmin`、`ordinaryAdmin`）
- **模块定义中新增 `default_roles`**：在 tenant 模块的 `get_module_definition()` 中声明 `tenantAdmin`（读写）和 `ordinaryAdmin`（只读）两个角色及其权限
- **模块定义中补充二级菜单**：为 tenant、iam、ai 模块的一级菜单补充二级隐藏菜单（创建/详情/编辑），通过 `is_visible=false` 隐藏但参与权限控制
- **登录响应扩展**：`admin_login` 接口返回管理员的角色和权限列表
- **新增 `/admin/me` 接口**：返回当前管理员的完整信息（角色、权限、已过滤菜单树）
- **菜单接口加权限过滤**：`get_admin_menus` 根据管理员角色的权限过滤返回的菜单树
- **前端 adminAuth Store 扩展**：存储角色和权限数据，新增 `hasPermission()` / `hasRole()` 方法
- **前端路由守卫扩展**：admin 路由分支检查 `meta.permissions`
- **前端路由 meta 补充**：各 admin 路由添加 `permissions` 声明
- **API 中间件扩展**：`AdminAuthMiddleware` 在 API 层拦截无权限的操作请求

## 功能 (Capabilities)

### 新增功能
- `admin-role-permission`: 租户管理员 RBAC 控制——管理员角色定义、权限与菜单关联、前端基于权限的访问控制

### 修改功能
<!-- 无现有规范变更 -->

## 影响

| 层面 | 影响范围 |
|------|---------|
| 数据库 | `tenant_admins` 表新增 `role` 字段；新增迁移脚本 |
| 后端模型 | `tenant/models/tenant_admin.py` 新增 `role` 列 |
| 后端服务 | `AdminAuthService.login()` 返回角色/权限；新增 `get_admin_info()` 聚合方法 |
| 后端控制器 | `get_admin_menus` 加权限过滤；新增 `/admin/me` 端点 |
| 后端中间件 | `AdminAuthMiddleware` 新增 API 级权限校验 |
| 后端模块定义 | `tenant/module.py`、`iam/module.py`、`ai/module.py` 补充二级菜单和默认角色 |
| 后端种子数据 | `admin_seed.py` 设置默认管理员角色 |
| 前端 Store | `adminAuth.ts` 扩展角色/权限/菜单存储 |
| 前端路由 | `tenant/router/index.ts` 各路由添加 `meta.permissions` |
| 前端路由守卫 | `framework/router/guards.ts` admin 分支加权限检查 |
| 前端类型 | `tenant/types/admin.ts` 扩展 `AdminInfo` 类型 |
