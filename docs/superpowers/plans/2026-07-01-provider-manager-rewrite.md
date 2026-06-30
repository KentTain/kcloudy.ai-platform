# ProviderManager 完全重写实现计划

> **规格文档：** [2026-07-01-provider-manager-rewrite-design.md](../specs/2026-07-01-provider-manager-rewrite-design.md)
>
> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 完全重写 ProviderManager，移除所有废弃代码和 TODO 注释，新增 plugin_default_models 表支持默认模型配置。

**架构：** 新增 PluginDefaultModel 表管理默认模型配置，ProviderManager 简化为从插件 manifest 获取配置并注入凭证，DefaultModelService 基于新表实现。

**技术栈：** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `src/ai/models/plugin_default_model.py` | 默认模型数据模型 |
| `src/ai/schemas/plugin_default_model.py` | 默认模型 Schema（DTO） |
| `src/ai/services/plugin_default_model_service.py` | 默认模型服务 |
| `src/ai/migrations/versions/003_add_plugin_default_models.py` | 数据库迁移 |
| `tests/ai/unit/models/test_plugin_default_model.py` | 模型单元测试 |
| `tests/ai/unit/schemas/test_plugin_default_model.py` | Schema 单元测试 |
| `tests/ai/unit/services/test_plugin_default_model_service.py` | 服务单元测试 |

### 修改文件

| 文件 | 职责 |
|------|------|
| `src/ai/models/__init__.py` | 导出新模型 |
| `src/ai/components/model/internal/provider_manager.py` | 重写：移除废弃方法、简化流程 |
| `src/ai/components/model/internal/provider_configuration.py` | 重构：移除凭证管理方法 |
| `src/ai/components/model/services/management_service.py` | 重构：DefaultModelService |
| `tests/ai/unit/components/model/test_provider_manager.py` | 重写测试 |
| `src/ai/components/model/MIGRATION.md` | 更新迁移文档 |

---

## 任务 1：创建 PluginDefaultModel 数据模型

**文件：**
- 创建：`server/python/src/ai/models/plugin_default_model.py`
- 测试：`server/python/tests/ai/unit/models/test_plugin_default_model.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/models/test_plugin_default_model.py`：

```python
"""PluginDefaultModel 模型测试"""

import pytest

from ai.models.plugin_default_model import PluginDefaultModel


class TestPluginDefaultModel:
    """PluginDefaultModel 测试类"""

    def test_model_class_exists(self):
        """测试模型类存在"""
        assert hasattr(PluginDefaultModel, "__tablename__")
        assert PluginDefaultModel.__tablename__ == "plugin_default_models"

    def test_model_has_required_fields(self):
        """测试模型包含必需字段"""
        assert hasattr(PluginDefaultModel, "model_type")
        assert hasattr(PluginDefaultModel, "plugin_id")
        assert hasattr(PluginDefaultModel, "model_name")
        assert hasattr(PluginDefaultModel, "credential_id")
        assert hasattr(PluginDefaultModel, "custom_base_url")
        assert hasattr(PluginDefaultModel, "custom_model_name")
        assert hasattr(PluginDefaultModel, "is_valid")

    def test_model_inherits_base_model(self):
        """测试模型继承 BaseModel"""
        from framework.database import BaseModel
        assert issubclass(PluginDefaultModel, BaseModel)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/models/test_plugin_default_model.py -v`
预期：FAIL，报错 `ImportError: cannot import name 'PluginDefaultModel'`

- [ ] **步骤 3：创建 PluginDefaultModel 模型**

创建 `server/python/src/ai/models/plugin_default_model.py`：

```python
"""插件默认模型配置"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import UniqueConstraint

from framework.database import BaseModel
from framework.database.mixins import ActiveRecordMixin, AuditMixin, TenantMixin


class PluginDefaultModel(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件默认模型配置"""

    __tablename__ = "plugin_default_models"
    __table_args__ = (
        UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
    )

    model_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="模型类型：llm, text-embedding, rerank 等",
    )

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID",
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="标准模型名称",
    )

    credential_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="关联的凭证ID",
    )

    custom_base_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="自定义 API 端点",
    )

    custom_model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="自定义模型名称",
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效",
    )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/models/test_plugin_default_model.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/models/plugin_default_model.py server/python/tests/ai/unit/models/test_plugin_default_model.py
git commit -m "feat(ai): 新增 PluginDefaultModel 数据模型"
```

