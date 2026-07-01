# 审计日志自动化记录设计文档

## 概述

本文档描述了审计日志自动化记录系统的设计方案，采用装饰器 + 事件混合模式，实现统一、声明式的审计日志记录机制。

## 设计目标

- **统一处理**：通过装饰器实现声明式审计日志记录
- **灵活扩展**：支持简单场景（装饰器）和复杂场景（事件机制）
- **数据完整**：记录完整的 before_data/after_data
- **可追溯性**：关联权限编码，支持权限追溯

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Controller Layer                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  @audit_log(module="iam", resource="user", action="create")  │  │
│  │  async def create_user(...) -> User:                   │  │
│  │      # 业务逻辑                                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Framework Audit Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Decorator   │──│ AuditService │──│ AuditContext │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database (AuditLog)                        │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

1. **AuditContext** - 审计上下文，传递审计日志所需信息
2. **AuditService** - 审计服务，负责记录审计日志
3. **audit_log 装饰器** - 声明式审计日志记录
4. **AuditLog 模型** - 审计日志数据存储

## 数据模型

### AuditLog 模型字段

#### 字段类型变更（枚举 → 字符串）

| 字段 | 当前类型 | 新类型 | 说明 |
|------|---------|--------|------|
| `business_domain` | `AuditLogBusinessType` (枚举) | `str` | 模块名称，如 `iam`、`tenant` |
| `operation_type` | `AuditLogOperationType` (枚举) | `str` | 权限 action，如 `create`、`update`、`delete` |
| `resource_type` | `AuditLogResourceType` (枚举) | `str` | 权限 resource，如 `user`、`role` |

#### 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `permission_code` | `str` | 权限编码，如 `iam:user:create` |

#### 字段重命名

| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| `details` | `detail` | 单数形式，统一命名 |

#### detail 字段格式

```json
{
  "text": "张三在2024-01-15 10:30:00对用户\"郭增强\"进行了创建操作",
  "template_key": "audit.user.create",
  "params": {
    "operator_name": "张三",
    "operated_at": "2024-01-15 10:30:00",
    "resource_name": "郭增强",
    "operation_type": "创建"
  },
  "extra": {
    "role_name": "管理员",
    "library_name": "销售管理文档库"
  }
}
```

**字段说明：**
- `text` - 渲染后的文本，直接展示使用
- `template_key` - 模板 Key，支持国际化
- `params` - 模板参数
- `extra` - 额外上下文信息（可选）

## 目录结构

```
framework/
├── audit/
│   ├── __init__.py              # 导出公共接口
│   ├── decorator.py             # audit_log 装饰器
│   ├── service.py               # AuditService 审计服务
│   ├── context.py               # AuditContext 审计上下文
│   ├── templates.py             # 审计日志模板
│   └── utils.py                 # 工具函数
```

## 核心组件设计

### AuditContext

```python
@dataclass
class AuditContext:
    """审计上下文，用于传递审计日志所需信息"""
    
    # 基础信息（必填）
    module: str                              # 模块名称：iam, tenant, ai
    resource: str                            # 资源类型：user, role, organization
    action: str                              # 操作类型：create, update, delete
    
    # 资源信息（必填）
    resource_id: str | None = None           # 资源 ID
    resource_name: str = ""                  # 资源名称（用于展示）
    
    # 数据快照（可选）
    before_data: dict | None = None          # 操作前数据
    after_data: dict | None = None           # 操作后数据
    
    # 详情信息（可选）
    detail_extra: dict | None = None         # 额外上下文信息
```

### AuditService

