## 上下文

当前系统存在以下问题：
1. **迁移历史混乱**：多个增量迁移文件，包含废弃的字段和表结构
2. **命名语义不清**：`Department`（部门）与实际业务场景"组织"不符
3. **角色定义分散**：每个模块独立定义角色，用户需要分配多个角色才能获得完整权限
4. **初始化流程复杂**：缺少统一的初始化顺序，数据依赖关系不清晰

**约束条件**：
- 必须保持与现有三层架构一致（Controller → Service → Model）
- 必须遵循现有的模块定义和同步机制
- 所有变更必须在单一迁移中完成，不保留历史数据

## 目标 / 非目标

**目标：**
1. 创建清晰、干净的单一初始化迁移
2. 建立 `Organization` 模型，替代 `Department`，语义更准确
3. 实现共享全局角色（`sysAdmin`、`normalUser`），简化权限管理
4. 重构初始化流程，明确数据依赖和执行顺序
5. 同步更新前端所有相关页面和组件

**非目标：**
- 不实现历史数据迁移（删除所有表重建）
- 不修改现有的权限校验逻辑（`PermissionCheckService`）
- 不改变 RBAC 同步机制的核心架构

## 决策

### 决策 1：全局角色存储位置

**选择**：全局角色定义在 tenant 模块的 `module_roles` 表中

**理由**：
- tenant 模块是基础模块，无依赖其他业务模块
- 符合"模块定义层 → 租户实例层"的同步架构
- 复用现有的 `ModuleDefinitionSyncService` 同步机制

**替代方案**：
- ❌ 在 framework 层定义全局角色：违反"framework 不依赖业务模块"原则
- ❌ 创建独立的 global_roles 表：增加复杂度，无法复用现有同步机制

### 决策 2：全局角色权限编码格式

**选择**：使用通配符匹配

```python
sysAdmin  → ["*:*:*"]     # 匹配所有权限
normalUser → ["*:*:read"]  # 匹配所有 read 权限
```

**理由**：
- 系统已支持 `fnmatch` 通配符匹配（`ModuleDefinitionSyncService._expand_permission_codes`）
- 自动适应新模块的权限，无需手动维护
- 保持向后兼容

**替代方案**：
- ❌ 动态聚合所有模块权限：每次同步需重新计算，复杂度高
- ❌ 硬编码权限列表：模块变更需同步修改，维护成本高

### 决策 3：Organization 模型的 parent_id 设计

**选择**：`parent_id` 允许 `NULL`，表示顶级组织

**理由**：
- 当前 `Department.parent_id` 已设置为 `nullable=True`
- 保持一致性，减少变更风险
- 顶级组织无需虚拟根节点

### 决策 4：初始化数据执行顺序

**选择**：按模块依赖顺序执行

```
tenant seeds:
  1. resource_config_seed  # 资源配置（无依赖）
  2. global_role_seed      # 全局角色（无依赖）
  3. tenant_seed           # 默认租户（依赖 resource_config）
  4. admin_seed            # 默认管理员（依赖 tenant）

iam seeds:
  5. organization_seed     # 默认组织（依赖 tenant, user）
  6. user_seed             # 默认用户（依赖 tenant, role, organization）
```

**理由**：
- 明确数据依赖关系
- 避免外键约束失败
- 便于调试和维护

## 风险 / 权衡

### 风险 1：破坏性变更影响现有功能

**风险描述**：
- API 路径变更（`/departments` → `/organizations`）
- 数据库表名变更
- 前端路由变更

**缓解措施**：
- 这是演示项目，不涉及生产环境迁移
- 完整更新前后端所有引用
- 提供完整的变更文件清单

### 风险 2：全局角色权限过于宽泛

**风险描述**：
- `sysAdmin` 拥有所有权限，可能超出预期
- `normalUser` 的 `*:*:read` 可能暴露敏感数据

**缓解措施**：
- 在角色描述中明确说明权限范围
- 后续可按需创建更细粒度的角色
- 文档记录角色权限语义

### 风险 3：角色同步时机

**风险描述**：
- 模块定义同步（启动时）vs 租户模块分配同步（运行时）
- 全局角色需要在两者中正确处理

**缓解措施**：
- 全局角色在启动时同步到 `module_roles`
- 租户模块分配时，通过 `code` 匹配全局角色
- 同步服务更新逻辑：优先查找全局角色

## 数据模型变更

### Organization 模型（替代 Department）

```python
# iam/models/organization.py
class Organization(BaseModel, TreeNodeMixin, TenantMixin):
    """组织模型"""

    __tablename__ = "organizations"

    parent_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="父组织ID"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="组织名称"
    )
    code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="组织编码"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序号"
    )
    leader_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, comment="组织负责人ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", comment="状态"
    )
```

### UserOrganization 模型（替代 UserDepartment）

```python
# iam/models/organization.py
class UserOrganization(BaseModel, TenantMixin):
    """用户-组织关联模型"""

    __tablename__ = "user_organizations"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="用户ID"
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, comment="组织ID"
    )
    is_leader: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否负责人"
    )
```

### 全局角色定义

```python
# tenant/module.py 或 tenant/migrations/seeds/global_role_seed.py
GLOBAL_ROLES = [
    ModuleRole(
        module_id=None,  # 全局角色不属于任何模块
        code="sysAdmin",
        name="系统管理员",
        description="拥有所有模块的所有权限",
        is_system=True,
    ),
    ModuleRole(
        module_id=None,
        code="normalUser",
        name="普通用户",
        description="拥有所有模块的只读权限",
        is_system=True,
    ),
]
```

## 初始化数据设计

### 默认组织创建规则

```python
# 为每个租户创建默认顶级组织
organization = Organization(
    tenant_id=tenant_id,
    name=tenant_name,       # 使用租户名称
    code=tenant_code,       # 使用租户编码
    parent_id=None,         # 顶级组织
    leader_id=admin_user_id,  # 默认管理员为负责人
    status="active",
)
```

### 默认用户关联

```python
# 创建用户-组织关联
user_organization = UserOrganization(
    user_id=admin_user_id,
    organization_id=default_org_id,
    is_leader=True,  # 默认管理员为组织负责人
)

# 分配角色
user_role = UserRole(
    user_id=admin_user_id,
    role_id=sysAdmin_role_id,  # 通过 code="sysAdmin" 查找
)
```