---

## 任务 2：创建 PluginDefaultModel Schema

**文件：**
- 创建：`server/python/src/ai/schemas/plugin_default_model.py`
- 测试：`server/python/tests/ai/unit/schemas/test_plugin_default_model.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/schemas/test_plugin_default_model.py`：

```python
"""PluginDefaultModel Schema 测试"""

import pytest

from ai.schemas.plugin_default_model import (
    PluginDefaultModelCreate,
    PluginDefaultModelResponse,
)


class TestPluginDefaultModelSchemas:
    """Schema 测试类"""

    def test_create_schema_standard_model(self):
        """测试创建 Schema（标准模型）"""
        schema = PluginDefaultModelCreate(
            model_type="llm",
            plugin_id="alon/tongyi",
            model_name="qwen-plus",
        )
        assert schema.model_type == "llm"
        assert schema.plugin_id == "alon/tongyi"
        assert schema.model_name == "qwen-plus"

    def test_create_schema_custom_model(self):
        """测试创建 Schema（自定义模型）"""
        schema = PluginDefaultModelCreate(
            model_type="llm",
            plugin_id="openai-api-compatible",
            credential_id="cred-123",
            custom_base_url="https://api.example.com/v1",
            custom_model_name="my-model",
        )
        assert schema.credential_id == "cred-123"
        assert schema.custom_model_name == "my-model"

    def test_response_schema(self):
        """测试响应 Schema"""
        schema = PluginDefaultModelResponse(
            id="test-id",
            tenant_id="tenant-001",
            model_type="llm",
            plugin_id="alon/tongyi",
            model_name="qwen-plus",
            is_valid=True,
        )
        assert schema.id == "test-id"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/schemas/test_plugin_default_model.py -v`
预期：FAIL

- [ ] **步骤 3：创建 Schema 文件**

创建 `server/python/src/ai/schemas/plugin_default_model.py`：

```python
"""插件默认模型配置 Schema"""

from __future__ import annotations

from framework.schemas import BaseModel


class PluginDefaultModelCreate(BaseModel):
    """创建默认模型请求"""

    model_type: str
    plugin_id: str
    model_name: str | None = None
    credential_id: str | None = None
    custom_base_url: str | None = None
    custom_model_name: str | None = None


class PluginDefaultModelResponse(BaseModel):
    """默认模型响应"""

    id: str
    tenant_id: str
    model_type: str
    plugin_id: str
    model_name: str | None = None
    credential_id: str | None = None
    custom_base_url: str | None = None
    custom_model_name: str | None = None
    is_valid: bool
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/schemas/test_plugin_default_model.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/schemas/plugin_default_model.py server/python/tests/ai/unit/schemas/test_plugin_default_model.py
git commit -m "feat(ai): 新增 PluginDefaultModel Schema"
```

---

## 任务 3：创建 PluginDefaultModelService 服务

**文件：**
- 创建：`server/python/src/ai/services/plugin_default_model_service.py`
- 测试：`server/python/tests/ai/unit/services/test_plugin_default_model_service.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/services/test_plugin_default_model_service.py`：

