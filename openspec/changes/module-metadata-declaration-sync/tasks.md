## 1. 后端基础设施

- [ ] 1.1 创建 `framework/module/definition.py`，定义 `MenuDef`、`PermissionDef`、`RoleDef`、`ModuleDefinition` 数据类
- [ ] 1.2 扩展 `framework/module/descriptor.py`，新增 `get_module_definition()` 方法签名
- [ ] 1.3 创建 `framework/module/sync_service.py`，实现模块定义同步服务

## 2. 后端同步服务

- [ ] 2.1 实现 `_sync_module()` 方法，同步模块基本信息
- [ ] 2.2 实现 `_sync_menus()` 方法，同步菜单并处理父子关系
- [ ] 2.3 实现 `_sync_permissions()` 方法，同步权限
- [ ] 2.4 实现 `_sync_roles()` 方法，同步角色及权限关联
- [ ] 2.5 实现 `_cleanup_orphans()` 方法，清理孤立记录
- [ ] 2.6 实现循环引用检测和错误处理

## 3. 后端启动集成

- [ ] 3.1 修改 `application_web.py` lifespan，在启动时调用同步服务
- [ ] 3.2 添加同步日志，记录同步结果和错误

## 4. 业务模块实现

- [ ] 4.1 IAM 模块实现 `get_module_definition()`，声明菜单、权限、默认角色
- [ ] 4.2 Tenant 模块实现 `get_module_definition()`，声明菜单、权限、默认角色
- [ ] 4.3 AI 模块实现 `get_module_definition()`，声明菜单、权限、默认角色

## 5. 用户菜单 API

- [ ] 5.1 创建 `iam/schemas/user_menu.py`，定义 `UserMenuVo` 响应模型
- [ ] 5.2 创建 `iam/services/user_menu_service.py`，实现菜单查询和权限过滤逻辑
- [ ] 5.3 创建 `iam/controllers/user_menu_controller.py`，实现 `GET /api/v1/user/menus` 端点
- [ ] 5.4 在 IAM 模块路由中注册用户菜单控制器

## 6. 前端基础设施

- [ ] 6.1 创建 `web/vue/src/framework/api/menu.ts`，实现用户菜单 API 客户端
- [ ] 6.2 扩展 `web/vue/src/framework/module/types.ts`，对齐 ModuleDescriptor 接口

## 7. 前端菜单 Store

- [ ] 7.1 修改 `web/vue/src/framework/stores/menu.ts`，新增 `menus` 状态
- [ ] 7.2 实现 `fetchMenus()` 方法，从 API 获取菜单
- [ ] 7.3 实现菜单树构建逻辑

## 8. 前端组件改造

- [ ] 8.1 修改 `web/vue/src/framework/layouts/components/AppNavMain.vue`，从 store 获取菜单
- [ ] 8.2 实现图标动态渲染，根据 icon 名称映射组件
- [ ] 8.3 删除硬编码的 `defaultItems` 常量

## 9. 登录集成

- [ ] 9.1 修改登录成功后逻辑，调用 `fetchMenus()` 获取用户菜单
- [ ] 9.2 处理菜单加载失败的降级逻辑

## 10. 测试

- [ ] 10.1 后端单元测试：同步服务测试
- [ ] 10.2 后端单元测试：用户菜单 API 测试
- [ ] 10.3 后端集成测试：模块定义同步端到端测试
- [ ] 10.4 前端单元测试：菜单 store 测试
- [ ] 10.5 前端组件测试：AppNavMain 渲染测试

## 11. 文档与清理

- [ ] 11.1 更新模块开发文档，说明如何实现 `get_module_definition()`
- [ ] 11.2 删除或注释不再需要的 seed 脚本中的菜单/权限初始化代码
