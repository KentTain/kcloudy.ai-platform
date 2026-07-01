# 审计日志自动化记录实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现审计日志自动化记录系统，支持声明式装饰器和事件混合模式

**架构：** 在 framework 层创建 audit 模块，提供装饰器和服务；在 IAM 模块应用装饰器记录用户、组织、角色等操作

**技术栈：** Python 3.12、FastAPI、SQLAlchemy 2.0、Pydantic

---

## 文件结构

**创建文件：**
- `server/python/src/framework/audit/__init__.py` - 导出公共接口
- `server/python/src/framework/audit/context.py` - AuditContext 审计上下文
- `server/python/src/framework/audit/service.py` - AuditService 审计服务
- `server/python/src/framework/audit/decorator.py` - audit_log 装饰器
- `server/python/src/framework/audit/templates.py` - 审计日志模板
- `server/python/src/framework/audit/utils.py` - 工具函数
- `server/python/tests/framework/unit/audit/test_context.py` - AuditContext 单元测试
- `server/python/tests/framework/unit/audit/test_service.py` - AuditService 单元测试
- `server/python/tests/framework/unit/audit/test_decorator.py` - 装饰器单元测试
- `server/python/tests/iam/integration/test_audit_log_decorator.py` - 装饰器集成测试

**修改文件：**
- `server/python/src/iam/models/audit_log.py` - 修改字段类型（枚举 → 字符串）
- `server/python/src/iam/models/enums.py` - 删除审计日志相关枚举
- `server/python/src/iam/schemas/audit_log.py` - 更新 Schema 字段类型
- `server/python/src/iam/services/audit_log_service.py` - 更新查询逻辑
- `server/python/src/framework/database/core/base.py` - 扩展 to_dict() 方法
- `server/python/src/framework/common/ctx.py` - 添加权限编码上下文支持
- `server/python/src/iam/services/user_service.py` - 应用装饰器
- `server/python/src/iam/migrations/versions/003_audit_log.py` - 完善迁移脚本

---

## 阶段一：基础设施

### 任务 1：扩展 Context 支持权限编码

**文件：**
- 修改：`server/python/src/framework/common/ctx.py:16-34`
- 测试：`server/python/tests/framework/unit/test_ctx.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/test_ctx.py`：

```python
"""测试上下文权限编码"""

import pytest
from framework.common.ctx import (
    get_context,
    set_permission_code,
    get_permission_code,
)


def test_set_and_get_permission_code():
    """测试设置和获取权限编码"""
    # 设置权限编码
    set_permission_code("iam:user:create")

    # 获取权限编码
    permission_code = get_permission_code()

    assert permission_code == "iam:user:create"


def test_get_permission_code_default_none():
    """测试默认权限编码为 None"""
    # 清空上下文
    from framework.common.ctx import clear_context
    clear_context()

    # 获取权限编码
    permission_code = get_permission_code()

    assert permission_code is None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/test_ctx.py -v`

预期：FAIL，报错 "cannot import name 'set_permission_code'"

- [ ] **步骤 3：实现 Context 扩展**

修改 `server/python/src/framework/common/ctx.py`：

在 `Context` 类中添加字段（第24行后）：

```python
@dataclass
class Context:
    """请求上下文"""

    # 用户信息
    user_id: str | None = None
    user_name: str | None = None
    session_id: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    # 租户信息
    tenant_id: str | None = None
    tenant_name: str | None = None
    tenant_code: str | None = None

    # 权限信息
    permission_code: str | None = None
    """当前操作的权限编码"""

    # 其他信息
    workspace_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
```

在 `copy()` 方法中添加字段复制（第50行后）：

```python
def copy(self) -> "Context":
    """创建上下文副本"""
    return Context(
        user_id=self.user_id,
        user_name=self.user_name,
        session_id=self.session_id,
        roles=list(self.roles),
        permissions=list(self.permissions),
        tenant_id=self.tenant_id,
        tenant_name=self.tenant_name,
        tenant_code=self.tenant_code,
        permission_code=self.permission_code,
        workspace_id=self.workspace_id,
        extra=deepcopy(self.extra),
    )
```

在文件末尾添加函数（第150行后）：

```python
def set_permission_code(code: str) -> None:
    """
    设置当前权限编码

    Args:
        code: 权限编码，如 "iam:user:create"
    """

    def modifier(ctx: Context) -> None:
        ctx.permission_code = code

    _update_context(modifier)


def get_permission_code() -> str | None:
    """获取当前权限编码"""
    return get_context().permission_code
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/test_ctx.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/common/ctx.py server/python/tests/framework/unit/test_ctx.py
git commit -m "feat(framework): 扩展 Context 支持权限编码存储"
```

---

### 任务 2：扩展 BaseModel to_dict() 方法

**文件：**
- 修改：`server/python/src/framework/database/core/base.py:40-45`
- 测试：`server/python/tests/framework/unit/database/test_base_model.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/database/test_base_model.py`：

