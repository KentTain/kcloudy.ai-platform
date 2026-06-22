## 上下文

租户管理后台（`/admin/*`）当前采用简化的认证模式：所有管理员登录后通过 `requiresAdminAuth: true` 即可访问全部管理功能。随着业务场景扩展，需要引入差异化权限控制：

- **租户管理员**（tenantAdmin）：完整的读写权限
- **普通管理员**（ordinaryAdmin）：只读权限

系统已有 tenant 模块的完整 RBAC 基础设施：

```
modules → module_roles → module_role_permissions → module_permissions
        → module_menus → module_menu_permissions
```

这些表通过 `ModuleDefinitionSyncService` 在启动时从模块定义（`module.py` 的 `get_module_definition()`）自动同步，支持声明式配置，无需手写种子数据。

## 目标 / 非目标

**目标：**

- 复用 tenant 模块现有的 RBAC 表结构实现管理员权限控制
- 通过模块定义声明菜单、权限、角色，启动时自动同步到数据库
- 二级菜单入库但侧边栏不显示，用于精确权限控制
- 前后端权限校验保持一致

**非目标：**

- 不实现复杂的多角色体系（仅两个固定角色）
- 不复用 IAM 模块的 RBAC（管理员权限体系独立）
- 不实现动态角色管理（角色定义固化在模块定义中）

## 决策

### 决策 1：复用 module_* 表而非新建独立权限体系

**理由：**

- tenant 模块已有完整的 `module_roles`、`module_permissions`、`module_menus` 等表
- `ModuleDefinitionSyncService` 支持声明式定义自动同步
- 与 IAM 的 RBAC 结构对齐（resource/action/code 字段一致）
- 避免重复造轮子

**替代方案：**

- 方案 A：程序硬编码角色权限 → 缺乏灵活性，与声明式架构不一致
- 方案 B：复用 IAM 的 permissions/roles 表 → 跨 schema 耦合，违反模块边界

### 决策 2：二级菜单入库，`is_visible=false`

**理由：**

- 一级菜单在侧边栏显示，二级菜单隐藏但参与权限控制
- 每个页面路由对应一个菜单节点，权限可精确到页面级
- 菜单与权限通过 `module_menu_permissions` 关联，查询高效

**数据结构示例：**

```
module_menus（tenant 模块）:
┌───────────────────────────────────────────────────┐
│ 租户管理 (is_visible=true, parent_id=null)        │  ← 侧边栏显示
│   path: /admin/tenants                             │
│                                                    │
│ ├─ 创建租户 (is_visible=false)                     │  ← 侧边栏隐藏
│ │    path: /admin/tenants/create                   │
│ │    permission_codes: ["tenant:tenant:write"]     │
│ │                                                  │
│ ├─ 租户详情 (is_visible=false)                     │
│ │    path: /admin/tenants/:id                      │
│ │    permission_codes: ["tenant:tenant:read"]      │
│ │                                                  │
│ └─ 编辑租户 (is_visible=false)                     │
│      path: /admin/tenants/:id/edit                 │
│      permission_codes: ["tenant:tenant:write"]     │
└───────────────────────────────────────────────────┘
```

### 决策 3：tenant_admins.role 存储角色编码

**理由：**

- 角色数量固定（tenantAdmin、ordinaryAdmin），单字段足够
- 通过角色编码可直接查询 `module_roles` 获取权限列表
- 查询链路：`tenant_admins.role` → `module_roles.code` → `module_role_permissions` → `module_permissions`

**替代方案：**

- 方案 A：创建 `tenant_admin_roles` 关联表 → 过度设计，角色固定无扩展需求

### 决策 4：登录时返回聚合数据

**理由：**

- 前端首次加载需要完整的角色、权限、菜单数据
- 避免前端多次请求
- 与 IAM 用户登录响应结构对齐

**响应结构：**

```typescript
interface AdminLoginResponse {
  token: string
  username: string
  is_default: boolean
  role: string                    // 新增：角色编码
  permissions: string[]           // 新增：权限码列表
}
```

### 决策 5：前端权限校验双轨制

**理由：**

- **菜单过滤**：后端根据权限过滤返回的菜单树
- **路由守卫**：前端检查 `meta.permissions`，无权限跳转 403
- **API 拦截**：后端中间件在 API 层校验权限

三层防护确保安全。

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|---------|
| 角色定义固化，扩展需改代码 | 作为演示项目，固定角色可接受；未来可扩展为动态角色管理 |
| 二级菜单数据量增加 | 菜单树由后端过滤后返回，前端无需全量渲染 |
| 权限码与路由 meta 手动维护 | 通过代码审查确保一致性；后续可考虑自动化校验 |
| API 权限校验可能遗漏 | 通过中间件集中处理，不依赖 Controller 层手动校验 |
