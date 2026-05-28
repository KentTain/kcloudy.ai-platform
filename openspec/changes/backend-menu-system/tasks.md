## 1. 数据模型

- [ ] 1.1 创建 `iam/models/menu.py`，定义 Menu 模型（继承 BaseModel + TreeNodeMixin）
- [ ] 1.2 创建 `iam/models/menu_permission.py`，定义 MenuPermission 关联表
- [ ] 1.3 在 Menu 模型中添加与 Permission 的多对多关系

## 2. Schema 定义

- [ ] 2.1 创建 `iam/schemas/menu.py`，定义 MenuCreate、MenuUpdate、MenuResponse Schema
- [ ] 2.2 创建 `iam/schemas/menu.py`，定义 MenuTreeResponse Schema（嵌套 children 字段）
- [ ] 2.3 创建 `iam/schemas/menu.py`，定义 MenuQueryParams 查询参数 Schema

## 3. 服务层

- [ ] 3.1 创建 `iam/services/menu_service.py`，实现 MenuService 单例
- [ ] 3.2 实现 `get_menu_tree()` 方法，返回完整菜单树
- [ ] 3.3 实现 `get_user_menu_tree(user_id)` 方法，按用户权限过滤菜单
- [ ] 3.4 实现 CRUD 方法：create、update、delete（软删除）
- [ ] 3.5 实现 `validate_menu_level()` 方法，校验菜单层级不超过 3 级

## 4. 控制器层

- [ ] 4.1 创建 `iam/controllers/menu_controller.py`，定义菜单路由蓝图
- [ ] 4.2 实现 GET `/admin/v1/menus` 端点（获取菜单列表）
- [ ] 4.3 实现 GET `/admin/v1/menus/tree` 端点（获取菜单树）
- [ ] 4.4 实现 GET `/admin/v1/menus/user` 端点（获取用户菜单树）
- [ ] 4.5 实现 POST `/admin/v1/menus` 端点（创建菜单）
- [ ] 4.6 实现 PUT `/admin/v1/menus/{id}` 端点（更新菜单）
- [ ] 4.7 实现 DELETE `/admin/v1/menus/{id}` 端点（删除菜单）
- [ ] 4.8 在 IAM 模块入口注册菜单路由蓝图

## 5. 数据库迁移

- [ ] 5.1 创建 Alembic 迁移脚本 `add_menu_tables.py`
- [ ] 5.2 实现 upgrade：创建 `iam_menu` 表
- [ ] 5.3 实现 upgrade：创建 `iam_menu_permission` 关联表
- [ ] 5.4 实现 upgrade：添加索引（parent_id、path）
- [ ] 5.5 实现 downgrade：删除 `iam_menu` 和 `iam_menu_permission` 表

## 6. 种子数据

- [ ] 6.1 在迁移脚本中添加菜单种子数据（demo、iam、tenant 根菜单）
- [ ] 6.2 为根菜单添加子菜单种子数据
- [ ] 6.3 为菜单关联默认权限种子数据

## 7. 测试

- [ ] 7.1 创建 `tests/iam/unit/test_menu_service.py`，测试 MenuService 业务逻辑
- [ ] 7.2 测试菜单树构建逻辑
- [ ] 7.3 测试用户权限过滤逻辑
- [ ] 7.4 测试菜单层级校验
- [ ] 7.5 创建 `tests/iam/integration/test_menu_api.py`，测试菜单 API 端点
- [ ] 7.6 测试未认证访问返回 401
- [ ] 7.7 测试删除有子菜单的菜单返回 400

## 8. 文档与验证

- [ ] 8.1 更新 API 文档（OpenAPI/Swagger）
- [ ] 8.2 运行数据库迁移验证
- [ ] 8.3 手动测试菜单 API 端点
