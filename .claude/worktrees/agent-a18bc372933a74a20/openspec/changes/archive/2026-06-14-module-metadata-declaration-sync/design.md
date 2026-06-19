## 上下文

### 当前状态

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           当前架构问题                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   后端                                      │
│   ───────────────────────────────────────────────────────                  │
│   • Module/ModuleMenu/ModulePermission/ModuleRole 存在于 tenant schema     │
│   • ModuleDescriptor 只有 get_routers()、get_seeds() 等方法                │
│   • 缺少 get_menus()、get_permissions()、get_default_roles()               │
│   • 元数据需要手动创建或通过分散的 seed 管理                                 │
│                                                                             │
│   前端 (Vue)                                                                │
│   ───────────────────────────────────────────────────────                  │
│   • AppNavMain.vue 中 defaultItems 硬编码菜单                              │
│   • ModuleDescriptor 接口有 getMenuItems() 但非强制                        │
│   • 菜单与后端 module_menus 表脱节                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 约束

1. **数据库不变更**：复用现有表结构，不新增迁移
2. **向后兼容**：现有 API 保持不变，新增接口
3. **渐进式迁移**：模块可逐步实现 `get_module_definition()`

### 利益相关者

- **业务模块开发者**：需要声明自己模块的菜单/权限
- **平台管理员**：需要在管理后台查看模块元数据
- **租户用户**：需要根据权限看到正确的菜单

## 目标 / 非目标

**目标：**

1. 建立**声明式**的模块元数据定义机制
2. 实现**自动同步**，应用启动时将模块声明同步到数据库
3. 提供**用户菜单 API**，返回当前用户有权限的菜单树
4. **前端动态获取**菜单，移除硬编码

**非目标：**

1. 不支持租户定制模块菜单/角色（模块定义对所有租户固定）
2. 不改变现有模块管理 API（`/admin/v1/modules`）
3. 不实现模块版本管理或灰度发布

## 决策

### 决策 1：扩展 ModuleDescriptor 协议

**选择**：在 Python 后端扩展 `ModuleDescriptor` 协议，新增 `get_module_definition()` 方法

**原因**：
- 与现有协议风格一致（get_routers、get_seeds 等）
- 可选实现，未实现的模块保持手动管理
- 类型安全，IDE 支持好

**替代方案**：
- ❌ 使用独立的配置文件（YAML/JSON）：需要额外的解析和验证
- ❌ 使用 seed 函数：非声明式，难以在运行时查询

**数据结构设计**：

```python
@dataclass
class MenuDef:
    """菜单定义"""
    code: str                    # 唯一标识，如 "iam.users"
    name: str                    # 显示名称
    path: str                    # 前端路由路径
    icon: str | None = None      # 图标标识
    parent_code: str | None = None  # 父菜单 code
    sort_order: int = 0
    is_visible: bool = True

@dataclass
class PermissionDef:
    """权限定义"""
    code: str                    # 唯一标识，如 "iam:user:read"
    name: str                    # 显示名称
    resource: str                # 资源名称
    action: str                  # 操作：read/write/delete
    description: str | None = None

@dataclass
class RoleDef:
    """默认角色定义"""
    code: str                    # 角色编码
    name: str                    # 角色名称
    description: str | None = None
    permission_codes: list[str] = field(default_factory=list)
    is_system: bool = False      # 是否系统内置

@dataclass
class ModuleDefinition:
    """模块完整定义"""
    code: str                    # 模块编码
    name: str                    # 模块名称
    description: str | None = None
    icon: str | None = None
    version: str = "1.0.0"
    menus: list[MenuDef] = field(default_factory=list)
    permissions: list[PermissionDef] = field(default_factory=list)
    default_roles: list[RoleDef] = field(default_factory=list)
```

### 决策 2：同步策略

**选择**：应用启动时自动同步，以模块定义为准

**同步算法**：

```
for module in registry.get_all_modules():
    definition = module.get_module_definition()
    if not definition:
        continue  # 未实现的模块跳过
    
    # 1. 同步模块基本信息
    upsert_module(definition)
    
    # 2. 同步菜单（处理父子关系）
    for menu in definition.menus:
        upsert_menu(module_id, menu)
    delete_orphan_menus(module_id, [m.code for m in definition.menus])
    
    # 3. 同步权限
    for perm in definition.permissions:
        upsert_permission(module_id, perm)
    delete_orphan_permissions(module_id, [p.code for p in definition.permissions])
    
    # 4. 同步角色和权限关联
    for role in definition.default_roles:
        upsert_role(module_id, role)
    delete_orphan_roles(module_id, [r.code for r in definition.default_roles])
```