```python
class AuditService:
    """审计日志服务"""
    
    async def record(
        self,
        session: AsyncSession,
        context: AuditContext,
    ) -> None:
        """
        记录审计日志
        
        Args:
            session: 数据库会话（由调用方管理事务）
            context: 审计上下文
        """
        # 1. 获取当前用户和租户信息
        user_id = get_user_id()
        user_name = get_user_name()
        tenant_id = get_tenant_id()
        
        # 2. 获取权限编码（从上下文获取）
        permission_code = get_permission_code()
        
        # 3. 构建 detail 字段
        detail = self._build_detail(context, user_name)
        
        # 4. 创建审计日志记录
        audit_log = AuditLog(
            tenant_id=tenant_id,
            business_domain=context.module,
            operation_type=context.action,
            resource_type=context.resource,
            resource_id=context.resource_id,
            resource_name=context.resource_name,
            permission_code=permission_code,
            operator_by=user_id,
            operator_name=user_name,
            operated_at=datetime.now(timezone.utc),
            before_data=context.before_data,
            after_data=context.after_data,
            detail=detail,
        )
        
        session.add(audit_log)
        # 不 commit，由调用方管理事务
```

### audit_log 装饰器

```python
def audit_log(
    module: str,
    resource: str,
    action: str,
    resource_id_getter: Callable | None = None,
    resource_name_getter: Callable | None = None,
    before_data_getter: Callable | None = None,
    detail_extra: dict | None = None,
):
    """
    审计日志装饰器
    
    Args:
        module: 模块名称
        resource: 资源类型
        action: 操作类型
        resource_id_getter: 从参数/返回值获取资源 ID
        resource_name_getter: 从参数/返回值获取资源名称
        before_data_getter: 获取操作前数据（更新/删除场景）
        detail_extra: 额外的 detail 信息
    
    Example:
        @audit_log(
            module="iam",
            resource="user",
            action="create",
            resource_id_getter=lambda result: result.id,
            resource_name_getter=lambda result: result.username,
        )
        async def create_user(self, session, user_create) -> User:
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 执行前：获取 before_data（如果有）
            before_data = None
            if before_data_getter:
                before_data = await before_data_getter(args, kwargs)
            
            # 2. 执行业务逻辑
            result = await func(*args, **kwargs)
            
            # 3. 执行后：构建审计上下文
            context = AuditContext(
                module=module,
                resource=resource,
                action=action,
                detail_extra=detail_extra,
            )
            
            # 4. 获取资源 ID 和名称
            if resource_id_getter:
                context.resource_id = resource_id_getter(result)
            if resource_name_getter:
                context.resource_name = resource_name_getter(result)
            
            # 5. 获取 before_data（如果之前没有获取）
            if before_data is None and before_data_getter:
                before_data = await before_data_getter(args, kwargs)
            context.before_data = before_data
            
            # 6. 获取 after_data（从返回值）
            if result and hasattr(result, 'to_dict'):
                context.after_data = result.to_dict()
            
            # 7. 记录审计日志
            session = _extract_session(args, kwargs)
            if session:
                await audit_service.record(session, context)
            
            return result
        return wrapper
    return decorator
```

## 使用示例

### 简单场景（创建操作）

```python
# iam/services/user_service.py

from framework.audit.decorator import audit_log

class UserService:
    @audit_log(
        module="iam",
        resource="user",
        action="create",
        resource_id_getter=lambda result: result.id,
        resource_name_getter=lambda result: result.username,
    )
    async def create_user(
        self, 
        session: AsyncSession, 
        user_create: UserCreate
    ) -> User:
        """创建用户"""
        user = User(**user_create.model_dump())
        session.add(user)
        await session.flush()
        return user
```

**生成的审计日志：**
```json
{
  "business_domain": "iam",
  "operation_type": "create",
  "resource_type": "user",
  "resource_id": "7ab4e404-f31d-48c7-b4c7-53a51a84d718",
  "resource_name": "guozengqiang",
  "permission_code": "iam:user:create",
  "before_data": null,
  "after_data": {
    "id": "7ab4e404-f31d-48c7-b4c7-53a51a84d718",
    "username": "guozengqiang",
    "nickname": "郭增强",
    "email": null,
    "mobile": null,
    "status": "0",
    "dept_id": null,
    "role_ids": []
  },
  "detail": {
    "text": "张三在2024-01-15 10:30:00对用户\"guozengqiang\"进行了创建操作",
    "template_key": "audit.user.create",
    "params": {
      "operator_name": "张三",
      "operated_at": "2024-01-15 10:30:00",
      "resource_name": "guozengqiang",
      "operation_type": "创建"
    }
  }
}
```