```python
"""PluginDefaultModelService 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai.services.plugin_default_model_service import plugin_default_model_service
from ai.models.plugin_default_model import PluginDefaultModel


class TestPluginDefaultModelService:
    """服务测试类"""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_get_default_model_found(self, mock_session):
        """测试获取默认模型（存在）"""
        mock_model = MagicMock(spec=PluginDefaultModel)
        mock_model.plugin_id = "alon/tongyi"
        mock_model.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_model,
        ):
            result = await plugin_default_model_service.get_default_model(
                mock_session, "tenant-001", "llm"
            )

        assert result is not None
        assert result.plugin_id == "alon/tongyi"

    @pytest.mark.asyncio
    async def test_get_default_model_not_found(self, mock_session):
        """测试获取默认模型（不存在）"""
        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await plugin_default_model_service.get_default_model(
                mock_session, "tenant-001", "llm"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_set_default_model_create(self, mock_session):
        """测试设置默认模型（创建）"""
        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                PluginDefaultModel,
                "create",
                new_callable=AsyncMock,
            ) as mock_create:
                await plugin_default_model_service.set_default_model(
                    mock_session,
                    tenant_id="tenant-001",
                    model_type="llm",
                    plugin_id="alon/tongyi",
                    model_name="qwen-plus",
                )
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_default_model_update(self, mock_session):
        """测试设置默认模型（更新）"""
        mock_existing = MagicMock(spec=PluginDefaultModel)
        mock_existing.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_existing,
        ):
            await plugin_default_model_service.set_default_model(
                mock_session,
                tenant_id="tenant-001",
                model_type="llm",
                plugin_id="alon/tongyi",
                model_name="qwen-max",
            )
            assert mock_existing.model_name == "qwen-max"

    @pytest.mark.asyncio
    async def test_clear_default_model(self, mock_session):
        """测试清除默认模型"""
        mock_existing = MagicMock(spec=PluginDefaultModel)
        mock_existing.is_valid = True

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_existing,
        ):
            await plugin_default_model_service.clear_default_model(
                mock_session, "tenant-001", "llm"
            )
            assert mock_existing.is_valid is False
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_plugin_default_model_service.py -v`
预期：FAIL

- [ ] **步骤 3：创建服务文件**

创建 `server/python/src/ai/services/plugin_default_model_service.py`：

```python
"""插件默认模型服务"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin_default_model import PluginDefaultModel

_logger = logger.bind(name=__name__)


class PluginDefaultModelService:
    """插件默认模型服务"""

    async def get_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
    ) -> PluginDefaultModel | None:
        """获取默认模型"""
        return await PluginDefaultModel.one_by_conditions(
            session,
            conditions=[
                PluginDefaultModel.tenant_id == tenant_id,
                PluginDefaultModel.model_type == model_type,
                PluginDefaultModel.is_valid == True,
            ],
        )

    async def set_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
        plugin_id: str,
        model_name: str | None = None,
        credential_id: str | None = None,
        custom_base_url: str | None = None,
        custom_model_name: str | None = None,
    ) -> PluginDefaultModel:
        """设置默认模型（upsert）"""
        existing = await self.get_default_model(session, tenant_id, model_type)

        if existing:
            existing.plugin_id = plugin_id
            existing.model_name = model_name
            existing.credential_id = credential_id
            existing.custom_base_url = custom_base_url
            existing.custom_model_name = custom_model_name
            existing.is_valid = True
            return existing
        else:
            return await PluginDefaultModel.create(
                session,
                tenant_id=tenant_id,
                model_type=model_type,
                plugin_id=plugin_id,
                model_name=model_name,
                credential_id=credential_id,
                custom_base_url=custom_base_url,
                custom_model_name=custom_model_name,
                is_valid=True,
            )

    async def clear_default_model(
        self,
        session: AsyncSession,
        tenant_id: str,
        model_type: str,
    ) -> None:
        """清除默认模型（软删除）"""
        existing = await self.get_default_model(session, tenant_id, model_type)
        if existing:
            existing.is_valid = False


plugin_default_model_service = PluginDefaultModelService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_plugin_default_model_service.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/services/plugin_default_model_service.py server/python/tests/ai/unit/services/test_plugin_default_model_service.py
git commit -m "feat(ai): 新增 PluginDefaultModelService 服务"
```

---

## 任务 4：创建数据库迁移文件

**文件：**
- 创建：`server/python/src/ai/migrations/versions/003_add_plugin_default_models.py`

- [ ] **步骤 1：创建迁移文件**

创建 `server/python/src/ai/migrations/versions/003_add_plugin_default_models.py`：

```python
"""添加 plugin_default_models 表

Revision ID: 003
Revises: 002_simplify_model_tables
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa

revision = "003_add_plugin_default_models"
down_revision = "002_simplify_model_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plugin_default_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("plugin_id", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("credential_id", sa.String(36), nullable=True),
        sa.Column("custom_base_url", sa.String(512), nullable=True),
        sa.Column("custom_model_name", sa.String(255), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
        schema="ai",
    )

    op.create_index("ix_plugin_default_models_plugin_id", "plugin_default_models", ["plugin_id"], schema="ai")
    op.create_index("ix_plugin_default_models_credential_id", "plugin_default_models", ["credential_id"], schema="ai")


def downgrade() -> None:
    op.drop_index("ix_plugin_default_models_credential_id", schema="ai")
    op.drop_index("ix_plugin_default_models_plugin_id", schema="ai")
    op.drop_table("plugin_default_models", schema="ai")
```

