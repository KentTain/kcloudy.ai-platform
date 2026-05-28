## 上下文

### 背景

当前前端框架直接导入业务模块路由，违反依赖倒置原则。为了实现前端模块化架构，需要后端提供动态菜单 API。菜单系统需要支持：

1. 树形结构：菜单支持多级嵌套
2. 权限关联：菜单与权限多对多关联，实现按权限过滤
3. 动态加载：前端根据用户权限动态加载菜单

### 当前状态

- 已有 `TreeNodeMixin`（`framework/database/mixins/tree.py`）提供树形结构支持
- 已有 `Permission`、`Role` 模型可用于关联
- 缺少菜单模型和菜单-权限关联

### 约束

- 遵循三层架构：Controller → Service → Model
- 使用 SQLAlchemy ORM，Mapped[...] 声明式字段
- API 端点遵循 `/admin/v1/` 前缀规范
- 数据库迁移使用 Alembic

## 目标 / 非目标

**目标：**

- 创建菜单模型，支持树形结构和权限关联
- 提供菜单 CRUD API，支持按权限过滤
- 提供菜单树查询 API，返回用户可访问的菜单树
- 创建数据库迁移和种子数据

**非目标：**

- 前端菜单 Store 实现（属于前端模块系统变更）
- 菜单排序算法优化（当前使用简单的 order 字段）
- 菜单国际化（后续迭代）

## 决策

### 决策 1：菜单模型设计

**选择：** 继承 `BaseModel` 和 `TreeNodeMixin`

**理由：**
- 复用现有的树形结构支持（parent_id、path、level 字段）
- 保持与现有模型一致的基类继承
- 减少重复代码

**字段设计：**

``python
class Menu(BaseModel, TreeNodeMixin):
    name: Mapped[str] = mapped_column(String(100))        # 菜单名称
    path: Mapped[str] = mapped_column(String(255))        # 路由路径
    icon: Mapped[str | None] = mapped_column(String(100)) # 图标名称
    component: Mapped[str | None] = mapped_column(String(255))  # 组件路径
    is_visible: Mapped[bool] = mapped_column(default=True)      # 是否显示
    order: Mapped[int] = mapped_column(default=0)               # 排序
    permissions: Mapped[list[Permission]] = relationship()      # 关联权限
``

**备选方案：** 不使用 `TreeNodeMixin`，自己实现树形结构
- **放弃理由：** 重复造轮子，且 `TreeNodeMixin` 已经过验证

### 决策 2：菜单-权限关联设计

**选择：** 使用中间表 `iam_menu_permission`

**理由：**
- 菜单和权限是多对多关系
- 中间表可以扩展（如添加条件字段）
- 遵循现有的关联表设计模式

**表结构：**

``sql
CREATE TABLE iam_menu_permission (
    menu_id UUID NOT NULL REFERENCES iam_menu(id),
    permission_id UUID NOT NULL REFERENCES iam_permission(id),
    PRIMARY KEY (menu_id, permission_id)
);
``

### 决策 3：API 端点设计

**选择：** RESTful 风格，使用 `/admin/v1/menus` 前缀

**端点列表：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/v1/menus` | 获取菜单列表（扁平） |
| GET | `/admin/v1/menus/tree` | 获取菜单树 |
| GET | `/admin/v1/menus/user` | 获取当前用户的菜单树 |
| POST | `/admin/v1/menus` | 创建菜单 |
| PUT | `/admin/v1/menus/{id}` | 更新菜单 |
| DELETE | `/admin/v1/menus/{id}` | 删除菜单 |

**认证：** 所有端点需要 JWT 认证，`/user` 端点需要验证用户权限

### 决策 4：菜单服务设计

**选择：** 单例模式，封装菜单业务逻辑

**核心方法：**

- `get_menu_tree()` - 获取完整菜单树
- `get_user_menu_tree(user_id)` - 获取用户可访问的菜单树
- `filter_by_permissions(menu_ids, permission_ids)` - 按权限过滤菜单

## 风险 / 权衡

### 风险 1：菜单层级过深导致性能问题

**缓解措施：**
- `TreeNodeMixin` 使用 path 字段优化树查询
- 限制菜单最大层级为 3 级（在服务层校验）

### 风险 2：菜单-权限关联变更后的缓存一致性

**缓解措施：**
- 当前不引入缓存，直接查询数据库
- 后续可添加 Redis 缓存，使用事件通知机制更新

### 风险 3：删除菜单时的级联影响

**缓解措施：**
- 删除前检查是否有子菜单
- 删除前检查是否关联权限
- 使用软删除（`BaseModel.deleted_at`）

## 迁移计划

### 部署步骤

1. 运行数据库迁移，创建 `iam_menu` 和 `iam_menu_permission` 表
2. 导入菜单种子数据（默认菜单结构）
3. 部署后端服务
4. 验证 API 端点可用

### 回滚策略

1. 删除菜单种子数据
2. 运行数据库回滚迁移
3. 回滚后端服务

## 开放问题

1. 菜单种子数据的初始结构需要与前端确认
2. 是否需要支持菜单的动态排序（拖拽排序）？当前设计使用 order 字段