```python
"""测试 BaseModel to_dict 方法"""

import enum
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.core.base import BaseModel


class StatusEnum(enum.Enum):
    """状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class TestModel(BaseModel):
    """测试模型"""
    __tablename__ = "test_model"

    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[StatusEnum] = mapped_column(default=StatusEnum.ACTIVE)


def test_to_dict_basic():
    """测试基本 to_dict 功能"""
    model = TestModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    result = model.to_dict()

    assert result["name"] == "test"
    assert result["status"] == "active"  # 枚举转为值


def test_to_dict_with_exclude():
    """测试 to_dict 排除字段"""
    model = TestModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    result = model.to_dict(exclude=["status"])

    assert "name" in result
    assert "status" not in result


def test_to_dict_datetime_conversion():
    """测试 datetime 类型转换"""
    now = datetime.now(timezone.utc)
    model = TestModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    model.created_at = now

    result = model.to_dict()

    assert isinstance(result["created_at"], str)  # ISO 格式字符串


def test_to_dict_uuid_conversion():
    """测试 UUID 类型转换"""
    uuid_str = str(uuid4())
    model = TestModel(id=uuid_str, name="test", status=StatusEnum.ACTIVE)

    result = model.to_dict()

    assert result["id"] == uuid_str
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/database/test_base_model.py -v`

预期：FAIL，报错 "unexpected keyword argument 'exclude'"

- [ ] **步骤 3：实现 to_dict 扩展**

修改 `server/python/src/framework/database/core/base.py`：

```python
"""
Base 模型类

提供统一的 SQLAlchemy Base 模型类。
"""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.uuid_primary_key import UUIDPrimaryKeyMixin


class Base(AsyncAttrs, DeclarativeBase):
    """
    基础模型类

    继承自 SQLAlchemy 的 DeclarativeBase 和 AsyncAttrs，提供：
    1. 异步属性访问支持
    2. 声明式模型定义
    """

    pass


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    基础数据实体（默认 public schema）

    所有数据模型的基类，提供：
    1. UUID 主键支持
    2. 时间戳字段
    3. 基础操作方法
    """

    __abstract__ = True

    def to_dict(self, exclude: list[str] | None = None) -> dict[str, Any]:
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

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/database/test_base_model.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/database/core/base.py server/python/tests/framework/unit/database/test_base_model.py
git commit -m "feat(framework): 扩展 BaseModel.to_dict() 支持 exclude 和类型转换"
```

---

### 任务 3：创建 AuditContext 审计上下文

**文件：**
- 创建：`server/python/src/framework/audit/context.py`
- 创建：`server/python/tests/framework/unit/audit/test_context.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/audit/test_context.py`：

```python
"""测试 AuditContext"""

import pytest
from framework.audit.context import AuditContext


def test_audit_context_creation():
    """测试创建审计上下文"""
    context = AuditContext(
        module="iam",
        resource="user",
        action="create",
        resource_id="user-123",
        resource_name="张三",
    )

    assert context.module == "iam"
    assert context.resource == "user"
    assert context.action == "create"
    assert context.resource_id == "user-123"
    assert context.resource_name == "张三"
    assert context.before_data is None
    assert context.after_data is None
    assert context.detail_extra is None


def test_audit_context_with_data():
    """测试带数据的审计上下文"""
    before_data = {"id": "user-123", "name": "张三"}
    after_data = {"id": "user-123", "name": "李四"}
    detail_extra = {"role": "admin"}

    context = AuditContext(
        module="iam",
        resource="user",
        action="update",
        resource_id="user-123",
        resource_name="李四",
        before_data=before_data,
        after_data=after_data,
        detail_extra=detail_extra,
    )

    assert context.before_data == before_data
    assert context.after_data == after_data
    assert context.detail_extra == detail_extra
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_context.py -v`

预期：FAIL，报错 "No module named 'framework.audit'"

- [ ] **步骤 3：创建 audit 模块目录结构**

创建目录和 `__init__.py`：

```bash
mkdir -p server/python/src/framework/audit
mkdir -p server/python/tests/framework/unit/audit
```

创建 `server/python/src/framework/audit/__init__.py`：

```python
"""
审计日志模块

提供审计日志自动化记录功能。
"""

from framework.audit.context import AuditContext
from framework.audit.decorator import audit_log
from framework.audit.service import AuditService

__all__ = [
    "AuditContext",
    "AuditService",
    "audit_log",
]
```

创建 `server/python/src/framework/audit/context.py`：