- [ ] **步骤 2：验证迁移文件语法**

运行：`cd server/python && uv run python -c "from ai.migrations.versions import *; print('OK')"`
预期：输出 "OK"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/migrations/versions/003_add_plugin_default_models.py
git commit -m "feat(ai): 添加 plugin_default_models 表迁移"
```

---

## 任务 5：更新 models/__init__.py 导出新模型

**文件：**
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：更新导出**

修改 `server/python/src/ai/models/__init__.py`：

```python
"""
AI 模块数据模型

包含 AI 相关的所有模型。
所有模型归属于 ai PostgreSQL schema。
"""

from framework.database import create_base_model, create_module_base

# 创建 AI 模块的 Base 和 BaseModel
Base = create_module_base("ai")
BaseModel = create_base_model(Base)

# 导入模型（必须在 Base 和 BaseModel 定义之后）
from .conversation import Conversation
from .enums import ConversationMode, ConversationStatus, MessageRole, MessageStatus
from .message import Message
from .plugin import (
    CredentialScope,
    InstallType,
    PluginCredential,
    PluginInstallTask,
    PluginStatus,
    PluginType,
    RuntimeType,
    SourceType,
    TaskStatus,
)
from .plugin_config import PluginConfig
from .plugin_default_model import PluginDefaultModel
from .plugin_runtime_state import PluginRuntimeState

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # 枚举
    "PluginType",
    "InstallType",
    "RuntimeType",
    "SourceType",
    "TaskStatus",
    "PluginStatus",
    "CredentialScope",
    # 插件相关
    "PluginConfig",
    "PluginDefaultModel",
    "PluginInstallTask",
    "PluginCredential",
    "PluginRuntimeState",
    # 会话相关
    "ConversationStatus",
    "ConversationMode",
    "MessageStatus",
    "MessageRole",
    "Conversation",
    "Message",
]
```

- [ ] **步骤 2：验证导入无错误**

运行：`cd server/python && uv run python -c "from ai.models import PluginDefaultModel; print('OK')"`
预期：输出 "OK"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/models/__init__.py
git commit -m "feat(ai): 导出 PluginDefaultModel"
```

---

## 任务 6：重写 ProviderManager

**文件：**
- 重写：`server/python/src/ai/components/model/internal/provider_manager.py`
- 重写：`server/python/tests/ai/unit/components/model/test_provider_manager.py`

- [ ] **步骤 1：编写失败的测试**

创建新的测试文件 `server/python/tests/ai/unit/components/model/test_provider_manager.py`：

```python
"""ProviderManager 重写测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin_default_model import PluginDefaultModel


class TestProviderManagerRewrite:
    """ProviderManager 重写测试"""

    @pytest.fixture
    def provider_manager(self):
        return ProviderManager()

    def test_no_deprecated_methods(self, provider_manager):
        """测试不存在废弃方法"""
        # 这些方法应该不存在
        assert not hasattr(provider_manager, "_get_all_custom_models")
        assert not hasattr(provider_manager, "_get_all_providers")
        assert not hasattr(provider_manager, "_get_all_provider_model_settings")

    def test_no_get_default_model(self, provider_manager):
        """测试 get_default_model 已删除"""
        # 此方法应该不存在（功能转移到 PluginDefaultModelService）
        assert not hasattr(provider_manager, "get_default_model")

    def test_no_update_default_model_record(self, provider_manager):
        """测试 update_default_model_record 已删除"""
        assert not hasattr(provider_manager, "update_default_model_record")

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_from_db(self, provider_manager):
        """测试从数据库获取默认模型"""
        mock_session = MagicMock()

        mock_default = MagicMock(spec=PluginDefaultModel)
        mock_default.plugin_id = "alon/tongyi"
        mock_default.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                tenant_id="tenant-001",
                model_type="llm",
                db_session=mock_session,
            )

        assert plugin_id == "alon/tongyi"
        assert model_name == "qwen-plus"

    @pytest.mark.asyncio
    async def test_get_default_provider_model_name_fallback(self, provider_manager):
        """测试无默认配置时返回第一个可用模型"""
        mock_session = MagicMock()

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                provider_manager,
                "_get_first_provider_first_model",
                new_callable=AsyncMock,
                return_value=("default/plugin", "default-model"),
            ):
                plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                    tenant_id="tenant-001",
                    model_type="llm",
                    db_session=mock_session,
                )

        assert plugin_id == "default/plugin"
        assert model_name == "default-model"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/components/model/test_provider_manager.py -v`
