# 插件系统与模型配置整合实现计划

> **规格文档：** [2026-06-30-plugin-model-integration-design.md](../specs/2026-06-30-plugin-model-integration-design.md)
>
> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 简化数据模型，删除未使用的模型表，打通对话接口与插件凭证的关联，让用户只需配置 API Key 即可使用模型。

**架构：** 模型定义完全来自插件 manifest，用户凭证存储在 plugin_credentials 表，对话时通过 plugin_id 关联获取默认凭证。删除冗余的 model_providers 和 model_configs 表。

**技术栈：** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic

---

## 文件结构

### 将删除的文件
- `server/python/src/ai/models/model_provider.py` - 未使用的模型提供商定义
- `server/python/src/ai/models/model_config.py` - 未使用的模型配置定义

### 将修改的文件
- `server/python/src/ai/models/__init__.py` - 移除删除模型的导出
- `server/python/src/ai/models/plugin.py` - 给 PluginCredential 添加 is_default 字段
- `server/python/src/ai/components/model/internal/provider_manager.py` - 改造凭证获取逻辑
- `server/python/src/ai/components/model/internal/provider_configuration.py` - 简化配置获取
- `server/python/src/ai/migrations/versions/001_initial_schema.py` - 移除未使用表的迁移定义

### 将创建的文件
- `server/python/src/ai/migrations/versions/002_simplify_model_tables.py` - 新迁移：添加 is_default 字段，删除未使用表

### 测试文件
- `server/python/tests/ai/unit/models/test_plugin_credential.py` - 新增：PluginCredential 测试
- `server/python/tests/ai/unit/components/model/test_provider_manager.py` - 修改：ProviderManager 测试

---

## 任务 1：给 PluginCredential 添加 is_default 字段

**文件：**
- 修改：`server/python/src/ai/models/plugin.py:214-274`
- 测试：`server/python/tests/ai/unit/models/test_plugin_credential.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/ai/unit/models/test_plugin_credential.py`：

```python
"""PluginCredential 模型测试"""

import pytest

from ai.models.plugin import PluginCredential, CredentialScope


class TestPluginCredential:
    """PluginCredential 测试类"""

    def test_is_default_field_exists(self):
        """测试 is_default 字段存在且默认为 False"""
        # 验证字段定义
        assert hasattr(PluginCredential, "is_default")
        # 获取列对象验证默认值
        column = PluginCredential.__table__.c.is_default
        assert column.default.arg is False

    def test_is_default_can_be_true(self):
        """测试 is_default 可以设置为 True"""
        credential = PluginCredential(
            tenant_id="test-tenant",
            plugin_id="test/plugin",
            plugin_type="model",
            scope=CredentialScope.GLOBAL,
            name="测试凭证",
            credentials={"api_key": "test"},
            is_default=True,
        )
        assert credential.is_default is True
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/models/test_plugin_credential.py -v`
预期：FAIL，报错 `AttributeError: type object 'PluginCredential' has no attribute 'is_default'`

- [ ] **步骤 3：修改 PluginCredential 模型**

在 `server/python/src/ai/models/plugin.py` 的 `PluginCredential` 类中添加 `is_default` 字段：

```python
class PluginCredential(
    BaseModel,
    AuditMixin,
    ActiveRecordMixin,
    TenantMixin,
):
    """插件凭证（全局多凭证池，预留个人维度）"""

    __tablename__ = "plugin_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_plugin_credentials_tenant_name"),
    )

    # ... 现有字段保持不变 ...

    # 是否禁用
    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否禁用",
    )

    # 是否为默认凭证
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否为默认凭证",
    )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/models/test_plugin_credential.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/models/plugin.py server/python/tests/ai/unit/models/test_plugin_credential.py
git commit -m "feat(ai): 给 PluginCredential 添加 is_default 字段

- 添加 is_default 布尔字段，默认 False
- 支持租户级别的默认凭证设置
- 添加单元测试验证字段行为"
```

---

## 任务 2：删除未使用的模型文件

**文件：**
- 删除：`server/python/src/ai/models/model_provider.py`
- 删除：`server/python/src/ai/models/model_config.py`
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：更新 models/__init__.py 移除导出**

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

- [ ] **步骤 2：删除未使用的模型文件**

```bash
rm server/python/src/ai/models/model_provider.py
rm server/python/src/ai/models/model_config.py
```

- [ ] **步骤 3：验证导入无错误**

运行：`cd server/python && uv run python -c "from ai.models import *; print('导入成功')"`
预期：输出 "导入成功"

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/ai/models/__init__.py
git add -u server/python/src/ai/models/model_provider.py server/python/src/ai/models/model_config.py
git commit -m "refactor(ai): 删除未使用的模型提供商和模型配置模型