```python
"""
审计上下文

定义审计日志所需的数据结构。
"""

from dataclasses import dataclass


@dataclass
class AuditContext:
    """
    审计上下文，用于传递审计日志所需信息

    Attributes:
        module: 模块名称，如 iam, tenant, ai
        resource: 资源类型，如 user, role, organization
        action: 操作类型，如 create, update, delete
        resource_id: 资源 ID
        resource_name: 资源名称（用于展示）
        before_data: 操作前数据
        after_data: 操作后数据
        detail_extra: 额外上下文信息
    """

    # 基础信息（必填）
    module: str
    resource: str
    action: str

    # 资源信息（必填）
    resource_id: str | None = None
    resource_name: str = ""

    # 数据快照（可选）
    before_data: dict | None = None
    after_data: dict | None = None

    # 详情信息（可选）
    detail_extra: dict | None = None
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_context.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/audit/ server/python/tests/framework/unit/audit/
git commit -m "feat(framework): 创建 AuditContext 审计上下文"
```

---

### 任务 4：创建审计日志模板

**文件：**
- 创建：`server/python/src/framework/audit/templates.py`
- 测试：`server/python/tests/framework/unit/audit/test_templates.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/audit/test_templates.py`：

```python
"""测试审计日志模板"""

import pytest
from framework.audit.templates import AuditTemplateBuilder


def test_build_template_key():
    """测试构建模板 Key"""
    builder = AuditTemplateBuilder()

    template_key = builder.build_template_key(
        module="iam",
        resource="user",
        action="create"
    )

    assert template_key == "audit.iam.user.create"


def test_build_detail_full():
    """测试构建完整 detail"""
    builder = AuditTemplateBuilder()

    detail = builder.build_detail(
        module="iam",
        resource="user",
        action="create",
        operator_name="张三",
        operated_at="2026-07-01 10:30:00",
        resource_name="李四",
        extra={"role": "管理员"}
    )

    assert detail["text"] == "张三在2026-07-01 10:30:00对用户\"李四\"进行了创建操作"
    assert detail["template_key"] == "audit.iam.user.create"
    assert detail["params"]["operator_name"] == "张三"
    assert detail["params"]["resource_name"] == "李四"
    assert detail["params"]["operation_type"] == "创建"
    assert detail["extra"]["role"] == "管理员"


def test_build_detail_without_extra():
    """测试构建不带 extra 的 detail"""
    builder = AuditTemplateBuilder()

    detail = builder.build_detail(
        module="iam",
        resource="user",
        action="update",
        operator_name="张三",
        operated_at="2026-07-01 10:30:00",
        resource_name="李四"
    )

    assert detail["text"] == "张三在2026-07-01 10:30:00对用户\"李四\"进行了更新操作"
    assert "extra" not in detail or detail["extra"] is None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_templates.py -v`

预期：FAIL，报错 "cannot import name 'AuditTemplateBuilder'"

- [ ] **步骤 3：实现审计日志模板**

创建 `server/python/src/framework/audit/templates.py`：

```python
"""
审计日志模板

提供审计日志 detail 字段的模板构建功能。
"""

from typing import Any


class AuditTemplateBuilder:
    """审计日志模板构建器"""

    # 操作类型中文映射
    ACTION_LABELS = {
        "create": "创建",
        "update": "更新",
        "delete": "删除",
        "enable": "启用",
        "disable": "禁用",
        "assign": "分配",
        "remove": "移除",
    }

    # 资源类型中文映射
    RESOURCE_LABELS = {
        "user": "用户",
        "role": "角色",
        "organization": "组织",
        "permission": "权限",
        "menu": "菜单",
    }

    def build_template_key(self, module: str, resource: str, action: str) -> str:
        """
        构建模板 Key

        Args:
            module: 模块名称
            resource: 资源类型
            action: 操作类型

        Returns:
            模板 Key，格式：audit.{module}.{resource}.{action}
        """
        return f"audit.{module}.{resource}.{action}"

    def build_detail(
        self,
        module: str,
        resource: str,
        action: str,
        operator_name: str,
        operated_at: str,
        resource_name: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        构建 detail 字段

        Args:
            module: 模块名称
            resource: 资源类型
            action: 操作类型
            operator_name: 操作人名称
            operated_at: 操作时间
            resource_name: 资源名称
            extra: 额外信息

        Returns:
            detail 字典
        """
        # 获取操作类型标签
        action_label = self.ACTION_LABELS.get(action, action)

        # 获取资源类型标签
        resource_label = self.RESOURCE_LABELS.get(resource, resource)

        # 构建文本
        text = f'{operator_name}在{operated_at}对{resource_label}"{resource_name}"进行了{action_label}操作'

        # 构建模板 Key
        template_key = self.build_template_key(module, resource, action)

        # 构建参数
        params = {
            "operator_name": operator_name,
            "operated_at": operated_at,
            "resource_name": resource_name,
            "operation_type": action_label,
        }

        # 构建 detail
        detail = {
            "text": text,
            "template_key": template_key,
            "params": params,
        }

        # 添加额外信息
        if extra:
            detail["extra"] = extra

        return detail
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_templates.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/audit/templates.py server/python/tests/framework/unit/audit/test_templates.py
git commit -m "feat(framework): 创建审计日志模板构建器"
```