预期：FAIL（因为旧代码还有废弃方法）

- [ ] **步骤 3：重写 ProviderManager**

完全重写 `server/python/src/ai/components/model/internal/provider_manager.py`（由于篇幅限制，仅展示关键部分，完整实现见规格文档）：

```python
"""供应商管理器类（重写版）

简化后的职责：
1. 从插件 manifest 获取供应商配置
2. 注入插件凭证
3. 查询默认模型
"""

from collections import defaultdict
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.model.errors import ProviderNotFoundError
from ai.components.model.internal.entities.provider_entities import (
    CustomConfiguration,
    CustomProviderConfiguration,
)
from ai.components.model.internal.model_provider_factory import ModelProviderFactory
from ai.components.model.internal.provider_configuration import (
    ProviderConfiguration,
    ProviderConfigurations,
)
from ai.components.model.schema.provider_entities import ProviderEntity
from ai.models.plugin import PluginCredential
from ai.models.plugin_default_model import PluginDefaultModel
from ai.services.credential_service import credential_service
from ai_plugin.sdk.entities.model import ModelType
from framework.cache import get_cache_manager

_logger = logger.bind(name=__name__)

CACHE_KEY_PREFIX = "model_provider_config"
CACHE_TTL = 3600  # 1小时


class ProviderManager:
    """供应商管理器（重写版）"""

    @staticmethod
    async def clear_cache(tenant_id: str) -> None:
        """清除缓存"""
        try:
            cache_manager = get_cache_manager()
            cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"
            await cache_manager.delete(cache_key, tenant_id=tenant_id)
            _logger.debug(f"已清除缓存 tenant_id={tenant_id}")
        except Exception as e:
            _logger.warning(f"清除缓存失败: {e}")

    async def get_configurations(
        self,
        tenant_id: str,
        use_cache: bool = True,
        db_session: AsyncSession | None = None,
    ) -> ProviderConfigurations:
        """获取模型供应商配置集合（简化版）"""
        cache_key = f"{CACHE_KEY_PREFIX}:{tenant_id}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cache_manager = get_cache_manager()
                cached_data = await cache_manager.get(cache_key, tenant_id=tenant_id)

                if cached_data:
                    _logger.debug(f"使用缓存配置 tenant_id={tenant_id}")
                    model_provider_factory = ModelProviderFactory(tenant_id)
                    provider_entities = await model_provider_factory.get_providers()
                    provider_entities_dict = {p.provider: p for p in provider_entities}
                    return ProviderConfigurations.from_dict(cached_data, provider_entities_dict)
            except Exception as e:
                _logger.warning(f"读取缓存失败: {e}")

        # 从插件 manifest 获取配置
        _logger.debug(f"从插件 manifest 加载配置 tenant_id={tenant_id}")
        model_provider_factory = ModelProviderFactory(tenant_id)
        provider_entities = await model_provider_factory.get_providers()

        provider_configurations = ProviderConfigurations(tenant_id=tenant_id)

        # 构造每个供应商的配置对象
        for provider_entity in provider_entities:
            custom_configuration = self._build_custom_configuration(provider_entity)

            provider_configuration = ProviderConfiguration(
                provider=provider_entity,
                custom_configuration=custom_configuration,
                model_settings=[],
                tenant_id=tenant_id,
            )
            provider_configurations[provider_entity.provider] = provider_configuration

        # 注入插件凭证
        if db_session:
            await self._inject_plugin_credentials(
                session=db_session,
                tenant_id=tenant_id,
                provider_configurations=provider_configurations,
            )

        # 存入缓存
        if use_cache:
            try:
                cache_manager = get_cache_manager()
                await cache_manager.set(
                    cache_key,
                    provider_configurations.to_dict(),
                    ttl=CACHE_TTL,
                    tenant_id=tenant_id,
                )
            except Exception as e:
                _logger.warning(f"缓存配置失败: {e}")

        return provider_configurations

    def _build_custom_configuration(
        self,
        provider_entity: ProviderEntity,
    ) -> CustomConfiguration:
        """构造自定义配置（简化版，不查询数据库）"""
        return CustomConfiguration(provider=None, models=[])

    async def _inject_plugin_credentials(
        self,
        session: AsyncSession,
        tenant_id: str,
        provider_configurations: ProviderConfigurations,
    ) -> None:
        """注入插件凭证"""
        for provider_name, config in provider_configurations.items():
            try:
                plugin_id = self._extract_plugin_id_from_provider(provider_name)
                if not plugin_id:
                    continue

                credential = await PluginCredential.one_by_conditions(
                    session,
                    conditions=[
                        PluginCredential.tenant_id == tenant_id,
                        PluginCredential.plugin_id == plugin_id,
                        PluginCredential.is_default == True,
                        PluginCredential.is_disabled == False,
                    ],
                )

                if not credential:
                    continue

                credentials_schema = self._extract_credentials_schema_from_provider(config.provider)
                decrypted = credential_service.decrypt_credentials(
                    credential.credentials or {},
                    credentials_schema,
                )

                if config.custom_configuration.provider is None:
                    config.custom_configuration.provider = CustomProviderConfiguration(
                        credentials=decrypted
                    )
                else:
                    config.custom_configuration.provider.credentials = decrypted

            except Exception as e:
                _logger.warning(f"注入凭证失败 provider={provider_name}: {e}")
                continue

    def _extract_plugin_id_from_provider(self, provider_name: str) -> str | None:
        """从 provider 名称提取 plugin_id"""
        try:
            from ai.components.model.schema.provider_id import ModelProviderID
            provider_id = ModelProviderID(provider_name)
            return provider_id.plugin_id
        except Exception:
            return None

    def _extract_credentials_schema_from_provider(
        self,
        provider_entity: ProviderEntity,
    ) -> list[dict]:
        """提取凭证架构"""
        if not provider_entity.provider_credential_schema:
            return []

        schemas = provider_entity.provider_credential_schema.credential_form_schemas
        if not schemas:
            return []

        result = []
        for schema in schemas:
            item = {
                "name": schema.variable,
                "type": schema.type.value if hasattr(schema.type, "value") else str(schema.type),
                "required": schema.required,
            }
            result.append(item)

        return result

    async def get_default_provider_model_name(
        self,
        tenant_id: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> tuple[str | None, str | None]:
        """获取默认供应商和模型名称（从数据库查询）"""
        if db_session:
            default_model = await PluginDefaultModel.one_by_conditions(
                db_session,
                conditions=[
                    PluginDefaultModel.tenant_id == tenant_id,
                    PluginDefaultModel.model_type == model_type.value,
                    PluginDefaultModel.is_valid == True,
                ],
            )

            if default_model:
                if default_model.model_name:
                    return default_model.plugin_id, default_model.model_name
                else:
                    return default_model.plugin_id, default_model.custom_model_name

        # 没有配置默认模型，返回第一个可用模型
        return await self._get_first_provider_first_model(tenant_id, model_type, db_session)

    async def _get_first_provider_first_model(
        self,
        tenant_id: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> tuple[str | None, str | None]:
        """获取第一个供应商的第一个模型"""
        configurations = await self.get_configurations(tenant_id, db_session=db_session)
        models = await configurations.get_models(model_type=model_type, only_active=True)

        if not models:
            return None, None

        first_model = models[0]
        return first_model.provider.provider, first_model.model

    async def _get_provider_model_bundle(
        self,
        tenant_id: str,
        provider: str,
        model_type: ModelType,
        db_session: AsyncSession | None = None,
    ) -> "ProviderModelBundle":
        """获取供应商模型束"""
        from ai.components.model.internal.provider_entities import ProviderModelBundle

        configurations = await self.get_configurations(tenant_id, db_session=db_session)
        provider_configuration = configurations.get(provider)

        if not provider_configuration:
            raise ProviderNotFoundError(provider)

        model_type_instance = await provider_configuration.get_model_type_instance(model_type)

        return ProviderModelBundle(
            configuration=provider_configuration,
            model_type_instance=model_type_instance,
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/components/model/test_provider_manager.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/components/model/internal/provider_manager.py server/python/tests/ai/unit/components/model/test_provider_manager.py
git commit -m "refactor(ai): 重写 ProviderManager

- 删除所有废弃方法
- 简化 get_configurations 流程
- 从 plugin_default_models 表查询默认模型
- 移除所有 TODO 注释"
```

