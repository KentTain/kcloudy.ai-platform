## 上下文

### 当前状态

系统采用双层定义架构：
- **模块定义层（tenant schema）**：定义全局的模块、菜单、权限、角色
- **租户实例层（iam schema）**：租户具体的菜单、权限、角色实例

当前同步机制存在以下缺失：
1. `ModuleMenuPermission` 模型不存在，菜单-权限关联无法定义
2. `ModuleRolePermission` → `RolePermission` 同步未实现
3. `UserTenant.role` 与 RBAC 角色体系隔离

### 约束

- 必须保持向后兼容，现有租户数据不受影响
- 遵循三层架构（Controller → Service → Model）
- 同步逻辑复用 `ModuleSyncService` 现有模式
- 数据库迁移使用 Alembic

## 目标 / 非目标

**目标：**
- 实现完整的模块定义层到租户实例层的 RBAC 同步
- 租户创建时自动创建 owner/admin/member 角色
- 废弃 `UserTenant.role`，改用 RBAC 管理租户身份

**非目标：**
- 不迁移现有租户的 `UserTenant.role` 数据
- 不修改前端租户管理 UI（本次仅后端变更）
- 不实现租户角色的细粒度权限配置 UI

## 决策

### 决策 1：新增 ModuleMenuPermission 模型

**选择**：新增 `tenant/models/module_menu_permission.py` 模型

**理由**：
- 与 `ModuleRolePermission` 模式一致
- 支持模块定义层定义菜单所需权限
- 可通过 `ref_id` 追溯到模块定义

**替代方案**：
- ❌ 在 `ModuleMenu` 中添加 `permission_ids` JSON 字段 - 无法保证引用完整性
- ❌ 使用 `MenuPermission.ref_id` 关联 - 语义不清晰

**模型定义**：
```python
# tenant/models/module_menu_permission.py
class ModuleMenuPermission(BaseModel):
    """模块菜单-权限关联模型"""

    __tablename__ = "module_menu_permissions"

    module_menu_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_menus.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块菜单ID",
    )
    module_permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("module_permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="模块权限ID",
    )

    __table_args__ = (
        UniqueConstraint(
            "module_menu_id",
            "module_permission_id",
            name="uq_module_menu_permissions_menu_perm",
        ),
    )
```

### 决策 2：实现 ModuleRolePermission 同步

**选择**：在 `ModuleSyncService` 中新增同步方法

**实现位置**：`iam/services/module_sync_service.py`

**同步逻辑**：
```
模块定义层                          租户实例层
────────────                       ────────────
ModuleRolePermission    ───────▶   RolePermission
  module_role_id                    role_id (通过 ref_id 查找)
  module_permission_id              permission_id (通过 ref_id 查找)
```

**触发时机**：
- 模块分配到租户时（`assign_module_to_tenant`）
- 模块角色权限创建时（`sync_module_role_permission_created`）
- 模块角色权限更新/删除时（事件监听）

### 决策 3：租户角色自动创建

**选择**：在 `TenantService.create()` 中自动创建角色

**角色定义**：
| 角色 | code | 权限 |
|------|------|------|
| 租户所有者 | `{tenant_id}:owner` | 所有模块的所有权限 |
| 租户管理员 | `{tenant_id}:admin` | 模块管理权限（不含删除） |
| 租户成员 | `{tenant_id}:member` | 基础访问权限 |

**角色编码规则**：
- 全局角色：`admin`, `user` 等（无租户前缀）
- 租户角色：`{tenant_id}:owner`, `{tenant_id}:admin`, `{tenant_id}:member`

**替代方案**：
- ❌ 使用固定的 `owner/admin/member` 编码 - 可能与全局角色冲突
- ❌ 租户角色存储在单独的 `TenantRole` 表 - 增加复杂度

### 决策 4：UserTenant.role 处理策略

**选择**：保留字段，标记为废弃，新功能使用 RBAC

**迁移策略**：
1. 阶段一（本次）：新租户使用 RBAC，旧租户保持原状
2. 阶段二（后续）：提供迁移脚本，批量迁移旧租户
3. 阶段三（未来）：移除 `UserTenant.role` 字段

**兼容性处理**：
```python
# 用户加入租户时
async def add_user_to_tenant(user_id: str, tenant_id: str, role: str):
    # 旧方式：设置 UserTenant.role（保留兼容）
    user_tenant = UserTenant(user_id=user_id, tenant_id=tenant_id, role=role)

    # 新方式：分配 RBAC 角色
    role_code = f"{tenant_id}:{role}"
    rbac_role = await RoleService.get_by_code(role_code, tenant_id)
    if rbac_role:
        await UserRoleService.assign_role(user_id, rbac_role.id)
```

## 风险 / 权衡

### 风险 1：同步性能问题

**风险**：模块分配到大量租户时，同步操作耗时

**缓解措施**：
- 使用批量插入而非逐条插入
- 在事务中执行，失败时全部回滚
- 添加异步任务支持（可选）

### 风险 2：角色编码冲突

**风险**：租户角色编码 `{tenant_id}:owner` 可能与未来定义的全局角色冲突

**缓解措施**：
- 全局角色编码禁止包含 `:` 字符
- 文档明确角色编码规范
- 添加编码校验逻辑

### 风险 3：权限缓存失效不完整

**风险**：`RolePermission` 同步后，用户权限缓存未失效

**缓解措施**：
- 在 `sync_module_role_permission_created` 完成后调用 `invalidate_tenant_permission_cache`
- 在 `RolePermission` CRUD 操作中触发缓存失效

### 权衡：新旧角色体系并存

**权衡**：保留 `UserTenant.role` 导致两套体系并存

**接受理由**：
- 保证向后兼容
- 给现有租户迁移时间
- 新功能直接使用 RBAC，逐步过渡

## 数据库变更

### 新增表

```sql
-- tenant.module_menu_permissions
CREATE TABLE tenant.module_menu_permissions (
    id VARCHAR(36) PRIMARY KEY,
    module_menu_id VARCHAR(36) NOT NULL REFERENCES tenant.module_menus(id) ON DELETE CASCADE,
    module_permission_id VARCHAR(36) NOT NULL REFERENCES tenant.module_permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_module_menu_permissions_menu_perm UNIQUE (module_menu_id, module_permission_id)
);

CREATE INDEX ix_module_menu_permissions_menu_id ON tenant.module_menu_permissions(module_menu_id);
CREATE INDEX ix_module_menu_permissions_permission_id ON tenant.module_menu_permissions(module_permission_id);
```

### 新增索引

无（现有表结构无需变更）

## 迁移计划

### 阶段 1：数据库迁移

1. 创建 `module_menu_permissions` 表
2. 创建 `ModuleMenuPermission` 模型

### 阶段 2：同步逻辑实现

1. 实现 `sync_module_role_permission_created()`
2. 实现 `sync_module_menu_permission_created()`
3. 集成到模块分配流程

### 阶段 3：租户角色自动创建

1. 修改 `TenantService.create()`
2. 创建租户角色种子数据

### 阶段 4：验证

1. 单元测试覆盖同步逻辑
2. 集成测试验证完整流程
3. 现有功能回归测试

## 开放问题

1. **租户角色权限如何配置？** - 初期使用固定权限模板，后续可扩展为可配置
2. **现有租户如何迁移？** - 需要单独的迁移脚本和执行计划
3. **前端是否需要修改？** - 本次仅后端变更，前端可继续使用 `UserTenant.role` 显示
