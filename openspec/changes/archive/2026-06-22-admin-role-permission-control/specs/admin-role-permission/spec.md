## 新增需求

### 需求:管理员角色定义
系统必须在 `module_roles` 表中为 tenant 模块预置两个管理员角色，角色及其权限通过模块定义声明，启动时自动同步。

#### 场景:租户管理员角色存在
- **当** 系统启动并同步模块定义
- **那么** `module_roles` 表中存在 `code=tenantAdmin` 的记录，且 `module_id` 为 tenant 模块的 ID
- **那么** 该角色通过 `module_role_permissions` 关联了 tenant 模块的所有权限（action 包括 read、write、delete）

#### 场景:普通管理员角色存在
- **当** 系统启动并同步模块定义
- **那么** `module_roles` 表中存在 `code=ordinaryAdmin` 的记录，且 `module_id` 为 tenant 模块的 ID
- **那么** 该角色通过 `module_role_permissions` 仅关联了 tenant 模块的只读权限（action=read）

#### 场景:角色已存在时跳过创建
- **当** `module_roles` 表中已存在 `code=tenantAdmin` 的记录
- **那么** 系统同步时跳过该角色的创建，不重复插入

### 需求:管理员账号关联角色
`tenant_admins` 表必须支持存储关联的角色编码。

#### 场景:管理员账号设置角色
- **当** 创建或更新 `tenant_admins` 记录
- **那么** `role` 字段可以存储角色编码（如 "tenantAdmin"、"ordinaryAdmin"）
- **那么** 该字段为 VARCHAR(50)，NOT NULL，默认值为 "ordinaryAdmin"

#### 场景:默认管理员初始化角色
- **当** 系统首次运行 admin_seed 种子数据
- **那么** 创建的默认管理员账号的 `role` 字段为 "tenantAdmin"

### 需求:管理员登录返回角色和权限
管理员登录接口必须返回管理员的角色编码和权限列表。

#### 场景:租户管理员登录
- **当** 租户管理员（role=tenantAdmin）登录成功
- **那么** 响应数据中包含 `role: "tenantAdmin"`
- **那么** 响应数据中包含 `permissions: ["tenant:module:read", "tenant:module:write", "tenant:module:delete", "tenant:tenant:read", "tenant:tenant:write", "tenant:tenant:delete", "tenant:resource:read", "tenant:resource:write", "tenant:resource:delete"]`

#### 场景:普通管理员登录
- **当** 普通管理员（role=ordinaryAdmin）登录成功
- **那么** 响应数据中包含 `role: "ordinaryAdmin"`
- **那么** 响应数据中包含 `permissions: ["tenant:module:read", "tenant:tenant:read", "tenant:resource:read"]`

#### 场景:管理员无角色
- **当** 管理员的 `role` 字段为角色不存在于 `module_roles` 中的值
- **那么** 登录成功但 `permissions` 返回空数组

### 需求:管理员菜单权限过滤
管理员菜单接口必须根据其角色权限过滤返回的菜单树。

#### 场景:租户管理员获取全部菜单
- **当** 租户管理员请求菜单
- **那么** 返回的菜单树包含 tenant 模块下所有 `is_visible=true` 的一级菜单及其二级子菜单

#### 场景:普通管理员仅获取只读菜单
- **当** 普通管理员请求菜单
- **那么** 返回的菜单树仅包含关联了 action=read 权限的菜单
- **那么** 写操作菜单（如关联了 tenant:tenant:write 的菜单项）不出现在结果中

#### 场景:无菜单权限
- **当** 管理员没有任何菜单权限
- **那么** 返回空数组

### 需求:API 层权限校验
后端中间件必须在 API 层根据管理员角色权限拦截无权操作。

#### 场景:普通管理员执行写操作被拒绝
- **当** 普通管理员（role=ordinaryAdmin）调用 POST /tenant/admin/v1/tenants 创建租户
- **那么** 返回 HTTP 403 错误，提示权限不足

#### 场景:租户管理员执行写操作被允许
- **当** 租户管理员（role=tenantAdmin）调用 POST /tenant/admin/v1/tenants 创建租户
- **那么** 请求正常处理

### 需求:前端路由权限守卫
前端路由守卫必须检查 admin 路由的 `meta.permissions`。

#### 场景:无权限访问写页面被拒
- **当** 普通管理员导航到 `/admin/tenants/create`
- **那么** 路由守卫重定向到 `/403` 无权限页面

#### 场景:有权限访问读页面
- **当** 租户管理员导航到 `/admin/tenants/:id`
- **那么** 路由守卫正常放行，页面正常渲染

#### 场景:无权限的按钮不可见
- **当** 普通管理员查看租户列表页
- **那么** "创建租户"按钮不显示或禁用
- **那么** "编辑"按钮不显示或禁用

### 需求:二级菜单入库但侧边栏隐藏
模块定义必须支持声明隐藏的二级菜单，菜单入库参与权限控制但不显示在侧边栏。

#### 场景:侧边栏不显示隐藏菜单
- **当** 管理员登录后渲染侧边栏
- **那么** 仅显示 `is_visible=true` 的一级菜单项
- **那么** `is_visible=false` 的二级菜单项不出现在侧边栏

#### 场景:隐藏菜单参与权限控制
- **当** 普通管理员直接访问 `/admin/tenants/create`
- **那么** 虽然该菜单 `is_visible=false` 不在侧边栏，但路由守卫仍检查权限并拦截

### 需求:模块定义中权限码通配符支持
模块角色定义的 `permission_codes` 必须支持通配符模式，自动展开为具体权限。

#### 场景:通配符展开为所有权限
- **当** 角色定义的 `permission_codes` 包含 "tenant:*:*"
- **那么** 系统自动将其展开为 tenant 模块下所有已存在的权限（如 tenant:module:read、tenant:tenant:write 等）

#### 场景:通配符展开为指定操作
- **当** 角色定义的 `permission_codes` 包含 "tenant:*:read"
- **那么** 系统自动将其展开为 tenant 模块下所有 action=read 的权限