---

## 任务 7：重构 ProviderConfiguration

**文件：**
- 修改：`server/python/src/ai/components/model/internal/provider_configuration.py`

- [ ] **步骤 1：删除废弃方法**

移除以下方法：
- `add_or_update_custom_credentials()`
- `delete_custom_credentials()`

简化以下方法（移除 TODO 注释）：
- `custom_credentials_validate()`
- `custom_model_credentials_validate()`

- [ ] **步骤 2：验证修改无语法错误**

运行：`cd server/python && uv run python -c "from ai.components.model.internal.provider_configuration import ProviderConfiguration; print('OK')"`
预期：输出 "OK"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/components/model/internal/provider_configuration.py
git commit -m "refactor(ai): 清理 ProviderConfiguration 废弃方法"
```

---

## 任务 8：重构 DefaultModelService

**文件：**
- 修改：`server/python/src/ai/components/model/services/management_service.py`

- [ ] **步骤 1：重构 DefaultModelService**

修改 `server/python/src/ai/components/model/services/management_service.py`：

```python
class DefaultModelService:
    """默认模型管理器（重构版）"""

    def __init__(self, tenant_id: str):
        self._tenant_id = tenant_id
        self._service = plugin_default_model_service

    async def get_default_model(self, model_type: ModelType) -> PluginDefaultModel | None:
        """获取默认模型"""
        from framework.database.dependencies import get_db_session

        async with get_db_session() as session:
            return await self._service.get_default_model(
                session, self._tenant_id, model_type.value
            )

    async def set_default_model(
        self,
        model_type: ModelType,
        plugin_id: str,
        model_name: str | None = None,
        credential_id: str | None = None,
        custom_base_url: str | None = None,
        custom_model_name: str | None = None,
    ) -> PluginDefaultModel:
        """设置默认模型"""
        from framework.database.dependencies import get_db_session

        async with get_db_session() as session:
            result = await self._service.set_default_model(
                session,
                tenant_id=self._tenant_id,
                model_type=model_type.value,
                plugin_id=plugin_id,
                model_name=model_name,
                credential_id=credential_id,
                custom_base_url=custom_base_url,
                custom_model_name=custom_model_name,
            )
            await session.commit()
            return result

    async def clear_default_model(self, model_type: ModelType) -> None:
        """清除默认模型"""
        from framework.database.dependencies import get_db_session

        async with get_db_session() as session:
            await self._service.clear_default_model(
                session, self._tenant_id, model_type.value
            )
            await session.commit()