---

### 任务 5：创建 AuditService 审计服务

**文件：**
- 创建：`server/python/src/framework/audit/service.py`
- 创建：`server/python/src/framework/audit/utils.py`
- 测试：`server/python/tests/framework/unit/audit/test_service.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/audit/test_service.py`：

```python
"""测试 AuditService"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.context import AuditContext
from framework.audit.service import AuditService


@pytest.mark.asyncio
async def test_audit_service_record():
    """测试审计服务记录日志"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # Mock context
    context = AuditContext(
        module="iam",
        resource="user",
        action="create",
        resource_id="user-123",
        resource_name="张三",
        after_data={"id": "user-123", "name": "张三"},
    )

    # Mock 上下文函数
    with patch("framework.audit.service.get_user_id") as mock_get_user_id, \
         patch("framework.audit.service.get_user_name") as mock_get_user_name, \
         patch("framework.audit.service.get_tenant_id") as mock_get_tenant_id, \
         patch("framework.audit.service.get_permission_code") as mock_get_permission_code:

        mock_get_user_id.return_value = "admin-123"
        mock_get_user_name.return_value = "管理员"
        mock_get_tenant_id.return_value = "tenant-123"
        mock_get_permission_code.return_value = "iam:user:create"

        # 执行
        service = AuditService()
        await service.record(session, context)

        # 验证
        session.add.assert_called_once()
        audit_log = session.add.call_args[0][0]

        assert audit_log.tenant_id == "tenant-123"
        assert audit_log.business_domain == "iam"
        assert audit_log.operation_type == "create"
        assert audit_log.resource_type == "user"
        assert audit_log.resource_id == "user-123"
        assert audit_log.resource_name == "张三"
        assert audit_log.permission_code == "iam:user:create"
        assert audit_log.operator_by == "admin-123"
        assert audit_log.operator_name == "管理员"
        assert audit_log.after_data == {"id": "user-123", "name": "张三"}
        assert audit_log.detail["text"] is not None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_service.py -v`

预期：FAIL，报错 "cannot import name 'AuditService'"

- [ ] **步骤 3：创建工具函数**

创建 `server/python/src/framework/audit/utils.py`：

```python
"""
审计日志工具函数

提供审计日志相关的工具函数。
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


def extract_session(args: tuple, kwargs: dict) -> AsyncSession | None:
    """
    从方法参数中提取数据库 Session

    Args:
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        AsyncSession 或 None
    """
    # 从 kwargs 中查找
    if "session" in kwargs:
        return kwargs["session"]

    # 从 args 中查找（通常是第一个参数）
    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg

    return None


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
    session = extract_session(args, kwargs)
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
    return model.to_dict() if hasattr(model, "to_dict") else None
```

- [ ] **步骤 4：实现 AuditService**

创建 `server/python/src/framework/audit/service.py`：

```python
"""
审计日志服务

提供审计日志记录功能。
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.context import AuditContext
from framework.audit.templates import AuditTemplateBuilder
from framework.common.ctx import (
    get_permission_code,
    get_tenant_id,
    get_user_id,
)
from iam.models import AuditLog


class AuditService:
    """审计日志服务"""

    def __init__(self):
        """初始化审计服务"""
        self.template_builder = AuditTemplateBuilder()

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
        user_name = self._get_user_name()
        tenant_id = get_tenant_id()

        # 2. 获取权限编码（从上下文获取）
        permission_code = get_permission_code()

        # 3. 构建 detail 字段
        operated_at = datetime.now(timezone.utc)
        operated_at_str = operated_at.strftime("%Y-%m-%d %H:%M:%S")

        detail = self.template_builder.build_detail(
            module=context.module,
            resource=context.resource,
            action=context.action,
            operator_name=user_name or "",
            operated_at=operated_at_str,
            resource_name=context.resource_name,
            extra=context.detail_extra,
        )

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
            operator_name=user_name or "",
            operated_at=operated_at,
            before_data=context.before_data,
            after_data=context.after_data,
            detail=detail,
        )

        session.add(audit_log)
        # 不 commit，由调用方管理事务

    def _get_user_name(self) -> str | None:
        """获取当前用户名称"""
        from framework.common.ctx import get_context

        ctx = get_context()
        return ctx.user_name


# 服务单例
audit_service = AuditService()
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_service.py -v`

