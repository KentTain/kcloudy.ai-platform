## 1. 数据库模型

- [ ] 1.1 创建 `tenant/models/module_menu_permission.py` 模块菜单-权限关联模型
- [ ] 1.2 在 `tenant/models/__init__.py` 中导出新模型
- [ ] 1.3 创建数据库迁移脚本，新增 `module_menu_permissions` 表

## 2. 事件定义

- [ ] 2.1 在 `tenant/models/enums.py` 中新增菜单权限相关事件类型
- [ ] 2.2 定义 `ModuleMenuPermissionCreated` 事件
- [ ] 2.3 定义 `ModuleMenuPermissionDeleted` 事件
- [ ] 2.4 定义 `ModuleRolePermissionCreated` 事件
- [ ] 2.5 定义 `ModuleRolePermissionDeleted` 事件

## 3. 同步逻辑实现

- [ ] 3.1 在 `iam/services/module_sync_service.py` 中实现 `sync_module_role_permission_created()` 方法
- [ ] 3.2 实现 `sync_module_role_permission_deleted()` 方法
- [ ] 3.3 实现 `sync_module_menu_permission_created()` 方法
- [ ] 3.4 实现 `sync_module_menu_permission_deleted()` 方法
- [ ] 3.5 在模块分配流程中集成角色权限同步
- [ ] 3.6 在模块分配流程中集成菜单权限同步

## 4. 租户角色自动创建

- [ ] 4.1 在 `tenant/services/tenant_service.py` 中创建 `_create_tenant_roles()` 私有方法
- [ ] 4.2 修改 `TenantService.create()` 方法，调用 `_create_tenant_roles()`
- [ ] 4.3 实现租户角色权限模板分配逻辑
- [ ] 4.4 创建者自动分配 owner 角色逻辑

## 5. 权限缓存失效

- [ ] 5.1 扩展 `iam/services/permission_service.py` 中的缓存失效触发点
- [ ] 5.2 在 RolePermission 变更时触发缓存失效
- [ ] 5.3 在角色权限同步完成后触发租户级缓存失效

## 6. API 端点

- [ ] 6.1 在 `tenant/controllers/admin/module_controller.py` 中新增菜单权限查询端点
- [ ] 6.2 新增菜单权限更新端点
- [ ] 6.3 创建请求/响应 Schema

## 7. 单元测试

- [ ] 7.1 编写 `ModuleMenuPermission` 模型测试
- [ ] 7.2 编写角色权限同步测试
- [ ] 7.3 编写菜单权限同步测试
- [ ] 7.4 编写租户角色自动创建测试
- [ ] 7.5 编写权限缓存失效测试

## 8. 集成测试

- [ ] 8.1 编写模块分配完整同步流程测试
- [ ] 8.2 编写租户创建完整流程测试
- [ ] 8.3 验证现有功能回归测试通过

## 9. 文档更新

- [ ] 9.1 更新 IAM 模块 CLAUDE.md，说明新的角色编码规范
- [ ] 9.2 更新模块同步流程文档