```

- [ ] **步骤 2：验证修改无语法错误**

运行：`cd server/python && uv run python -c "from ai.components.model.services.management_service import DefaultModelService; print('OK')"`
预期：输出 "OK"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/components/model/services/management_service.py
git commit -m "refactor(ai): 重构 DefaultModelService 基于新表"
```

---

## 任务 9：集成测试验证整体流程

**文件：**
- 创建：`server/python/tests/ai/integration/test_plugin_default_model_flow.py`

- [ ] **步骤 1：编写集成测试**

创建 `server/python/tests/ai/integration/test_plugin_default_model_flow.py`：

```python
"""默认模型配置集成测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin_default_model import PluginDefaultModel
from ai.services.plugin_default_model_service import plugin_default_model_service


class TestPluginDefaultModelFlow:
    """默认模型配置流程测试"""

    @pytest.mark.asyncio
    async def test_set_and_get_default_model(self):
        """测试设置和获取默认模型"""
        mock_session = MagicMock()

        # 设置默认模型
        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                PluginDefaultModel,
                "create",
                new_callable=AsyncMock,
            ):
                await plugin_default_model_service.set_default_model(
                    mock_session,
                    tenant_id="tenant-001",
                    model_type="llm",
                    plugin_id="alon/tongyi",
                    model_name="qwen-plus",
                )

    @pytest.mark.asyncio
    async def test_provider_manager_uses_default_model(self):
        """测试 ProviderManager 使用默认模型"""
        provider_manager = ProviderManager()
        mock_session = MagicMock()

        mock_default = MagicMock(spec=PluginDefaultModel)
        mock_default.plugin_id = "alon/tongyi"
        mock_default.model_name = "qwen-plus"

        with patch.object(
            PluginDefaultModel,
            "one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            plugin_id, model_name = await provider_manager.get_default_provider_model_name(
                tenant_id="tenant-001",
                model_type="llm",
                db_session=mock_session,
            )

        assert plugin_id == "alon/tongyi"
        assert model_name == "qwen-plus"
```