预期：PASS

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/framework/audit/service.py server/python/src/framework/audit/utils.py server/python/tests/framework/unit/audit/test_service.py
git commit -m "feat(framework): 创建 AuditService 审计服务"
```

---

### 任务 6：创建 audit_log 装饰器

**文件：**
- 创建：`server/python/src/framework/audit/decorator.py`
- 测试：`server/python/tests/framework/unit/audit/test_decorator.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/audit/test_decorator.py`：

```python
"""测试 audit_log 装饰器"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.decorator import audit_log


@pytest.mark.asyncio
async def test_audit_log_decorator_simple():
    """测试简单场景的装饰器"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # 定义测试函数
    @audit_log(
        module="iam",
        resource="user",
        action="create",
        resource_id_getter=lambda result: result["id"],
        resource_name_getter=lambda result: result["name"],
    )
    async def create_user(session, user_data):
        return {"id": "user-123", "name": "张三"}

    # Mock 上下文和 AuditService
    with patch("framework.audit.decorator.audit_service") as mock_service:
        mock_service.record = AsyncMock()

        # 执行
        result = await create_user(session, {"name": "张三"})

        # 验证结果
        assert result == {"id": "user-123", "name": "张三"}

        # 验证审计日志被调用
        mock_service.record.assert_called_once()
        call_args = mock_service.record.call_args

        assert call_args[0][0] == session  # session
        context = call_args[0][1]  # context

        assert context.module == "iam"
        assert context.resource == "user"
        assert context.action == "create"
        assert context.resource_id == "user-123"
        assert context.resource_name == "张三"
        assert context.after_data == {"id": "user-123", "name": "张三"}


@pytest.mark.asyncio
async def test_audit_log_decorator_with_before_data():
    """测试带 before_data 的装饰器"""
    # Mock session
    session = AsyncMock(spec=AsyncSession)

    # 定义 before_data_getter
    async def get_before_data(args, kwargs):
        return {"id": "user-123", "name": "旧名字"}

    # 定义测试函数
    @audit_log(
        module="iam",
        resource="user",
        action="update",
        resource_id_getter=lambda result: result["id"],
        resource_name_getter=lambda result: result["name"],
        before_data_getter=get_before_data,
    )
    async def update_user(session, user_id, user_data):
        return {"id": user_id, "name": "新名字"}

    # Mock 上下文和 AuditService
    with patch("framework.audit.decorator.audit_service") as mock_service:
        mock_service.record = AsyncMock()

        # 执行
        result = await update_user(session, "user-123", {"name": "新名字"})

        # 验证审计日志被调用
        mock_service.record.assert_called_once()
        call_args = mock_service.record.call_args
        context = call_args[0][1]

        assert context.before_data == {"id": "user-123", "name": "旧名字"}
        assert context.after_data == {"id": "user-123", "name": "新名字"}
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_decorator.py -v`

预期：FAIL，报错 "cannot import name 'audit_log'"

- [ ] **步骤 3：实现装饰器**

创建 `server/python/src/framework/audit/decorator.py`：

```python
"""
审计日志装饰器

提供声明式的审计日志记录功能。
"""

from functools import wraps
from typing import Any, Callable

from framework.audit.context import AuditContext
from framework.audit.service import audit_service
from framework.audit.utils import extract_session


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
                import asyncio

                result = before_data_getter(args, kwargs)
                if asyncio.iscoroutine(result):
                    before_data = await result
                else:
                    before_data = result

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

            # 5. 设置 before_data
            context.before_data = before_data

            # 6. 获取 after_data（从返回值）
            if result and hasattr(result, "to_dict"):
                context.after_data = result.to_dict()
            elif isinstance(result, dict):
                context.after_data = result

            # 7. 记录审计日志
            session = extract_session(args, kwargs)
            if session:
                await audit_service.record(session, context)

            return result

        return wrapper

    return decorator
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/test_decorator.py -v`

预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/audit/decorator.py server/python/tests/framework/unit/audit/test_decorator.py
git commit -m "feat(framework): 创建 audit_log 装饰器"
```

---

## 阶段二：数据模型调整

### 任务 7：修改 AuditLog 模型字段

**文件：**
- 修改：`server/python/src/iam/models/audit_log.py`
- 修改：`server/python/src/iam/models/enums.py`
- 修改：`server/python/src/iam/schemas/audit_log.py`
- 修改：`server/python/src/iam/services/audit_log_service.py`

- [ ] **步骤 1：修改 AuditLog 模型**

修改 `server/python/src/iam/models/audit_log.py`：

```python
"""
审计日志模型
"""

from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.datetime import UtcDateTime
from iam.models import BaseModel


class AuditLog(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """
    审计日志表
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_permission_code", "permission_code"),
        {"comment": "审计日志表"},
    )

    business_domain: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="业务域（模块名称）",
    )
    business_domain_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="业务域ID",
    )
    permission_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="权限编码",
    )
    operator_by: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="操作用户ID"
    )
    operator_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="操作用户名"
    )
    operated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, nullable=False, index=True, comment="操作时间"
    )
    operation_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="操作类型",
    )
    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="资源类型",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="主操作对象ID",
    )
    resource_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="主操作对象名称"
    )
    before_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作前数据"
    )
    after_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作后数据"
    )
    detail: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="操作详情"
    )
```

- [ ] **步骤 2：删除审计日志相关枚举**

