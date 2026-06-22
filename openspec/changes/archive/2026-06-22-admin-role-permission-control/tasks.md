## 1. 数据库变更

- [ ] 1.1 `tenant_admins` 表新增 `role` 字段（VARCHAR(50), NOT NULL, DEFAULT 'ordinaryAdmin'）
- [ ] 1.2 创建 Alembic 迁移脚本

## 2. 后端模型变更

- [ ] 2.1 `tenant/models/tenant_admin.py` 的 TenantAdmin 类新增 `role` 映射字段

## 3. 后端模块定义更新

- [ ] 3.1 `tenant/module.py` 的 `get_module_definition()` 补充二级隐藏菜单（modules.create/detail/edit、tenants.create/detail/edit）
- [ ] 3.2 `tenant/module.py` 的 `get_module_definition()` 补充 `default_roles` 定义（tenantAdmin、ordinaryAdmin）
- [ ] 3.3 `iam/module.py` 的 `get_module_definition()` 补充二级隐藏菜单（organizations.create/detail/edit、roles.create/detail/edit、users.create/detail/edit、menus.detail、permissions.detail）
- [ ] 3.4 `ai/module.py` 的 `get_module_definition()` 补充二级隐藏菜单（plugins.create/detail/edit）

## 4. 后端认证服务层

- [ ] 4.1 `AdminAuthService.login()` 扩展：返回到角色编码和权限码列表
- [ ] 4.2 新增 `AdminAuthService.get_admin_info()` 聚合方法：根据 admin.role 查询 module_roles → module_role_permissions → module_permissions 获取权限列表，查询 module_menus 获取过滤后的菜单树
- [ ] 4.3 `admin_seed.py` 更新：设置默认管理员的 `role` 为 "tenantAdmin"

## 5. 后端控制器层

- [ ] 5.1 `/tenant/admin/v1/auth/login` 登录接口扩展返回 `role` 和 `permissions`
- [ ] 5.2 新增 `/tenant/admin/v1/admin/me` 接口：返回当前管理员完整信息（角色、权限、菜单）
- [ ] 5.3 `/tenant/admin/v1/admin/menus` 菜单接口增加基于 admin 角色的权限过滤

## 6. 后端中间件

- [ ] 6.1 `AdminAuthMiddleware` 新增加 Check 模块 API 级权限校验：根据请求方法和方法对应的权限判断是否允许

## 7. 前端类型定义

- [ ] 7.1 `tenant/types/admin.ts` 扩展 `AdminInfo` / `AdminLoginResponse` 类型，新增 `role` 和 `permissions` 字段

## 8. 前端状态管理

- [ ] 8.1 `tenant/stores/adminAuth.ts` 扩展：存储 `role`、`permissions`、`menus`
- [ ] 8.2 `tenant/stores/adminAuth.ts` 新增 `hasPermission(code)` 和 `hasRole(code)` 方法
- [ ] 8.3 登录流程调整：登录成功后调用 `/admin/me` 获取完整权限和菜单数据

## 9. 前端路由配置

- [ ] 9.1 `tenant/router/index.ts` 各 admin 路由补充 `meta.permissions` 声明（列表页:read、创建页:write、详情页:read、编辑页:write）

## 10. 前端路由守卫

- [ ] 10.1 `framework/router/guards.ts` admin 路由分支增加 `meta.permissions` 检查，无权限跳转 `/403`

## 11. 测试

- [ ] 11.1 后端单元测试：`AdminAuthService.login()` 角色/权限返回验证
- [ ] 11.2 后端单元测试：`get_admin_menus` 权限过滤验证
- [ ] 11.3 前端单元测试：`adminAuth.hasPermission()` 逻辑验证
- [ ] 11.4 前端单元测试：路由守卫 admin 权限分支验证