- [ ] **步骤 2：运行集成测试**

运行：`cd server/python && uv run pytest tests/ai/integration/test_plugin_default_model_flow.py -v`
预期：PASS

- [ ] **步骤 3：Commit**

```bash
git add server/python/tests/ai/integration/test_plugin_default_model_flow.py
git commit -m "test(ai): 添加默认模型配置集成测试"
```

---

## 任务 10：更新 MIGRATION.md 文档

**文件：**
- 修改：`server/python/src/ai/components/model/MIGRATION.md`

- [ ] **步骤 1：更新迁移文档**

在 `server/python/src/ai/components/model/MIGRATION.md` 末尾添加：

```markdown
## ProviderManager 重写（2026-07-01）

### 新增表

| 表名 | 说明 |
|------|------|
| plugin_default_models | 默认模型配置，支持标准模型和自定义模型 |

### 删除的方法

以下方法已从 ProviderManager 中删除：

| 方法 | 原因 |
|------|------|
| `_get_all_custom_models()` | 模型定义来自插件 manifest |
| `_get_all_providers()` | 供应商定义来自插件 manifest |
| `_get_all_provider_model_settings()` | 模型设置来自插件 manifest |
| `get_default_model()` | 功能转移到 PluginDefaultModelService |
| `update_default_model_record()` | 功能转移到 PluginDefaultModelService |

### 简化的流程

**get_configurations() 简化：**

原流程：
1. _get_all_providers() → 空字典
2. ModelProviderFactory.get_providers() → 插件 manifest
3. _get_all_provider_model_settings() → 空字典
4. _get_all_custom_models() → 空字典
5. 构造 ProviderConfiguration
6. _inject_plugin_credentials()

新流程：
1. ModelProviderFactory.get_providers() → 插件 manifest
2. 构造 ProviderConfiguration
3. _inject_plugin_credentials()

**默认模型查询：**

从 `plugin_default_models` 表查询，不再依赖废弃的 `model_tenant_default` 表。
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/ai/components/model/MIGRATION.md
git commit -m "docs(ai): 更新 MIGRATION.md 记录 ProviderManager 重写变更"
```

---

## 自检清单

**1. 规格覆盖度：**
- [ ] 新增 plugin_default_models 表 → 任务 1, 4
- [ ] PluginDefaultModelService 服务 → 任务 3
- [ ] ProviderManager 重写 → 任务 6
- [ ] ProviderConfiguration 重构 → 任务 7
- [ ] DefaultModelService 重构 → 任务 8
- [ ] 删除废弃方法 → 任务 6, 7
- [ ] 移除 TODO 注释 → 任务 6, 7

**2. 占位符扫描：**
- [ ] 无 "待定"、"TODO"、"后续实现" 字样
- [ ] 所有代码步骤都有完整代码块
- [ ] 所有测试步骤都有完整测试代码

**3. 类型一致性：**
- [ ] PluginDefaultModel 在所有使用处一致
- [ ] db_session 参数类型为 `AsyncSession | None`
- [ ] model_type 使用字符串类型（`llm`, `text-embedding` 等）