修改 `server/python/src/iam/models/enums.py`，删除以下类：
- `AuditLogBusinessType`（第94-113行）
- `AuditLogOperationType`（第115-272行）
- `AuditLogResourceType`（第275-320行左右）

- [ ] **步骤 3：更新 Schema**

修改 `server/python/src/iam/schemas/audit_log.py`：

```python
"""审计日志 Schema"""

from datetime import datetime

from framework.schemas import BaseModel


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: str
    tenant_id: str
    business_domain: str
    business_domain_id: str | None = None
    permission_code: str | None = None
    operator_by: str
    operator_name: str
    operated_at: datetime
    operation_type: str
    resource_type: str
    resource_id: str | None = None
    resource_name: str
    before_data: dict | None = None
    after_data: dict | None = None
    detail: dict | None = None
    created_at: datetime


class AuditOptionSchema(BaseModel):
    """审计选项 Schema"""

    value: str
    label: str


class AuditLogOptionsResponse(BaseModel):
    """审计日志选项响应"""

    business_domains: list[AuditOptionSchema]
    actions: list[AuditOptionSchema]
    resource_types: list[AuditOptionSchema]
```

- [ ] **步骤 4：更新 AuditLogService**

修改 `server/python/src/iam/services/audit_log_service.py`，删除枚举引用：

```python
"""
审计日志服务

提供审计日志查询功能。
"""

from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.tenant.context import get_tenant_id
from iam.models import AuditLog
from iam.schemas.audit_log import (
    AuditLogOptionsResponse,
    AuditLogResponse,
    AuditOptionSchema,
)

_logger = logger.bind(name=__name__)


class AuditLogService:
    """审计日志服务"""

    @staticmethod
    async def list_audit_logs(
        session: AsyncSession,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        business_domain: str | None = None,
        operation_type: str | None = None,
        resource_type: str | None = None,
        operator_by: str | None = None,
        time_range: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """
        获取审计日志列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            page: 页码
            page_size: 每页数量
            business_domain: 业务域
            operation_type: 操作类型
            resource_type: 资源类型
            operator_by: 操作人 ID
            time_range: 时间范围（24h/7d/30d/all）
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            tuple[list[AuditLog], int]
        """
        # 构建查询条件
        conditions = []

        # 租户隔离
        if tenant_id:
            conditions.append(AuditLog.tenant_id == tenant_id)

        # 业务域筛选
        if business_domain:
            conditions.append(AuditLog.business_domain == business_domain)

        # 操作类型筛选
        if operation_type:
            conditions.append(AuditLog.operation_type == operation_type)

        # 资源类型筛选
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)

        # 操作人筛选
        if operator_by:
            conditions.append(AuditLog.operator_by == operator_by)

        # 时间范围筛选
        if time_range and time_range != "all":
            now = datetime.now(timezone.utc)
            if time_range == "24h":
                start_time = now - timedelta(hours=24)
            elif time_range == "7d":
                start_time = now - timedelta(days=7)
            elif time_range == "30d":
                start_time = now - timedelta(days=30)

        if start_time:
            conditions.append(AuditLog.operated_at >= start_time)
        if end_time:
            conditions.append(AuditLog.operated_at <= end_time)

        # 查询总数
        count_stmt = select(func.count(AuditLog.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = select(AuditLog)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(AuditLog.operated_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        logs = list(result.scalars().all())

        return logs, total

    @staticmethod
    async def get_audit_options(session: AsyncSession) -> AuditLogOptionsResponse:
        """
        获取审计日志选项

        返回业务域、操作类型、资源类型的可选项列表。
        根据当前租户的实际数据动态生成。

        Args:
            session: 数据库会话

        Returns:
            AuditLogOptionsResponse
        """
        tenant_id = get_tenant_id()

        # 查询该租户下实际存在的业务域
        business_domain_stmt = (
            select(AuditLog.business_domain)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        business_domain_result = await session.execute(business_domain_stmt)
        business_domains = [row[0] for row in business_domain_result.all()]

        # 查询该租户下实际存在的操作类型
        operation_type_stmt = (
            select(AuditLog.operation_type)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        operation_type_result = await session.execute(operation_type_stmt)
        operation_types = [row[0] for row in operation_type_result.all()]

        # 查询该租户下实际存在的资源类型
        resource_type_stmt = (
            select(AuditLog.resource_type)
            .where(AuditLog.tenant_id == tenant_id)
            .distinct()
        )
        resource_type_result = await session.execute(resource_type_stmt)
        resource_types = [row[0] for row in resource_type_result.all()]

        # 构建选项响应
        business_domain_options = [
            AuditOptionSchema(value=domain, label=domain)
            for domain in business_domains
        ]

        action_options = [
            AuditOptionSchema(value=action, label=action)
            for action in operation_types
        ]

        resource_type_options = [
            AuditOptionSchema(value=resource, label=resource)
            for resource in resource_types
        ]

        return AuditLogOptionsResponse(
            business_domains=business_domain_options,
            actions=action_options,
            resource_types=resource_type_options,
        )


# 服务单例
audit_log_service = AuditLogService()
```

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/models/audit_log.py \
        server/python/src/iam/models/enums.py \
        server/python/src/iam/schemas/audit_log.py \
        server/python/src/iam/services/audit_log_service.py
