## 新增需求

### 需求:菜单模型定义

系统必须提供 Menu 模型，继承 BaseModel 和 TreeNodeMixin，存储在 `iam` schema。

Menu 模型必须包含以下字段：
- `id`: 主键，UUID 字符串
- `parent_id`: 父菜单 ID，可为空，外键关联 menus.id
- `module`: 所属模块标识（demo/iam/tenant）
- `code`: 菜单编码，唯一约束，格式为 `module:name`
- `name`: 菜单名称（显示用）
- `path`: 前端路由路径
- `icon`: 图标标识，可为空
- `is_visible`: 是否显示，默认 true
- `deployment_base_url`: 模块部署地址，可为空

Menu 模型必须继承 TreeNodeMixin 提供的树形字段：
- `tree_leaf`: 是否为叶子节点
- `tree_level`: 树层级
- `tree_sort`: 排序号
- `tree_sorts`: 排序路径
- `tree_names`: 名称路径
- `parent_ids`: 父 ID 路径

#### 场景:创建顶级菜单成功
- **当** 创建菜单时 parent_id 为空
- **那么** 菜单成为顶级节点，tree_level 为 0

#### 场景:创建子菜单成功
- **当** 创建菜单时指定有效的 parent_id
- **那么** 菜单成为父菜单的子节点，tree_level 为父节点 tree_level + 1

#### 场景:菜单编码唯一性校验
- **当** 创建菜单时使用已存在的 code
- **那么** 系统拒绝创建并返回唯一约束错误

### 需求:菜单权限关联

系统必须提供 MenuPermission 模型，关联菜单和权限。

MenuPermission 模型必须包含以下字段：
- `id`: 主键，UUID 字符串
- `menu_id`: 菜单 ID，外键关联 menus.id，级联删除
- `permission_id`: 权限 ID，外键关联 permissions.id，级联删除

系统必须确保 menu_id 和 permission_id 组合的唯一性。

#### 场景:菜单关联权限成功
- **当** 为菜单添加权限关联
- **那么** 拥有该权限的用户可以看到此菜单

#### 场景:菜单关联多个权限
- **当** 菜单关联多个权限
- **那么** 用户拥有任一权限即可看到此菜单

#### 场景:删除菜单时级联删除权限关联
- **当** 删除菜单
- **那么** 该菜单的所有权限关联自动删除

### 需求:用户菜单查询 API

系统必须提供 `GET /api/v1/menus/user` API，返回当前登录用户可见的菜单树。

API 响应必须包含以下字段：
- `menus`: 菜单树数组，每个菜单包含：
  - `id`: 菜单 ID
  - `parent_id`: 父菜单 ID
  - `module`: 所属模块
  - `code`: 菜单编码
  - `name`: 菜单名称
  - `path`: 路由路径
  - `icon`: 图标
  - `tree_level`: 树层级
  - `tree_sort`: 排序
  - `deployment_base_url`: 部署地址
  - `children`: 子菜单数组

#### 场景:已登录用户获取菜单
- **当** 已登录用户请求菜单列表
- **那么** 系统返回该用户有权限查看的菜单树

#### 场景:未登录用户请求菜单
- **当** 未登录用户请求菜单列表
- **那么** 系统返回 401 未授权错误

#### 场景:用户无任何菜单权限
- **当** 用户没有任何菜单权限
- **那么** 系统返回空数组

#### 场景:菜单无权限限制
- **当** 菜单未关联任何权限
- **那么** 所有登录用户可见此菜单（is_visible = true 时）

### 需求:IAM 模块迁移重建

系统必须重建 IAM 模块的所有数据库表，确保归属 `iam` schema。

迁移文件必须：
- 创建 `iam` schema
- 在 schema 下创建所有 IAM 模型表
- 版本表 `alembic_version` 也必须在 `iam` schema

#### 场景:执行 IAM 迁移
- **当** 执行 `manage.py db migrate --module iam`
- **那么** 所有 IAM 表创建在 `iam` schema 下

#### 场景:回滚 IAM 迁移
- **当** 执行 `manage.py db downgrade --module iam`
- **那么** 删除 `iam` schema 及其所有表

### 需求:Demo 模块迁移重建

系统必须重建 Demo 模块的所有数据库表，确保归属 `demo` schema。

迁移文件必须：
- 创建 `demo` schema
- 在 schema 下创建所有 Demo 模型表
- 版本表 `alembic_version` 也必须在 `demo` schema

#### 场景:执行 Demo 迁移
- **当** 执行 `manage.py db migrate --module demo`
- **那么** 所有 Demo 表创建在 `demo` schema 下

### 需求:菜单种子数据

系统必须提供菜单种子数据，初始化默认菜单配置。

默认菜单必须包含：
- Demo 模块：首页、知识库
- IAM 模块：用户管理、角色管理、部门管理
- Tenant 模块：租户管理

#### 场景:执行种子数据初始化
- **当** 执行 `manage.py seed --module iam`
- **那么** 系统创建默认菜单及其权限关联

#### 场景:种子数据幂等性
- **当** 多次执行种子数据初始化
- **那么** 已存在的菜单不重复创建

## 修改需求

无。

## 移除需求

无。