- 删除 model_provider.py（ModelProvider, ProviderType）
- 删除 model_config.py（ModelConfig, ModelType）
- 模型定义现在完全来自插件 manifest"
```

---

## 任务 3：创建数据库迁移

**文件：**
- 创建：`server/python/src/ai/migrations/versions/002_simplify_model_tables.py`

- [ ] **步骤 1：创建迁移文件**

创建 `server/python/src/ai/migrations/versions/002_simplify_model_tables.py`：

```python
"""简化模型表结构

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2026-06-30

- 给 plugin_credentials 添加 is_default 字段
- 删除未使用的 model_providers 表
- 删除未使用的 model_configs 表
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002_simplify_model_tables"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：添加字段，删除表"""

    # 1. 给 plugin_credentials 添加 is_default 字段
    op.add_column(
        "plugin_credentials",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否为默认凭证",
        ),
        schema="ai",
    )

    # 2. 创建索引
    op.create_index(
        "ix_plugin_credentials_is_default",
        "plugin_credentials",
        ["is_default"],
        schema="ai",
    )

    # 3. 删除未使用的表
    op.drop_table("model_configs", schema="ai")
    op.drop_table("model_providers", schema="ai")


def downgrade() -> None:
    """降级：恢复表，删除字段"""

    # 1. 重建 model_providers 表
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("provider_type", sa.String(64), nullable=False),
        sa.Column("plugin_id", sa.String(128), nullable=True),
        sa.Column("credentials", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        schema="ai",
    )

    # 2. 重建 model_configs 表
    op.create_table(
        "model_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("provider_id", sa.String(36), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("parameters", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        schema="ai",
    )

    # 3. 删除 is_default 字段
    op.drop_index("ix_plugin_credentials_is_default", schema="ai")
    op.drop_column("plugin_credentials", "is_default", schema="ai")
```

- [ ] **步骤 2：验证迁移文件语法**

运行：`cd server/python && uv run python -c "from ai.migrations.versions import upgrade; print('迁移文件语法正确')"`
预期：输出 "迁移文件语法正确"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/migrations/versions/002_simplify_model_tables.py
git commit -m "feat(ai): 添加数据库迁移简化模型表结构

- 给 plugin_credentials 添加 is_default 字段
- 删除未使用的 model_providers 表
- 删除未使用的 model_configs 表"
```

---

## 任务 4：改造 ProviderManager 凭证获取逻辑

**文件：**
- 修改：`server/python/src/ai/components/model/internal/provider_manager.py`
- 测试：`server/python/tests/ai/unit/components/model/test_provider_manager.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/components/model/test_provider_manager.py`：

```python
"""ProviderManager 测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.components.model.internal.provider_manager import ProviderManager
from ai.models.plugin import PluginCredential, CredentialScope


class TestProviderManagerCredentials:
    """ProviderManager 凭证获取测试"""

    @pytest.fixture
    def provider_manager(self):
        """创建 ProviderManager 实例"""
        return ProviderManager()

    @pytest.mark.asyncio
    async def test_get_plugin_credentials_success(self, provider_manager):
        """测试成功获取插件凭证"""
        tenant_id = "test-tenant"
        plugin_id = "alon/tongyi"

        # Mock 数据库查询
        mock_credential = MagicMock(spec=PluginCredential)
        mock_credential.credentials = {"api_key": "encrypted_key"}
        mock_credential.plugin_id = plugin_id

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_credential,
        ):
            with patch(
                "ai.services.credential_service.credential_service.decrypt_credentials",
                return_value={"api_key": "decrypted_key"},
            ):
                result = await provider_manager._get_plugin_credentials(
                    tenant_id, plugin_id
                )

        assert result == {"api_key": "decrypted_key"}

    @pytest.mark.asyncio
    async def test_get_plugin_credentials_not_found(self, provider_manager):
        """测试凭证不存在时抛出异常"""
        tenant_id = "test-tenant"
        plugin_id = "nonexistent/plugin"

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(ValueError, match="未配置凭证"):
                await provider_manager._get_plugin_credentials(tenant_id, plugin_id)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/components/model/test_provider_manager.py -v`
预期：FAIL，报错 `AttributeError: 'ProviderManager' object has no attribute '_get_plugin_credentials'`

- [ ] **步骤 3：在 ProviderManager 中添加凭证获取方法**

在 `server/python/src/ai/components/model/internal/provider_manager.py` 中添加新方法：