git commit -m "feat(iam): 修改 AuditLog 模型字段类型为字符串"
```

---

### 任务 8：完善数据库迁移文件

**文件：**
- 修改：`server/python/src/iam/migrations/versions/003_audit_log.py`

- [ ] **步骤 1：完善迁移脚本**

修改 `server/python/src/iam/migrations/versions/003_audit_log.py`：

```python
"""审计日志字段类型调整

Revision ID: 003_audit_log
Revises: 002_initial
Create Date: 2026-07-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_audit_log"
down_revision = "002_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库"""

    # 1. 删除旧字段（枚举类型）
    op.drop_column("audit_log", "business_domain", schema="iam")
    op.drop_column("audit_log", "operation_type", schema="iam")
    op.drop_column("audit_log", "resource_type", schema="iam")

    # 2. 添加新字段（字符串类型）
    op.add_column(
        "audit_log",
        sa.Column(
            "business_domain",
            sa.String(64),
            nullable=False,
            comment="业务域（模块名称）",
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "operation_type",
            sa.String(64),
            nullable=False,
            comment="操作类型",
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "resource_type",
            sa.String(64),
            nullable=False,
            comment="资源类型",
        ),
        schema="iam",
    )

    # 3. 添加新字段
    op.add_column(
        "audit_log",
        sa.Column(
            "permission_code",
            sa.String(128),
            nullable=True,
            comment="权限编码",
        ),
        schema="iam",
    )

    # 4. 重命名字段
    op.alter_column("audit_log", "details", new_column_name="detail", schema="iam")

    # 5. 创建索引
    op.create_index(
        "ix_audit_log_permission_code",
        "audit_log",
        ["permission_code"],
        schema="iam",
    )

    # 6. 删除枚举类型
    op.execute("DROP TYPE IF EXISTS iam.auditlogbusinesstype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogoperationtype")
    op.execute("DROP TYPE IF EXISTS iam.auditlogresourcetype")