### 复杂场景（更新操作）

```python
# iam/services/user_service.py

from framework.audit.decorator import audit_log
from framework.audit.utils import get_model_before_data

class UserService:
    @audit_log(
        module="iam",
        resource="user",
        action="update",
        resource_id_getter=lambda args, kwargs: kwargs.get("user_id"),
        resource_name_getter=lambda result: result.username,
        before_data_getter=lambda args, kwargs: get_model_before_data(
            args, kwargs, 
            model_class=User,
            id_param="user_id"
        ),
    )
    async def update_user(
        self, 
        session: AsyncSession, 
        user_id: str, 
        user_update: UserUpdate
    ) -> User:
        """更新用户"""
        user = await session.get(User, user_id)
        
        for key, value in user_update.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        
        await session.flush()
        return user
```

### 工具函数

```python
# framework/audit/utils.py

async def get_model_before_data(
    args: tuple,
    kwargs: dict,
    model_class: type,
    id_param: str = "id",
) -> dict | None:
    """
    获取模型操作前的数据
    
    Args:
        args: 方法位置参数
        kwargs: 方法关键字参数
        model_class: 模型类
        id_param: ID 参数名
    
    Returns:
        模型数据字典，如果未找到返回 None
    """
    # 提取 session
    session = _extract_session(args, kwargs)
    if not session:
        return None
    
    # 提取 ID
    model_id = kwargs.get(id_param)
    if not model_id:
        return None
    
    # 查询模型
    model = await session.get(model_class, model_id)
    if not model:
        return None
    
    # 返回数据字典
    return model.to_dict() if hasattr(model, 'to_dict') else None
```

## 模型基类扩展

### to_dict() 方法

所有需要记录审计日志的模型必须实现 `to_dict()` 方法。

```python
# framework/database/base.py

class BaseModel:
    """模型基类"""
    
    def to_dict(self, exclude: list[str] | None = None) -> dict:
        """
        将模型转换为字典
        
        Args:
            exclude: 需要排除的字段列表
        
        Returns:
            模型数据字典
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            # 跳过排除字段
            if column.name in exclude:
                continue
            
            value = getattr(self, column.name)
            
            # 处理特殊类型
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, enum.Enum):
                value = value.value
            elif isinstance(value, UUID):
                value = str(value)
            
            result[column.name] = value
        
        return result
```

### 敏感字段处理

```python
# iam/models/user.py

class User(BaseModel):
    """用户模型"""
    
    # 敏感字段定义
    SENSITIVE_FIELDS = ["password", "password_hash", "token"]
    
    def to_dict(self, exclude: list[str] | None = None) -> dict:
        """转换为字典，自动排除敏感字段"""
        exclude = exclude or []
        exclude.extend(self.SENSITIVE_FIELDS)
        return super().to_dict(exclude=exclude)
```

## 权限编码获取

### 上下文存储

```python
# framework/common/context.py

from contextvars import ContextVar

# 当前权限编码
_current_permission_code: ContextVar[str | None] = ContextVar("permission_code", default=None)

def set_permission_code(code: str) -> None:
    """设置当前权限编码"""
    _current_permission_code.set(code)

def get_permission_code() -> str | None:
    """获取当前权限编码"""
    return _current_permission_code.get()
```

### 中间件集成

```python
# framework/middlewares/auth.py

async def permission_middleware(request: Request, call_next):
    """权限验证中间件"""
    
    # 验证权限
    permission_code = await verify_permission(request)
    
    if permission_code:
        # 设置权限编码到上下文
        set_permission_code(permission_code)
    
    response = await call_next(request)
    return response
```

## 数据来源映射