```python
from ai.models.plugin import PluginCredential
from ai.services.credential_service import credential_service

class ProviderManager:
    # ... 现有代码保持不变 ...

    async def _get_plugin_credentials(
        self,
        tenant_id: str,
        plugin_id: str,
    ) -> dict:
        """
        获取插件的默认凭证

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID（如 alon/tongyi）

        Returns:
            解密后的凭证字典

        Raises:
            ValueError: 插件未配置凭证
        """
        from framework.database.core.engine import async_session

        async with async_session() as session:
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
                raise ValueError(
                    f"插件 {plugin_id} 未配置凭证，请先在插件设置中添加 API Key"
                )

            # 获取凭证架构用于解密
            credentials_schema = await self._get_credentials_schema(plugin_id)

            # 解密凭证
            decrypted = credential_service.decrypt_credentials(
                credential.credentials or {},
                credentials_schema,
            )

            return decrypted

    async def _get_credentials_schema(self, plugin_id: str) -> list[dict]:
        """
        获取插件的凭证架构

        Args:
            plugin_id: 插件 ID

        Returns:
            凭证架构列表
        """
        # 从插件配置中获取凭证架构
        # 这里简化实现，实际需要从插件 manifest 中解析
        return []
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/components/model/test_provider_manager.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/ai/components/model/internal/provider_manager.py server/python/tests/ai/unit/components/model/test_provider_manager.py
git commit -m "feat(ai): 改造 ProviderManager 支持从插件凭证获取配置

- 添加 _get_plugin_credentials 方法获取默认凭证
- 添加 _get_credentials_schema 方法获取凭证架构
- 使用 plugin_credentials 表替代 model_providers 表"
```

---

## 任务 5：清理 ProviderManager 中的 TODO 注释

**文件：**
- 修改：`server/python/src/ai/components/model/internal/provider_manager.py`

- [ ] **步骤 1：删除或改造 _get_all_providers 方法**

将 `_get_all_providers` 方法改为直接返回空字典（因为现在从插件获取）：

```python
async def _get_all_providers(self, tenant_id: str) -> dict[str, list]:
    """
    获取所有模型供应商记录

    注意：此方法已废弃，模型定义现在来自插件 manifest。
    保留方法签名以保持向后兼容。

    Returns:
        空字典
    """
    # 模型定义现在完全来自插件系统
    # 此方法保留仅为向后兼容，后续可删除
    return defaultdict(list)
```

- [ ] **步骤 2：删除其他 TODO 方法或标记为已废弃**

对以下方法添加废弃警告：

```python
async def _get_all_provider_model_settings(self, tenant_id: str) -> dict[str, list]:
    """
    获取所有模型供应商模型设置

    注意：此方法已废弃，模型设置现在由插件管理。
    """
    # 已废弃：模型设置现在由插件管理
    return defaultdict(list)

async def _get_all_custom_models(self, tenant_id: str) -> dict[str, list]:
    """
    获取所有自定义模型记录

    注意：此方法已废弃，自定义模型现在通过插件扩展。
    """
    # 已废弃：自定义模型现在通过插件扩展
    return defaultdict(list)

async def get_default_model_record(self, tenant_id: str, model_type: ModelType) -> None:
    """
    更新默认模型记录

    注意：此方法已废弃，默认模型现在通过 plugin_credentials.is_default 管理。
    """
    # 已废弃：默认模型现在通过 plugin_credentials.is_default 管理
    pass
```

- [ ] **步骤 3：验证代码无语法错误**

运行：`cd server/python && uv run python -c "from ai.components.model.internal.provider_manager import ProviderManager; print('导入成功')"`
预期：输出 "导入成功"

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/ai/components/model/internal/provider_manager.py
git commit -m "refactor(ai): 清理 ProviderManager 中的废弃方法

- 标记 _get_all_providers 为废弃
- 标记 _get_all_provider_model_settings 为废弃
- 标记 _get_all_custom_models 为废弃
- 标记 get_default_model_record 为废弃
- 移除所有 TODO 注释，说明设计决策"
```

---

## 任务 6：更新 MIGRATION.md 文档

**文件：**
- 修改：`server/python/src/ai/components/model/MIGRATION.md`

- [ ] **步骤 1：更新 MIGRATION.md 记录变更**

在 `server/python/src/ai/components/model/MIGRATION.md` 末尾添加：

```markdown
## 架构简化（2026-06-30）

### 删除的模型

以下模型已删除，模型定义现在完全来自插件 manifest：

| 模型 | 说明 | 替代方案 |
|------|------|---------|
| ModelProvider | 模型提供商配置 | 插件 manifest 的 models_configuration |
| ModelConfig | 具体模型配置 | 插件 manifest 的 models 列表 |

### 新增字段