def downgrade() -> None:
    """回滚数据库"""

    # 1. 删除索引
    op.drop_index("ix_audit_log_permission_code", table_name="audit_log", schema="iam")

    # 2. 删除新字段
    op.drop_column("audit_log", "permission_code", schema="iam")

    # 3. 重命名字段回退
    op.alter_column("audit_log", "detail", new_column_name="details", schema="iam")

    # 4. 删除字符串字段
    op.drop_column("audit_log", "business_domain", schema="iam")
    op.drop_column("audit_log", "operation_type", schema="iam")
    op.drop_column("audit_log", "resource_type", schema="iam")

    # 5. 创建枚举类型
    op.execute(
        "CREATE TYPE iam.auditlogbusinesstype AS ENUM ('library', 'knowledge_base', 'tag', 'role', 'system_role', 'user', 'dept', 'platform_setting')"
    )
    op.execute(
        "CREATE TYPE iam.auditlogoperationtype AS ENUM ('library.library_create', 'user.user_create')"
    )
    op.execute(
        "CREATE TYPE iam.auditlogresourcetype AS ENUM ('user', 'dept', 'role', 'system_role', 'tag', 'library')"
    )

    # 6. 添加枚举字段
    op.add_column(
        "audit_log",
        sa.Column(
            "business_domain",
            sa.Enum(
                "library",
                "knowledge_base",
                "tag",
                "role",
                "system_role",
                "user",
                "dept",
                "platform_setting",
                name="auditlogbusinesstype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "operation_type",
            sa.Enum(
                "library.library_create",
                "user.user_create",
                name="auditlogoperationtype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
    op.add_column(
        "audit_log",
        sa.Column(
            "resource_type",
            sa.Enum(
                "user",
                "dept",
                "role",
                "system_role",
                "tag",
                "library",
                name="auditlogresourcetype",
                schema="iam",
            ),
            nullable=False,
        ),
        schema="iam",
    )
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/migrations/versions/003_audit_log.py
git commit -m "feat(iam): 完善审计日志数据库迁移脚本"
```

---

## 阶段三：应用推广

### 任务 9：在 UserService 应用装饰器

**文件：**
- 修改：`server/python/src/iam/services/user_service.py`
- 测试：`server/python/tests/iam/integration/test_audit_log_decorator.py`

- [ ] **步骤 1：添加审计日志装饰器到 UserService**

修改 `server/python/src/iam/services/user_service.py`：

在文件开头添加导入：

```python
from framework.audit.decorator import audit_log
from framework.audit.utils import get_model_before_data
```

在 `create_user` 方法上添加装饰器：

```python
@audit_log(
    module="iam",
    resource="user",
    action="create",
    resource_id_getter=lambda result: result.id,
    resource_name_getter=lambda result: result.username,
)
async def create_user(
    self, session: AsyncSession, user_create: UserCreate
) -> User:
    """创建用户"""
    # ... 原有实现
```

在 `update_user` 方法上添加装饰器：

```python
@audit_log(
    module="iam",
    resource="user",
    action="update",
    resource_id_getter=lambda args, kwargs: kwargs.get("user_id"),
    resource_name_getter=lambda result: result.username,
    before_data_getter=lambda args, kwargs: get_model_before_data(
        args, kwargs, model_class=User, id_param="user_id"
    ),
)
async def update_user(
    self, session: AsyncSession, user_id: str, user_update: UserUpdate
) -> User:
    """更新用户"""
    # ... 原有实现
```

在 `delete_user` 方法上添加装饰器：

```python
@audit_log(
    module="iam",
    resource="user",
    action="delete",
    resource_id_getter=lambda args, kwargs: kwargs.get("user_id"),
    resource_name_getter=lambda result: result.username,
    before_data_getter=lambda args, kwargs: get_model_before_data(
        args, kwargs, model_class=User, id_param="user_id"
    ),
)
async def delete_user(self, session: AsyncSession, user_id: str) -> None:
    """删除用户"""
    # ... 原有实现
```

- [ ] **步骤 2：编写集成测试**

创建测试文件 `server/python/tests/iam/integration/test_audit_log_decorator.py`：

```python
"""测试审计日志装饰器集成"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework.audit.decorator import audit_log
from iam.models import AuditLog


@pytest.mark.asyncio
async def test_create_user_audit_log(
    session: AsyncSession,
    test_tenant_id: str,
):
    """测试创建用户记录审计日志"""
    # 模拟创建用户
    from iam.services.user_service import user_service
    from iam.schemas.user import UserCreate

    user_create = UserCreate(
        username="testuser",
        password="password123",
        nickname="测试用户",
    )

    # 设置上下文
    from framework.common.ctx import set_user

    set_user(
        user_id="admin-123",
        user_name="管理员",
        tenant_id=test_tenant_id,
    )

    # 执行创建
    user = await user_service.create_user(session, user_create)
    await session.commit()

    # 查询审计日志
    from sqlalchemy import select

    stmt = select(AuditLog).where(AuditLog.resource_id == user.id)
    result = await session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None
    assert audit_log.business_domain == "iam"
    assert audit_log.operation_type == "create"
    assert audit_log.resource_type == "user"
    assert audit_log.resource_name == "testuser"
    assert audit_log.after_data is not None
    assert audit_log.after_data["username"] == "testuser"
```

- [ ] **步骤 3：运行测试验证**

运行：`cd server/python && uv run pytest tests/iam/integration/test_audit_log_decorator.py -v`

预期：PASS

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/iam/services/user_service.py server/python/tests/iam/integration/test_audit_log_decorator.py
git commit -m "feat(iam): 在 UserService 应用审计日志装饰器"
```

---

### 任务 10：在 OrganizationService 和 RoleService 应用装饰器

**文件：**
- 修改：`server/python/src/iam/services/organization_service.py`
- 修改：`server/python/src/iam/services/role_service.py`

- [ ] **步骤 1：在 OrganizationService 应用装饰器**

修改 `server/python/src/iam/services/organization_service.py`，添加装饰器到以下方法：
- `create_organization` - 创建组织
- `update_organization` - 更新组织
- `delete_organization` - 删除组织

- [ ] **步骤 2：在 RoleService 应用装饰器**

修改 `server/python/src/iam/services/role_service.py`，添加装饰器到以下方法：
- `create_role` - 创建角色
- `update_role` - 更新角色
- `delete_role` - 删除角色

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/iam/services/organization_service.py \
        server/python/src/iam/services/role_service.py
git commit -m "feat(iam): 在 OrganizationService 和 RoleService 应用审计日志装饰器"
```

---

## 验收测试

### 任务 11：运行完整测试套件

- [ ] **步骤 1：运行所有单元测试**

运行：`cd server/python && uv run pytest tests/framework/unit/audit/ -v`

预期：所有测试通过

- [ ] **步骤 2：运行所有集成测试**

运行：`cd server/python && uv run pytest tests/iam/integration/test_audit_log_decorator.py -v`

预期：所有测试通过

- [ ] **步骤 3：运行完整测试套件**

运行：`cd server/python && uv run pytest -v`

预期：所有测试通过

- [ ] **步骤 4：验证数据库迁移**

运行：`cd server/python && uv run python manage.py db migrate --module iam`

预期：迁移成功

---

## 完成标志

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 数据库迁移成功
- [ ] 代码已提交到 git
- [ ] 功能符合设计文档要求