| 字段 | 数据来源 | 说明 |
|------|---------|------|
| `business_domain` | 装饰器参数 `module` | 模块名称，如 `iam`、`tenant` |
| `operation_type` | 装饰器参数 `action` | 对应权限 `action` 字段 |
| `resource_type` | 装饰器参数 `resource` | 对应权限 `resource` 字段 |
| `resource_id` | 装饰器参数 `resource_id_getter` | 资源 ID |
| `resource_name` | 装饰器参数 `resource_name_getter` | 资源名称 |
| `permission_code` | 请求上下文 | `{module}:{resource}:{action}` |
| `before_data` | 装饰器参数 `before_data_getter` | 完整模型数据 |
| `after_data` | 从返回值获取 | 完整模型数据 |
| `detail` | 自动构建 | 固定格式模板 |

## 数据库迁移

### 迁移策略

**无需处理** - 数据库中没有审计日志数据，直接执行迁移。

### 迁移步骤

1. 删除枚举类型字段（`business_domain`、`operation_type`、`resource_type`）
2. 添加字符串类型字段
3. 添加新字段（`permission_code`）
4. 重命名字段（`details` → `detail`）
5. 创建索引
6. 删除枚举类型定义

### 迁移文件示例

```python
# iam/migrations/versions/003_audit_log.py

def upgrade() -> None:
    # 1. 删除枚举类型字段
    op.drop_column("audit_log", "business_domain", schema="iam")
    op.drop_column("audit_log", "operation_type", schema="iam")
    op.drop_column("audit_log", "resource_type", schema="iam")
    
    # 2. 添加字符串类型字段
    op.add_column("audit_log", 
        sa.Column("business_domain", sa.String(64), nullable=False, comment="业务域"),
        schema="iam"
    )
    op.add_column("audit_log",
        sa.Column("operation_type", sa.String(64), nullable=False, comment="操作类型"),
        schema="iam"
    )
    op.add_column("audit_log",
        sa.Column("resource_type", sa.String(64), nullable=False, comment="资源类型"),
        schema="iam"
    )
    
    # 3. 添加新字段
    op.add_column("audit_log",
        sa.Column("permission_code", sa.String(128), nullable=True, comment="权限编码"),
        schema="iam"
    )
    
    # 4. 重命名字段
    op.alter_column("audit_log", "details", new_column_name="detail", schema="iam")
    
    # 5. 创建索引
    op.create_index("ix_audit_log_permission_code", "audit_log", ["permission_code"], schema="iam")
    
    # 6. 删除枚举类型
    op.execute("DROP TYPE IF EXISTS iam.auditlogbusinesstype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogoperationtype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogresourcetype")
```

## 实施范围

### 阶段一：基础设施

1. 修改 `AuditLog` 模型字段（枚举 → 字符串）
2. 创建 `framework/audit/` 模块
3. 实现装饰器和审计服务
4. 扩展 `BaseModel` 添加 `to_dict()` 方法
5. 添加权限编码上下文支持
6. 创建数据库迁移文件

### 阶段二：应用推广

7. 在 IAM 模块应用装饰器
   - `UserService.create_user()`
   - `UserService.update_user()`
   - `UserService.delete_user()`
   - `OrganizationService` 相关方法
   - `RoleService` 相关方法
8. 更新测试用例
9. 提供使用文档

## 设计决策

1. **字段类型**：使用字符串而非枚举，避免维护成本
2. **权限编码获取**：从请求上下文获取，无需手动拼接
3. **数据获取策略**：混合模式，简单场景自动处理，复杂场景手动处理
4. **detail 格式**：同时存储渲染文本和结构化数据，支持直接展示和国际化
5. **跨模块调用**：由被调用方记录，保持一致性
6. **事务管理**：审计日志与业务操作在同一事务中，保证一致性

## 验收标准

1. ✅ 所有枚举字段改为字符串类型
2. ✅ 装饰器能够自动记录审计日志
3. ✅ before_data/after_data 正确记录完整模型数据
4. ✅ detail 字段包含渲染文本和结构化数据
5. ✅ 权限编码正确关联
6. ✅ 敏感字段自动脱敏
7. ✅ 测试用例全部通过