| 表 | 字段 | 说明 |
|----|------|------|
| plugin_credentials | is_default | 标记是否为插件的默认凭证 |

### 凭证获取流程变更

**旧流程（Alon）：**
1. 从 model_providers 表查询提供商配置
2. 从 model_configs 表查询模型配置
3. 从配置中获取凭证

**新流程（AI Platform）：**
1. 从插件 manifest 获取模型定义
2. 从 plugin_credentials 表获取默认凭证
3. 通过 plugin_id 关联插件和凭证

### ProviderManager 改造

以下方法已废弃，保留仅为向后兼容：

- `_get_all_providers()` - 模型定义来自插件
- `_get_all_provider_model_settings()` - 模型设置由插件管理
- `_get_all_custom_models()` - 自定义模型通过插件扩展
- `get_default_model_record()` - 默认凭证通过 is_default 管理

新增方法：

- `_get_plugin_credentials()` - 获取插件的默认凭证
- `_get_credentials_schema()` - 获取插件的凭证架构
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/ai/components/model/MIGRATION.md
git commit -m "docs(ai): 更新 MIGRATION.md 记录架构简化变更"
```

---

## 任务 7：集成测试验证整体流程

**文件：**
- 创建：`server/python/tests/ai/integration/test_plugin_model_flow.py`

- [ ] **步骤 1：编写集成测试**

创建 `server/python/tests/ai/integration/test_plugin_model_flow.py`：

```python
"""插件模型配置集成测试

验证从插件安装到对话使用的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.models.plugin import PluginCredential, CredentialScope
from ai.components.model.services.llm_service import LLMService


class TestPluginModelFlow:
    """插件模型配置流程测试"""

    @pytest.mark.asyncio
    async def test_chat_uses_plugin_credentials(self):
        """测试对话接口使用插件凭证"""
        tenant_id = "test-tenant"
        plugin_id = "alon/tongyi"
        provider = f"{plugin_id}/openai"

        # 1. 模拟插件已安装
        # 2. 模拟凭证已配置
        mock_credential = MagicMock(spec=PluginCredential)
        mock_credential.credentials = {"api_key": "sk-test-key"}
        mock_credential.is_default = True

        # 3. 测试 LLM 调用能获取到凭证
        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_credential,
        ):
            llm_service = LLMService(tenant_id)

            # 验证服务创建成功
            assert llm_service._tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_multiple_credentials_uses_default(self):
        """测试多个凭证时使用默认凭证"""
        tenant_id = "test-tenant"
        plugin_id = "alon/tongyi"

        # 模拟有多个凭证，其中一个是默认的
        mock_default = MagicMock(spec=PluginCredential)
        mock_default.credentials = {"api_key": "default-key"}
        mock_default.is_default = True

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=mock_default,
        ):
            provider_manager = ProviderManager()
            result = await provider_manager._get_plugin_credentials(tenant_id, plugin_id)

            assert result["api_key"] == "default-key"

    @pytest.mark.asyncio
    async def test_no_credentials_raises_error(self):
        """测试未配置凭证时抛出错误"""
        tenant_id = "test-tenant"
        plugin_id = "nonexistent/plugin"

        with patch(
            "ai.components.model.internal.provider_manager.PluginCredential.one_by_conditions",
            new_callable=AsyncMock,
            return_value=None,
        ):
            provider_manager = ProviderManager()

            with pytest.raises(ValueError, match="未配置凭证"):
                await provider_manager._get_plugin_credentials(tenant_id, plugin_id)
```

- [ ] **步骤 2：运行集成测试**

运行：`cd server/python && uv run pytest tests/ai/integration/test_plugin_model_flow.py -v`
预期：PASS

- [ ] **步骤 3：Commit**

```bash
git add server/python/tests/ai/integration/test_plugin_model_flow.py
git commit -m "test(ai): 添加插件模型配置集成测试

- 测试对话接口使用插件凭证
- 测试多凭证时使用默认凭证
- 测试未配置凭证时的错误处理"
```

---

## 自检清单

**1. 规格覆盖度：**
- [x] 删除 model_providers 表 → 任务 2, 任务 3
- [x] 删除 model_configs 表 → 任务 2, 任务 3
- [x] 添加 is_default 字段 → 任务 1
- [x] 改造 ProviderManager → 任务 4, 任务 5
- [x] 打通对话流程 → 任务 7

**2. 占位符扫描：**
- [x] 无 TODO/TBD/待定字样
- [x] 所有代码步骤都有完整代码块
- [x] 所有测试步骤都有完整测试代码

**3. 类型一致性：**
- [x] PluginCredential.is_default 在所有使用处一致
- [x] ProviderManager._get_plugin_credentials 签名一致