**幂等性保证**：
- 基于 `code` 字段做 upsert
- 菜单父子关系通过 `parent_code` 解析，延迟处理
- 角色权限关联整体替换

**替代方案**：
- ❌ 通过 seed 命令手动触发：运维复杂，容易遗漏
- ❌ 监听文件变化热更新：过于复杂，演示项目不需要

### 决策 3：用户菜单 API

**选择**：新增 `GET /api/v1/user/menus` 接口

**API 设计**：

```
GET /api/v1/user/menus
Authorization: Bearer <token>

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "code": "iam",
      "name": "IAM",
      "icon": "Settings",
      "path": null,
      "children": [
        {
          "id": "uuid",
          "code": "iam.users",
          "name": "用户管理",
          "path": "/iam/users",
          "children": []
        }
      ]
    }
  ]
}
```

**权限过滤逻辑**：
1. 获取当前用户的所有权限码
2. 查询所有已启用模块的菜单
3. 过滤：用户有权限的菜单或其父菜单
4. 构建树形结构返回

**替代方案**：
- ❌ 在登录时返回菜单：权限变更后需要重新登录
- ❌ 前端自行过滤：需要传输所有菜单，浪费带宽

### 决策 4：前端改造

**选择**：从 API 获取菜单，存储到 Pinia store

**改造点**：
1. 新增 `useMenuStore`，提供 `fetchMenus()` 方法
2. 登录成功后调用 `fetchMenus()`
3. `AppNavMain` 从 store 获取菜单数据
4. 删除硬编码的 `defaultItems`

**组件接口保持不变**：
```vue
<AppNavMain :items="menuStore.menus" />
```

## 风险 / 权衡

### 风险 1：模块定义与数据库不一致

**风险**：如果开发者修改了模块定义但未重启应用，数据库中的数据会过时

**缓解措施**：
- 文档说明：模块定义变更后需要重启应用
- 提供 `/admin/v1/modules/sync` 手动触发同步接口（可选）

### 风险 2：菜单 parent_code 循环引用

**风险**：如果配置错误导致菜单循环引用

**缓解措施**：
- 同步时检测循环引用，抛出明确错误
- 日志记录同步失败原因

### 风险 3：前端图标映射

**风险**：后端返回 icon 字符串（如 "Settings"），前端需要映射到组件

**缓解措施**：
- 使用图标名称映射表
- 前端定义 `ICON_MAP: Record<string, FunctionalComponent>`

## 迁移计划

### 阶段 1：基础设施（无破坏性）

1. 新增 `framework/module/definition.py` 数据类
2. 扩展 `framework/module/descriptor.py` 协议
3. 新增 `framework/module/sync_service.py` 同步服务
4. 修改 `application_web.py` 启动时调用同步

### 阶段 2：模块实现

1. IAM 模块实现 `get_module_definition()`
2. Tenant 模块实现 `get_module_definition()`
3. AI 模块实现 `get_module_definition()`

### 阶段 3：前端改造

1. 新增 `framework/api/menu.ts`
2. 修改 `framework/stores/menu.ts`，新增 `fetchMenus()`
3. 修改 `AppNavMain.vue`，从 store 获取菜单
4. 删除硬编码菜单

### 回滚策略

- 后端：模块不实现 `get_module_definition()` 即回退到手动管理
- 前端：保留 `items` prop，可传入静态菜单

## 开放问题

1. **权限通配符**：`iam:*:read` 这样的通配符权限是否需要支持？当前权限过滤是精确匹配。
   
   *建议*：第一版不支持通配符，后续如有需求再扩展。

2. **菜单排序**：跨模块的菜单如何排序？当前只有模块内的 sort_order。
   
   *建议*：在 `ModuleDefinition` 中增加 `sort_order` 字段，控制模块级别的排序。

3. **前端多语言**：菜单名称是否需要支持多语言？
   
   *建议*：当前不需要，名称直接使用中文。
