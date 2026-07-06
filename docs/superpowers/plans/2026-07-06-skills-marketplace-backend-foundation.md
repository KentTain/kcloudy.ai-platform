# Skills 市场后端基础实现计划（Phase 1-3）

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 扩展 Tenant 模块的插件市场架构，支持 Skill 类型插件的数据模型、MinIO 存储和三种市场适配器（AgentSkills、ModelScope Skill、本地文件扫描）。

**架构：** Skill 作为 Plugin 的子类型（`plugin_type='skill'`），复用现有 `plugin_definitions` 表，扩展 `skill_type` 和 `runtime_type` 字段。市场适配器复用现有 `MarketplaceAdapter` 协议，新增三个适配器实现。存储服务扩展支持 Skill 包的 `skills/` 路径。

**技术栈：** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + httpx + PyYAML + MinIO

**设计规格：** `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md`

---

## 文件结构

### 创建的文件

| 文件路径 | 职责 |
|---------|------|
| `server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py` | AgentSkills 市场适配器，兼容 agentskills.io 标准 |
| `server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py` | ModelScope Skills 市场适配器 |
| `server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py` | 本地文件扫描适配器 |
| `server/python/src/tenant/migrations/versions/003_add_skill_support.py` | 数据库迁移：扩展 plugin_definitions 表 |
| `server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py` | AgentSkills 适配器单元测试 |
| `server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py` | ModelScope Skill 适配器单元测试 |
| `server/python/tests/tenant/unit/marketplace/test_local_skill_adapter.py` | 本地文件扫描适配器单元测试 |
| `server/python/tests/tenant/unit/services/test_plugin_storage_skill.py` | Skill 存储服务单元测试 |
| `server/python/tests/tenant/integration/test_skill_sync_flow.py` | Skill 同步流程集成测试 |

### 修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/python/src/tenant/models/plugin_definition.py` | 新增 `skill_type` 和 `runtime_type` 字段 |
| `server/python/src/tenant/services/marketplace/protocol.py` | 扩展 `RemotePluginInfo` 支持 Skill 字段 |
| `server/python/src/tenant/services/marketplace/gateway.py` | 注册新适配器，新增 `sync_skill_from_marketplace` 方法 |
| `server/python/src/tenant/services/marketplace/adapters/__init__.py` | 导出新适配器 |
| `server/python/src/tenant/services/plugin_storage_service.py` | 新增 Skill 包上传/下载/解析方法 |

---

## 任务 1：扩展 RemotePluginInfo 协议

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/protocol.py`
- 测试：无（数据类扩展，由后续任务测试）

- [ ] **步骤 1：查看现有 RemotePluginInfo 定义**

运行：`cat server/python/src/tenant/services/marketplace/protocol.py`

确认现有 `RemotePluginInfo` 数据类的字段结构（第 13-29 行）。

- [ ] **步骤 2：扩展 RemotePluginInfo 数据类**

在 `server/python/src/tenant/services/marketplace/protocol.py` 文件中，修改 `RemotePluginInfo` 数据类，在 `plugin_type` 字段后新增 Skill 特有字段：

```python
@dataclass
class RemotePluginInfo:
    """远程插件信息"""

    plugin_id: str  # 插件ID：author/name
    name: str  # 显示名称
    description: str | None  # 描述
    version: str  # 版本
    author: str  # 作者
    icon: str | None  # 图标 URL
    plugin_type: str  # tool/model/agent/skill
    skill_type: str | None = None  # Skill 类型：knowledge(知识文档) | script(简单脚本)
    skill_metadata: dict | None = None  # Skill 特有元数据
    tags: list[str] = field(default_factory=list)  # 标签
    downloads: int | None = None  # 下载量
    manifest_url: str | None  # 清单文件 URL
    download_url: str  # 下载地址
    created_at: datetime | None
    updated_at: datetime | None
```

注意：需要在文件顶部导入 `field`：`from dataclasses import dataclass, field`

- [ ] **步骤 3：验证修改不破坏现有代码**

运行：`cd server/python && uv run python -c "from tenant.services.marketplace.protocol import RemotePluginInfo; print(RemotePluginInfo.__dataclass_fields__.keys())"`

预期：输出包含 `skill_type` 和 `skill_metadata` 字段

- [ ] **步骤 4：运行现有测试确认无回归**

运行：`cd server/python && uv run pytest tests/tenant/ -v -k "marketplace or adapter" --no-header 2>&1 | tail -20`

预期：现有测试全部通过

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/services/marketplace/protocol.py
git commit -m "feat(tenant): 扩展 RemotePluginInfo 支持 Skill 字段

新增 skill_type 和 skill_metadata 字段，用于区分知识文档和简单脚本类型

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2：扩展 PluginDefinition 模型

**文件：**
- 修改：`server/python/src/tenant/models/plugin_definition.py`
- 测试：无（模型扩展，由迁移和后续任务测试）

- [ ] **步骤 1：在 PluginDefinition 模型中新增 Skill 字段**

在 `server/python/src/tenant/models/plugin_definition.py` 文件的 `TenantPluginDefinition` 类中，在 `source_type` 字段后新增两个字段：

```python
    skill_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="Skill 类型：knowledge(知识文档) | script(简单脚本)。仅 plugin_type='skill' 时使用",
    )
    runtime_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="运行时类型：none(零隔离) | sandbox(轻量级沙箱) | local(本地进程)",
    )
```

- [ ] **步骤 2：验证模型定义正确**

运行：`cd server/python && uv run python -c "from tenant.models.plugin_definition import TenantPluginDefinition; print([c.name for c in TenantPluginDefinition.__table__.columns])"`

预期：输出列表包含 `skill_type` 和 `runtime_type`

- [ ] **步骤 3：Commit**

```bash
cd server/python
git add src/tenant/models/plugin_definition.py
git commit -m "feat(tenant): PluginDefinition 模型新增 Skill 字段

新增 skill_type 和 runtime_type 字段，支持 Skill 类型插件

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3：创建数据库迁移脚本

**文件：**
- 创建：`server/python/src/tenant/migrations/versions/003_add_skill_support.py`
- 测试：通过迁移命令验证

- [ ] **步骤 1：查看现有迁移文件格式**

运行：`cat server/python/src/tenant/migrations/versions/002_add_installed_at_to_plugin_installations.py`

了解迁移文件的头部格式和 revision/down_revision 设置。

- [ ] **步骤 2：创建迁移文件**

创建 `server/python/src/tenant/migrations/versions/003_add_skill_support.py`：

```python
"""add skill support to plugin tables

Revision ID: 003
Revises: 002
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 扩展 plugin_definitions 表，新增 Skill 特有字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "skill_type",
            sa.String(16),
            nullable=True,
            comment="Skill 类型：knowledge(知识文档) | script(简单脚本)",
        ),
    )
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "runtime_type",
            sa.String(16),
            nullable=True,
            comment="运行时类型：none(零隔离) | sandbox(轻量级沙箱) | local(本地进程)",
        ),
    )

    # 添加部分索引，仅对 skill 类型查询优化
    op.execute(
        "CREATE INDEX idx_plugin_definitions_skill_type "
        "ON tenant.plugin_definitions (plugin_type, skill_type) "
        "WHERE plugin_type = 'skill';"
    )


def downgrade() -> None:
    op.drop_index("idx_plugin_definitions_skill_type", table_name="plugin_definitions")
    op.drop_column("plugin_definitions", "runtime_type")
    op.drop_column("plugin_definitions", "skill_type")
```

- [ ] **步骤 3：验证迁移脚本语法**

运行：`cd server/python && uv run python -c "import ast; ast.parse(open('src/tenant/migrations/versions/003_add_skill_support.py').read()); print('语法正确')"`

预期：输出"语法正确"

- [ ] **步骤 4：执行迁移（如有数据库环境）**

运行：`cd server/python && uv run python manage.py db migrate --module tenant`

预期：迁移成功执行，无错误

如果数据库不可用，跳过此步骤，在集成环境验证。

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/migrations/versions/003_add_skill_support.py
git commit -m "feat(tenant): 新增 Skill 支持数据库迁移

扩展 plugin_definitions 表，新增 skill_type 和 runtime_type 字段

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4：扩展 PluginStorageService 支持 Skill

**文件：**
- 修改：`server/python/src/tenant/services/plugin_storage_service.py`
- 测试：`server/python/tests/tenant/unit/services/test_plugin_storage_skill.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/services/test_plugin_storage_skill.py`：

```python
"""Skill 存储服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tenant.services.plugin_storage_service import PluginStorageService


class TestSkillStorageService:
    """Skill 存储服务测试"""

    @pytest.fixture
    def storage_service(self):
        """创建存储服务实例（mock 依赖）"""
        with patch("tenant.services.plugin_storage_service.get_storage_provider"), \
             patch("tenant.services.plugin_storage_service.get_settings") as mock_settings:
            mock_settings.return_value.plugin.storage_bucket = "test-bucket"
            mock_settings.return_value.oss = MagicMock()
            service = PluginStorageService()
            service._storage = AsyncMock()
            service._bucket_name = "test-bucket"
            service._initialized = True
            return service

    @pytest.mark.asyncio
    async def test_upload_skill_package_success(self, storage_service):
        """测试成功上传 Skill 包"""
        skill_data = b"fake skill zip data"
        checksum = "abc123def456"

        storage_key = await storage_service.upload_skill_package(
            skill_id="community/airtable",
            skill_data=skill_data,
            checksum=checksum,
            version="1.1.0",
        )

        # 验证存储路径格式
        assert storage_key == "skills/global/community/airtable/1.1.0/skill.zip"

        # 验证上传调用
        storage_service._storage.upload.assert_any_call(
            bucket="test-bucket",
            name="skills/global/community/airtable/1.1.0/skill.zip",
            data=skill_data,
            content_type="application/zip",
        )

        # 验证校验和上传
        storage_service._storage.upload.assert_any_call(
            bucket="test-bucket",
            name="skills/global/community/airtable/1.1.0/checksum.sha256",
            data=checksum.encode("utf-8"),
            content_type="text/plain",
        )

    @pytest.mark.asyncio
    async def test_download_skill_package(self, storage_service):
        """测试下载 Skill 包"""
        storage_service._storage.download.return_value = b"skill data"

        result = await storage_service.download_skill_package(
            "skills/global/community/airtable/1.1.0/skill.zip"
        )

        assert result == b"skill data"
        storage_service._storage.download.assert_called_once_with(
            bucket="test-bucket",
            name="skills/global/community/airtable/1.1.0/skill.zip",
        )

    @pytest.mark.asyncio
    async def test_load_skill_documents_from_zip(self, storage_service):
        """测试从 ZIP 包加载 Skill 文档"""
        import zipfile
        import io

        # 构建 mock ZIP 数据
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("SKILL.md", "# Airtable Skill\nTest content")
            zf.writestr("examples/create.md", "## Example\nCreate record")
        zip_data = zip_buffer.getvalue()

        storage_service._storage.download.return_value = zip_data

        documents = await storage_service.load_skill_documents(
            "skills/global/community/airtable/1.1.0/skill.zip"
        )

        assert "SKILL.md" in documents
        assert "examples/create.md" in documents
        assert "Airtable Skill" in documents["SKILL.md"]

    @pytest.mark.asyncio
    async def test_load_skill_documents_from_single_md(self, storage_service):
        """测试从单个 Markdown 文件加载 Skill 文档"""
        skill_data = b"# Single Skill\nThis is a single markdown file."

        storage_service._storage.download.return_value = skill_data

        documents = await storage_service.load_skill_documents("some/key")

        assert "SKILL.md" in documents
        assert "Single Skill" in documents["SKILL.md"]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/services/test_plugin_storage_skill.py -v`

预期：FAIL，报错 `AttributeError: 'PluginStorageService' object has no attribute 'upload_skill_package'`

- [ ] **步骤 3：实现 Skill 存储方法**

在 `server/python/src/tenant/services/plugin_storage_service.py` 文件的 `PluginStorageService` 类中，在 `download_package` 方法后新增以下方法：

```python
    async def upload_skill_package(
        self,
        skill_id: str,
        skill_data: bytes,
        checksum: str,
        version: str = "latest",
    ) -> str:
        """
        上传 Skill 包到 MinIO

        存储路径：skills/global/{skill_id}/{version}/skill.zip

        Args:
            skill_id: Skill ID，格式：author/name
            skill_data: Skill 包二进制数据
            checksum: SHA256 校验和
            version: 版本号

        Returns:
            str: 存储路径（object key）
        """
        await self._ensure_bucket()

        object_key = f"skills/global/{skill_id}/{version}/skill.zip"
        checksum_key = f"skills/global/{skill_id}/{version}/checksum.sha256"

        try:
            await self._storage.upload(
                bucket=self._bucket_name,
                name=object_key,
                data=skill_data,
                content_type="application/zip",
            )
            await self._storage.upload(
                bucket=self._bucket_name,
                name=checksum_key,
                data=checksum.encode("utf-8"),
                content_type="text/plain",
            )
            logger.info(f"上传 Skill 包成功: {self._bucket_name}/{object_key}")
            return object_key
        except Exception as e:
            logger.error(f"上传 Skill 包失败: {skill_id}/{version} - {e}")
            raise

    async def download_skill_package(self, storage_key: str) -> bytes:
        """
        从 MinIO 下载 Skill 包

        Args:
            storage_key: 存储路径

        Returns:
            bytes: Skill 包二进制数据
        """
        try:
            return await self._storage.download(self._bucket_name, storage_key)
        except Exception as e:
            logger.error(f"下载 Skill 包失败: {storage_key} - {e}")
            raise

    async def load_skill_documents(self, storage_key: str) -> dict[str, str]:
        """
        加载 Skill 包中的所有 Markdown 文档

        支持 ZIP 包和单个 SKILL.md 文件两种格式。

        Args:
            storage_key: 存储路径

        Returns:
            dict[str, str]: {文件名: 文件内容}
        """
        import zipfile
        import io

        skill_data = await self.download_skill_package(storage_key)
        documents: dict[str, str] = {}

        try:
            with zipfile.ZipFile(io.BytesIO(skill_data)) as zf:
                for file_info in zf.filelist:
                    if file_info.filename.endswith(".md"):
                        documents[file_info.filename] = zf.read(file_info.filename).decode("utf-8")
        except zipfile.BadZipFile:
            # 不是 ZIP 格式，尝试解析为单个 SKILL.md 文件
            documents["SKILL.md"] = skill_data.decode("utf-8")

        return documents
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/services/test_plugin_storage_skill.py -v`

预期：4 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/services/plugin_storage_service.py tests/tenant/unit/services/test_plugin_storage_skill.py
git commit -m "feat(tenant): PluginStorageService 新增 Skill 存储方法

新增 upload_skill_package、download_skill_package、load_skill_documents 方法
支持 ZIP 包和单个 Markdown 文件两种格式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5：实现 AgentSkills 市场适配器

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py`
- 测试：`server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py`：

```python
"""AgentSkills 市场适配器单元测试"""

import hashlib
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tenant.services.marketplace.adapters.agentskills_adapter import AgentSkillsAdapter


class TestAgentSkillsAdapter:
    """AgentSkills 适配器测试"""

    @pytest.fixture
    def adapter(self):
        return AgentSkillsAdapter()

    @pytest.fixture
    def mock_config(self):
        return {
            "url": "https://agentskills.io",
            "auth_type": "none",
            "auth_config": {},
        }

    @pytest.mark.asyncio
    async def test_market_type(self, adapter):
        """测试市场类型标识"""
        assert adapter.market_type == "agentskills"

    @pytest.mark.asyncio
    async def test_list_plugins_success(self, adapter, mock_config):
        """测试成功获取 Skill 列表"""
        mock_response_data = {
            "skills": [
                {
                    "identifier": "community/airtable",
                    "name": "airtable",
                    "description": "Airtable REST API via curl",
                    "version": "1.1.0",
                    "author": "community",
                    "tags": ["Airtable", "Productivity"],
                    "download_url": "https://agentskills.io/skills/airtable/download",
                }
            ],
            "total": 1,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            skills, total = await adapter.list_plugins(
                mock_config, keyword="airtable", page=1, page_size=20
            )

        assert total == 1
        assert len(skills) == 1
        assert skills[0].plugin_id == "community/airtable"
        assert skills[0].plugin_type == "skill"
        assert skills[0].skill_type == "knowledge"
        assert "Airtable" in skills[0].tags

    @pytest.mark.asyncio
    async def test_list_plugins_with_pagination(self, adapter, mock_config):
        """测试分页参数传递"""
        mock_response_data = {"skills": [], "total": 100}
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            await adapter.list_plugins(mock_config, page=2, page_size=10)

            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["page"] == 2
            assert call_args.kwargs["params"]["size"] == 10

    @pytest.mark.asyncio
    async def test_download_plugin_success(self, adapter, mock_config):
        """测试成功下载 Skill 包"""
        mock_skill_data = b"fake skill package content"
        mock_response = MagicMock()
        mock_response.content = mock_skill_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            data, checksum = await adapter.download_plugin(
                mock_config, "community/airtable", "1.1.0"
            )

        assert data == mock_skill_data
        assert checksum == hashlib.sha256(mock_skill_data).hexdigest()

    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter, mock_config):
        """测试连接成功"""
        mock_response_data = {"skills": [], "total": 0}
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await adapter.test_connection(mock_config)

        assert result.success is True
        assert result.plugin_count == 0

    @pytest.mark.asyncio
    async def test_get_plugin_success(self, adapter, mock_config):
        """测试获取单个 Skill 详情"""
        mock_response_data = {
            "identifier": "community/airtable",
            "name": "airtable",
            "description": "Airtable REST API via curl",
            "version": "1.1.0",
            "author": "community",
            "tags": ["Airtable"],
            "download_url": "https://agentskills.io/skills/airtable/download",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            skill = await adapter.get_plugin(mock_config, "community/airtable")

        assert skill is not None
        assert skill.plugin_id == "community/airtable"
        assert skill.skill_type == "knowledge"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_agentskills_adapter.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'tenant.services.marketplace.adapters.agentskills_adapter'`

- [ ] **步骤 3：实现 AgentSkills 适配器**

创建 `server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py`：

```python
"""AgentSkills 市场适配器

兼容 https://agentskills.io 开放标准，获取 Skill 资源。
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class AgentSkillsAdapter(MarketplaceAdapter):
    """AgentSkills 市场适配器

    兼容 agentskills.io 开放标准，默认 Skill 类型为 knowledge（知识文档）。
    """

    @property
    def market_type(self) -> str:
        return "agentskills"

    def _build_url(self, config: dict, path: str) -> str:
        """构建完整 API URL"""
        base_url = config.get("url", "").rstrip("/")
        return f"{base_url}{path}"

    def _parse_skill(self, item: dict) -> RemotePluginInfo:
        """解析 Skill 数据为 RemotePluginInfo"""
        return RemotePluginInfo(
            plugin_id=item.get("identifier", ""),
            name=item.get("name", ""),
            description=item.get("description"),
            version=item.get("version", "1.0.0"),
            author=item.get("author", "community"),
            icon=item.get("icon"),
            plugin_type="skill",
            skill_type="knowledge",  # AgentSkills 默认为知识文档
            tags=item.get("tags", []),
            downloads=item.get("downloads"),
            manifest_url=item.get("manifest_url"),
            download_url=item.get("download_url", ""),
            created_at=self._parse_datetime(item.get("created_at")),
            updated_at=self._parse_datetime(item.get("updated_at")),
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析时间字符串"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self._build_url(config, "/api/v1/skills"),
                    params={"page": 1, "size": 1},
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    return MarketplaceTestResult(
                        success=True,
                        message="连接成功",
                        plugin_count=total,
                        latency_ms=latency_ms,
                    )
                return MarketplaceTestResult(
                    success=False,
                    message=f"连接失败: HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )
        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 AgentSkills 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取 Skill 列表"""
        params: dict[str, Any] = {"page": page, "size": page_size}
        if keyword:
            params["keyword"] = keyword

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self._build_url(config, "/api/v1/skills"),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        skills = [self._parse_skill(item) for item in data.get("skills", [])]
        return skills, data.get("total", 0)

    async def get_plugin(
        self, config: dict, plugin_id: str
    ) -> RemotePluginInfo | None:
        """获取单个 Skill 详情"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self._build_url(config, f"/api/v1/skills/{plugin_id}")
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return self._parse_skill(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def download_plugin(
        self, config: dict, plugin_id: str, version: str | None = None
    ) -> tuple[bytes, str]:
        """下载 Skill 包，返回 (数据, SHA256 校验和)"""
        params: dict[str, Any] = {}
        if version:
            params["version"] = version

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                self._build_url(config, f"/api/v1/skills/{plugin_id}/download"),
                params=params,
            )
            response.raise_for_status()

            data = response.content
            checksum = hashlib.sha256(data).hexdigest()
            return data, checksum

    async def check_updates(
        self, config: dict, plugins: Sequence[dict]
    ) -> Sequence[PluginUpdateInfo]:
        """检查 Skill 更新"""
        results: list[PluginUpdateInfo] = []
        for plugin in plugins:
            plugin_id = plugin.get("plugin_id")
            current_version = plugin.get("current_version")
            if not plugin_id:
                continue
            try:
                remote = await self.get_plugin(config, plugin_id)
                if remote:
                    has_update = remote.version != current_version
                    results.append(
                        PluginUpdateInfo(
                            plugin_id=plugin_id,
                            current_version=current_version or "",
                            latest_version=remote.version,
                            has_update=has_update,
                            changelog=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"检查 Skill 更新失败: {plugin_id}, 错误: {e}")
        return results
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_agentskills_adapter.py -v`

预期：6 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/services/marketplace/adapters/agentskills_adapter.py tests/tenant/unit/marketplace/test_agentskills_adapter.py
git commit -m "feat(tenant): 实现 AgentSkills 市场适配器

兼容 agentskills.io 开放标准，支持 Skill 列表浏览、详情查询、下载、更新检查

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6：实现 ModelScope Skill 市场适配器

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py`
- 测试：`server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py`：

```python
"""ModelScope Skill 市场适配器单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)


class TestModelScopeSkillAdapter:
    """ModelScope Skill 适配器测试"""

    @pytest.fixture
    def adapter(self):
        return ModelScopeSkillAdapter()

    @pytest.fixture
    def mock_config(self):
        return {
            "url": "https://modelscope.cn/api/v1",
            "auth_type": "api_key",
            "auth_config": {"api_token": "test-token"},
        }

    @pytest.mark.asyncio
    async def test_market_type(self, adapter):
        """测试市场类型标识"""
        assert adapter.market_type == "modelscope-skill"

    @pytest.mark.asyncio
    async def test_list_plugins_success(self, adapter, mock_config):
        """测试成功获取 Skill 列表"""
        mock_response_data = {
            "Data": {
                "Skills": [
                    {
                        "Id": "test/scraper-skill",
                        "Name": "scraper-skill",
                        "Description": "Web scraper skill",
                        "Version": "1.0.0",
                        "Owner": "test",
                        "Tags": ["scraper", "web"],
                        "Downloads": 100,
                        "Logo": "https://example.com/logo.png",
                        "DownloadUrl": "https://modelscope.cn/api/v1/skills/test/scraper-skill/download",
                        "HasScript": True,
                    }
                ],
                "TotalCount": 1,
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            skills, total = await adapter.list_plugins(mock_config, keyword="scraper")

        assert total == 1
        assert len(skills) == 1
        assert skills[0].plugin_id == "test/scraper-skill"
        assert skills[0].plugin_type == "skill"
        assert skills[0].skill_type == "script"  # HasScript=True
        assert skills[0].downloads == 100

    @pytest.mark.asyncio
    async def test_parse_skill_type_knowledge(self, adapter):
        """测试解析知识文档类型"""
        skill_data = {"HasScript": False}
        assert adapter._parse_skill_type(skill_data) == "knowledge"

    @pytest.mark.asyncio
    async def test_parse_skill_type_script(self, adapter):
        """测试解析脚本类型"""
        skill_data = {"HasScript": True}
        assert adapter._parse_skill_type(skill_data) == "script"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter, mock_config):
        """测试连接成功"""
        mock_response_data = {"Data": {"Skills": [], "TotalCount": 0}}
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await adapter.test_connection(mock_config)

        assert result.success is True
        assert result.plugin_count == 0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'tenant.services.marketplace.adapters.modelscope_skill_adapter'`

- [ ] **步骤 3：实现 ModelScope Skill 适配器**

创建 `server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py`：

```python
"""ModelScope Skills 市场适配器

兼容 https://modelscope.cn/skills API，获取 Skill 资源。
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class ModelScopeSkillAdapter(MarketplaceAdapter):
    """ModelScope Skills 市场适配器

    支持 knowledge（知识文档）和 script（简单脚本）两种 Skill 类型。
    """

    @property
    def market_type(self) -> str:
        return "modelscope-skill"

    def _build_headers(self, config: dict) -> dict[str, str]:
        """构建请求头"""
        headers = {"Accept": "application/json"}
        auth_config = config.get("auth_config", {})
        api_token = auth_config.get("api_token", "")
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    def _build_url(self, config: dict, path: str) -> str:
        """构建完整 API URL"""
        base_url = config.get("url", "https://modelscope.cn/api/v1").rstrip("/")
        return f"{base_url}{path}"

    def _parse_skill_type(self, skill_data: dict) -> str:
        """解析 Skill 类型

        ModelScope 通过 HasScript 字段区分：
        - True: script（简单脚本）
        - False: knowledge（知识文档）
        """
        if skill_data.get("HasScript"):
            return "script"
        return "knowledge"

    def _parse_skill(self, item: dict) -> RemotePluginInfo:
        """解析 Skill 数据为 RemotePluginInfo"""
        namespace = item.get("Owner", "")
        name = item.get("Name", "")
        plugin_id = item.get("Id") or f"{namespace}/{name}"

        return RemotePluginInfo(
            plugin_id=plugin_id,
            name=item.get("ChineseName", name) or name,
            description=item.get("Description", ""),
            version=item.get("Version", "latest"),
            author=namespace,
            icon=item.get("Logo"),
            plugin_type="skill",
            skill_type=self._parse_skill_type(item),
            tags=item.get("Tags", []),
            downloads=item.get("Downloads"),
            manifest_url=None,
            download_url=item.get("DownloadUrl", ""),
            created_at=self._parse_datetime(item.get("CreateTime")),
            updated_at=self._parse_datetime(item.get("UpdateTime")),
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """解析时间字符串"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试市场连接"""
        headers = self._build_headers(config)
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self._build_url(config, "/skills"),
                    headers=headers,
                    params={"PageNumber": 1, "PageSize": 1},
                )
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("Data", {}).get("TotalCount", 0)
                    return MarketplaceTestResult(
                        success=True,
                        message="连接成功",
                        plugin_count=total,
                        latency_ms=latency_ms,
                    )
                return MarketplaceTestResult(
                    success=False,
                    message=f"连接失败: HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )
        except httpx.TimeoutException:
            return MarketplaceTestResult(success=False, message="连接超时")
        except Exception as e:
            logger.error(f"测试 ModelScope Skill 市场连接失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取 Skill 列表"""
        headers = self._build_headers(config)
        params: dict[str, Any] = {"PageNumber": page, "PageSize": page_size}
        if keyword:
            params["Keyword"] = keyword

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self._build_url(config, "/skills"),
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        skills = [
            self._parse_skill(item)
            for item in data.get("Data", {}).get("Skills", [])
        ]
        return skills, data.get("Data", {}).get("TotalCount", 0)

    async def get_plugin(
        self, config: dict, plugin_id: str
    ) -> RemotePluginInfo | None:
        """获取单个 Skill 详情"""
        headers = self._build_headers(config)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self._build_url(config, f"/skills/{plugin_id}"),
                    headers=headers,
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return self._parse_skill(response.json().get("Data", {}))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def download_plugin(
        self, config: dict, plugin_id: str, version: str | None = None
    ) -> tuple[bytes, str]:
        """下载 Skill 包"""
        headers = self._build_headers(config)
        params: dict[str, Any] = {}
        if version:
            params["Version"] = version

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                self._build_url(config, f"/skills/{plugin_id}/download"),
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.content
            checksum = hashlib.sha256(data).hexdigest()
            return data, checksum

    async def check_updates(
        self, config: dict, plugins: Sequence[dict]
    ) -> Sequence[PluginUpdateInfo]:
        """检查 Skill 更新"""
        results: list[PluginUpdateInfo] = []
        for plugin in plugins:
            plugin_id = plugin.get("plugin_id")
            current_version = plugin.get("current_version")
            if not plugin_id:
                continue
            try:
                remote = await self.get_plugin(config, plugin_id)
                if remote:
                    has_update = remote.version != current_version
                    results.append(
                        PluginUpdateInfo(
                            plugin_id=plugin_id,
                            current_version=current_version or "",
                            latest_version=remote.version,
                            has_update=has_update,
                            changelog=None,
                        )
                    )
            except Exception as e:
                logger.warning(f"检查 Skill 更新失败: {plugin_id}, 错误: {e}")
        return results
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py -v`

预期：5 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py
git commit -m "feat(tenant): 实现 ModelScope Skill 市场适配器

兼容 modelscope.cn/skills API，支持 knowledge 和 script 两种 Skill 类型

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7：实现本地文件扫描适配器

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py`
- 测试：`server/python/tests/tenant/unit/marketplace/test_local_skill_adapter.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/marketplace/test_local_skill_adapter.py`：

```python
"""本地文件扫描适配器单元测试"""

import pytest
from pathlib import Path
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter


class TestLocalSkillAdapter:
    """本地文件扫描适配器测试"""

    @pytest.fixture
    def adapter(self):
        return LocalSkillAdapter()

    @pytest.fixture
    def mock_config(self):
        return {
            "url": "file:///data/skills",
            "auth_type": "none",
            "auth_config": {},
        }

    @pytest.mark.asyncio
    async def test_market_type(self, adapter):
        """测试市场类型标识"""
        assert adapter.market_type == "local-skill"

    @pytest.mark.asyncio
    async def test_parse_skill_file_with_front_matter(self, adapter, tmp_path):
        """测试解析带 YAML front matter 的 SKILL.md"""
        skill_file = tmp_path / "airtable" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(
            "---\n"
            "name: airtable\n"
            "description: Airtable REST API via curl\n"
            "version: 1.1.0\n"
            "author: community\n"
            "metadata:\n"
            "  hermes:\n"
            "    tags: [Airtable, Productivity]\n"
            "---\n"
            "# Airtable Skill\n"
            "Work with Airtable's REST API.",
            encoding="utf-8",
        )

        skill_info = await adapter._parse_skill_file(skill_file)

        assert skill_info.plugin_id == "community/airtable"
        assert skill_info.name == "airtable"
        assert skill_info.version == "1.1.0"
        assert skill_info.author == "community"
        assert skill_info.plugin_type == "skill"
        assert skill_info.skill_type == "knowledge"
        assert "Airtable" in skill_info.tags

    @pytest.mark.asyncio
    async def test_parse_skill_file_without_author(self, adapter, tmp_path):
        """测试解析没有 author 的 SKILL.md（默认 local）"""
        skill_file = tmp_path / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text(
            "---\n"
            "name: my-skill\n"
            "description: My custom skill\n"
            "version: 1.0.0\n"
            "---\n"
            "# My Skill",
            encoding="utf-8",
        )

        skill_info = await adapter._parse_skill_file(skill_file)

        assert skill_info.plugin_id == "local/my-skill"
        assert skill_info.author == "local"

    @pytest.mark.asyncio
    async def test_parse_skill_file_invalid_format(self, adapter, tmp_path):
        """测试解析无效格式的文件"""
        skill_file = tmp_path / "invalid.md"
        skill_file.write_text("This is not a valid skill file", encoding="utf-8")

        with pytest.raises(ValueError, match="无效的 Skill 文件格式"):
            await adapter._parse_skill_file(skill_file)

    @pytest.mark.asyncio
    async def test_scan_skills_finds_all_skill_files(self, adapter, tmp_path):
        """测试扫描目录找到所有 SKILL.md 文件"""
        # 创建多个 Skill 目录
        (tmp_path / "skill1" / "SKILL.md").parent.mkdir(parents=True)
        (tmp_path / "skill1" / "SKILL.md").write_text(
            "---\nname: skill1\nversion: 1.0.0\n---\n# Skill 1",
            encoding="utf-8",
        )

        (tmp_path / "skill2" / "SKILL.md").parent.mkdir(parents=True)
        (tmp_path / "skill2" / "SKILL.md").write_text(
            "---\nname: skill2\nversion: 1.0.0\n---\n# Skill 2",
            encoding="utf-8",
        )

        skills = await adapter.scan_skills({}, str(tmp_path))

        assert len(skills) == 2
        skill_names = [s.name for s in skills]
        assert "skill1" in skill_names
        assert "skill2" in skill_names

    @pytest.mark.asyncio
    async def test_list_plugins_uses_scan(self, adapter, tmp_path):
        """测试 list_plugins 方法调用 scan_skills"""
        config = {"url": f"file://{tmp_path}"}

        (tmp_path / "test-skill" / "SKILL.md").parent.mkdir(parents=True)
        (tmp_path / "test-skill" / "SKILL.md").write_text(
            "---\nname: test-skill\nversion: 1.0.0\n---\n# Test",
            encoding="utf-8",
        )

        skills, total = await adapter.list_plugins(config)

        assert total == 1
        assert skills[0].name == "test-skill"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_local_skill_adapter.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'tenant.services.marketplace.adapters.local_skill_adapter'`

- [ ] **步骤 3：实现本地文件扫描适配器**

创建 `server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py`：

```python
"""本地文件扫描适配器

从服务器本地目录扫描 Skill 文件，支持 SKILL.md 格式。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import yaml
from loguru import logger

from tenant.services.marketplace.protocol import (
    MarketplaceAdapter,
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocalSkillAdapter(MarketplaceAdapter):
    """本地 Skill 扫描适配器

    从服务器本地目录扫描 SKILL.md 文件，解析 YAML front matter 获取 Skill 元数据。
    支持格式：
    1. 单个 SKILL.md 文件
    2. 包含 SKILL.md 的目录
    """

    @property
    def market_type(self) -> str:
        return "local-skill"

    def _resolve_scan_path(self, config: dict) -> Path:
        """从配置解析扫描路径

        支持两种格式：
        - file:///path/to/skills
        - /path/to/skills
        """
        url = config.get("url", "")
        if url.startswith("file://"):
            parsed = urlparse(url)
            return Path(parsed.path)
        return Path(url)

    async def scan_skills(
        self, config: dict, scan_path: str | None = None
    ) -> list[RemotePluginInfo]:
        """扫描本地目录中的所有 Skill

        Args:
            config: 市场配置
            scan_path: 可选扫描路径，未指定时从 config['url'] 解析

        Returns:
            list[RemotePluginInfo]: 扫描到的 Skill 列表
        """
        if scan_path:
            scan_dir = Path(scan_path)
        else:
            scan_dir = self._resolve_scan_path(config)

        if not scan_dir.exists():
            logger.warning(f"扫描目录不存在: {scan_dir}")
            return []

        skills: list[RemotePluginInfo] = []
        for skill_file in scan_dir.rglob("SKILL.md"):
            try:
                skill_info = await self._parse_skill_file(skill_file)
                skills.append(skill_info)
            except ValueError as e:
                logger.warning(f"解析 Skill 文件失败: {skill_file}, 错误: {e}")

        return skills

    async def _parse_skill_file(self, skill_file: Path) -> RemotePluginInfo:
        """解析 SKILL.md 文件

        文件格式：YAML front matter + Markdown 正文

        Args:
            skill_file: SKILL.md 文件路径

        Returns:
            RemotePluginInfo: Skill 信息

        Raises:
            ValueError: 文件格式无效
        """
        content = skill_file.read_text(encoding="utf-8")

        if not content.startswith("---"):
            raise ValueError(f"无效的 Skill 文件格式: {skill_file}")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"无效的 Skill 文件格式: {skill_file}")

        metadata = yaml.safe_load(parts[1])
        if not metadata or "name" not in metadata:
            raise ValueError(f"Skill 文件缺少 name 字段: {skill_file}")

        name = metadata["name"]
        author = metadata.get("author", "local")
        version = metadata.get("version", "1.0.0")

        # 提取 Hermes 风格的标签
        hermes_meta = metadata.get("metadata", {}).get("hermes", {})
        tags = hermes_meta.get("tags", [])

        return RemotePluginInfo(
            plugin_id=f"{author}/{name}",
            name=name,
            description=metadata.get("description", ""),
            version=version,
            author=author,
            icon=metadata.get("icon"),
            plugin_type="skill",
            skill_type="knowledge",  # 本地扫描默认为知识文档
            tags=tags,
            downloads=None,
            manifest_url=None,
            download_url=f"file://{skill_file.parent}",
            created_at=None,
            updated_at=None,
        )

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试本地目录可访问性"""
        try:
            scan_dir = self._resolve_scan_path(config)
            if not scan_dir.exists():
                return MarketplaceTestResult(
                    success=False, message=f"目录不存在: {scan_dir}"
                )

            # 统计 Skill 文件数量
            skill_count = len(list(scan_dir.rglob("SKILL.md")))
            return MarketplaceTestResult(
                success=True,
                message="连接成功",
                plugin_count=skill_count,
            )
        except Exception as e:
            logger.error(f"测试本地 Skill 目录失败: {e}")
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取本地 Skill 列表（支持关键词过滤和分页）"""
        all_skills = await self.scan_skills(config)

        # 关键词过滤
        if keyword:
            keyword_lower = keyword.lower()
            all_skills = [
                s for s in all_skills
                if keyword_lower in s.name.lower()
                or (s.description and keyword_lower in s.description.lower())
                or any(keyword_lower in t.lower() for t in s.tags)
            ]

        # 分页
        total = len(all_skills)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_skills[start:end]

        return paginated, total

    async def get_plugin(
        self, config: dict, plugin_id: str
    ) -> RemotePluginInfo | None:
        """获取单个 Skill 详情"""
        all_skills = await self.scan_skills(config)
        for skill in all_skills:
            if skill.plugin_id == plugin_id:
                return skill
        return None

    async def download_plugin(
        self, config: dict, plugin_id: str, version: str | None = None
    ) -> tuple[bytes, str]:
        """下载 Skill 包（打包为 ZIP）"""
        import hashlib
        import io
        import zipfile

        skill_info = await self.get_plugin(config, plugin_id)
        if not skill_info:
            raise ValueError(f"Skill 不存在: {plugin_id}")

        # 从 download_url 解析本地路径
        skill_path_str = skill_info.download_url.replace("file://", "")
        skill_path = Path(skill_path_str)

        # 打包为 ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in skill_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_path.parent)
                    zf.write(file_path, arcname)

        zip_data = zip_buffer.getvalue()
        checksum = hashlib.sha256(zip_data).hexdigest()
        return zip_data, checksum

    async def check_updates(
        self, config: dict, plugins: Sequence[dict]
    ) -> Sequence[PluginUpdateInfo]:
        """检查 Skill 更新（本地 Skill 不支持更新检查，返回空列表）"""
        return []
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/test_local_skill_adapter.py -v`

预期：6 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/tenant/services/marketplace/adapters/local_skill_adapter.py tests/tenant/unit/marketplace/test_local_skill_adapter.py
git commit -m "feat(tenant): 实现本地文件扫描适配器

支持从本地目录扫描 SKILL.md 文件，解析 YAML front matter 获取 Skill 元数据

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 8：Gateway 注册新适配器并新增 Skill 同步方法

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/gateway.py`
- 修改：`server/python/src/tenant/services/marketplace/adapters/__init__.py`
- 测试：无（由集成测试覆盖）

- [ ] **步骤 1：更新适配器 __init__.py 导出**

修改 `server/python/src/tenant/services/marketplace/adapters/__init__.py`，新增三个适配器的导入：

```python
"""插件市场适配器"""

from tenant.services.marketplace.adapters.dify_adapter import DifyAdapter
from tenant.services.marketplace.adapters.modelscope_adapter import ModelScopeAdapter
from tenant.services.marketplace.adapters.agentskills_adapter import AgentSkillsAdapter
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter

__all__ = [
    "DifyAdapter",
    "ModelScopeAdapter",
    "AgentSkillsAdapter",
    "ModelScopeSkillAdapter",
    "LocalSkillAdapter",
]
```

- [ ] **步骤 2：在 Gateway 中注册新适配器**

修改 `server/python/src/tenant/services/marketplace/gateway.py`，更新导入和 `_adapters` 字典：

在文件顶部导入区域新增：

```python
from tenant.services.marketplace.adapters.agentskills_adapter import AgentSkillsAdapter
from tenant.services.marketplace.adapters.local_skill_adapter import LocalSkillAdapter
from tenant.services.marketplace.adapters.modelscope_skill_adapter import (
    ModelScopeSkillAdapter,
)
```

修改 `_adapters` 字典（第 29-32 行）：

```python
    _adapters: dict[str, type] = {
        "dify": DifyAdapter,
        "modelscope": ModelScopeAdapter,
        "agentskills": AgentSkillsAdapter,
        "modelscope-skill": ModelScopeSkillAdapter,
        "local-skill": LocalSkillAdapter,
    }
```

- [ ] **步骤 3：新增 sync_skill_from_marketplace 方法**

在 `server/python/src/tenant/services/marketplace/gateway.py` 的 `MarketplaceGateway` 类中，在 `apply_update` 方法后新增以下方法：

```python
    async def sync_skill_from_marketplace(
        self,
        session: AsyncSession,
        marketplace_id: str,
        skill_id: str,
    ) -> TenantPluginDefinition:
        """从市场同步单个 Skill 到本地

        Args:
            session: 数据库会话
            marketplace_id: 市场 ID
            skill_id: Skill ID（格式：author/name）

        Returns:
            TenantPluginDefinition: 创建或更新的插件定义

        Raises:
            ValueError: 市场不存在或 Skill 不存在
        """
        from tenant.services.plugin_storage_service import plugin_storage_service

        marketplace = await self.get_marketplace(session, marketplace_id)
        if not marketplace:
            raise ValueError(f"市场不存在: {marketplace_id}")
        if not marketplace.is_enabled:
            raise ValueError(f"市场已禁用: {marketplace.name}")

        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)

        # 1. 获取 Skill 元数据
        skill_info = await adapter.get_plugin(config, skill_id)
        if not skill_info:
            raise ValueError(f"Skill 不存在: {skill_id}")

        # 2. 下载 Skill 包
        skill_data, checksum = await adapter.download_plugin(
            config, skill_id, version=skill_info.version
        )

        # 3. 上传到 MinIO
        storage_key = await plugin_storage_service.upload_skill_package(
            skill_id=skill_id,
            skill_data=skill_data,
            checksum=checksum,
            version=skill_info.version,
        )

        # 4. 构建 declaration
        skill_runtime = "none" if skill_info.skill_type == "knowledge" else "sandbox"
        declaration = {
            "skill": {
                "skill_type": skill_info.skill_type or "knowledge",
                "runtime": skill_runtime,
            },
            "metadata": {
                "name": skill_info.name,
                "description": skill_info.description,
                "version": skill_info.version,
                "author": skill_info.author,
                "tags": skill_info.tags,
            },
        }

        # 5. 检查是否已存在
        existing = await session.execute(
            select(TenantPluginDefinition).where(
                TenantPluginDefinition.plugin_id == skill_id,
                TenantPluginDefinition.is_enabled == True,  # noqa: E712
            )
        )
        existing_def = existing.scalar_one_or_none()

        if existing_def:
            # 更新现有记录
            existing_def.declaration = declaration
            existing_def.skill_type = skill_info.skill_type
            existing_def.runtime_type = skill_runtime
            existing_def.remote_version = skill_info.version
            existing_def.local_version = skill_info.version
            existing_def.update_available = False
            existing_def.source_type = "remote"
            existing_def.marketplace_id = marketplace_id
            await session.flush()
            return existing_def

        # 6. 创建新记录
        new_def = TenantPluginDefinition(
            plugin_id=skill_id,
            plugin_unique_identifier=f"{skill_id}:{skill_info.version}@{checksum}",
            declaration=declaration,
            refers=0,
            install_type="remote",
            manifest_type="skill",
            skill_type=skill_info.skill_type,
            runtime_type=skill_runtime,
            marketplace_id=marketplace_id,
            remote_plugin_id=skill_id,
            remote_version=skill_info.version,
            local_version=skill_info.version,
            source_type="remote",
        )
        session.add(new_def)
        await session.flush()
        return new_def
```

- [ ] **步骤 4：验证 Gateway 修改正确**

运行：`cd server/python && uv run python -c "from tenant.services.marketplace.gateway import marketplace_gateway; print(list(marketplace_gateway._adapters.keys()))"`

预期：输出 `['dify', 'modelscope', 'agentskills', 'modelscope-skill', 'local-skill']`

- [ ] **步骤 5：运行现有测试确认无回归**

运行：`cd server/python && uv run pytest tests/tenant/ -v -k "marketplace or gateway" --no-header 2>&1 | tail -20`

预期：现有测试全部通过

- [ ] **步骤 6：Commit**

```bash
cd server/python
git add src/tenant/services/marketplace/gateway.py src/tenant/services/marketplace/adapters/__init__.py
git commit -m "feat(tenant): Gateway 注册 Skill 市场适配器

新增 sync_skill_from_marketplace 方法，支持从市场同步 Skill 到本地
注册 agentskills、modelscope-skill、local-skill 三种适配器

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 9：Skill 同步流程集成测试

**文件：**
- 创建：`server/python/tests/tenant/integration/test_skill_sync_flow.py`

- [ ] **步骤 1：编写集成测试**

创建 `server/python/tests/tenant/integration/test_skill_sync_flow.py`：

```python
"""Skill 同步流程集成测试

测试从市场适配器到存储服务到数据库定义的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from tenant.services.marketplace.gateway import MarketplaceGateway
from tenant.models.plugin_marketplace import TenantPluginMarketplace
from tenant.models.plugin_definition import TenantPluginDefinition


class TestSkillSyncFlow:
    """Skill 同步流程集成测试"""

    @pytest.fixture
    def gateway(self):
        return MarketplaceGateway()

    @pytest.fixture
    def mock_marketplace(self):
        """模拟 AgentSkills 市场"""
        marketplace = MagicMock(spec=TenantPluginMarketplace)
        marketplace.id = "market-001"
        marketplace.name = "AgentSkills Hub"
        marketplace.type = "agentskills"
        marketplace.url = "https://agentskills.io"
        marketplace.auth_type = "none"
        marketplace.auth_config = {}
        marketplace.is_enabled = True
        return marketplace

    @pytest.mark.asyncio
    async def test_sync_skill_creates_definition(
        self, gateway, mock_marketplace, mock_db_session
    ):
        """测试同步 Skill 创建插件定义"""
        # Mock 适配器返回的 Skill 信息
        mock_skill_info = MagicMock()
        mock_skill_info.plugin_id = "community/airtable"
        mock_skill_info.name = "airtable"
        mock_skill_info.description = "Airtable REST API"
        mock_skill_info.version = "1.1.0"
        mock_skill_info.author = "community"
        mock_skill_info.skill_type = "knowledge"
        mock_skill_info.tags = ["Airtable", "Productivity"]

        # Mock 适配器
        mock_adapter = AsyncMock()
        mock_adapter.get_plugin.return_value = mock_skill_info
        mock_adapter.download_plugin.return_value = (b"skill zip data", "checksum123")

        # Mock 存储服务
        with patch(
            "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
            new_callable=AsyncMock,
            return_value="skills/global/community/airtable/1.1.0/skill.zip",
        ):
            # Mock 数据库查询（无现有记录）
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db_session.execute.return_value = mock_result

            # 执行同步
            with patch.object(
                gateway, "_get_adapter", return_value=mock_adapter
            ):
                result = await gateway.sync_skill_from_marketplace(
                    mock_db_session, "market-001", "community/airtable"
                )

        # 验证结果
        assert result.plugin_id == "community/airtable"
        assert result.skill_type == "knowledge"
        assert result.runtime_type == "none"
        assert result.manifest_type == "skill"
        assert result.source_type == "remote"

        # 验证 declaration 内容
        assert result.declaration["skill"]["skill_type"] == "knowledge"
        assert result.declaration["skill"]["runtime"] == "none"

        # 验证数据库操作
        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_skill_updates_existing_definition(
        self, gateway, mock_marketplace, mock_db_session
    ):
        """测试同步 Skill 更新现有插件定义"""
        # Mock 现有插件定义
        existing_def = MagicMock(spec=TenantPluginDefinition)
        existing_def.plugin_id = "community/airtable"
        existing_def.version = "1.0.0"

        # Mock 适配器
        mock_skill_info = MagicMock()
        mock_skill_info.plugin_id = "community/airtable"
        mock_skill_info.name = "airtable"
        mock_skill_info.description = "Airtable REST API v2"
        mock_skill_info.version = "1.1.0"
        mock_skill_info.author = "community"
        mock_skill_info.skill_type = "knowledge"
        mock_skill_info.tags = ["Airtable"]

        mock_adapter = AsyncMock()
        mock_adapter.get_plugin.return_value = mock_skill_info
        mock_adapter.download_plugin.return_value = (b"new skill data", "newchecksum")

        with patch(
            "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
            new_callable=AsyncMock,
            return_value="skills/global/community/airtable/1.1.0/skill.zip",
        ):
            # Mock 数据库查询（返回现有记录）
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing_def
            mock_db_session.execute.return_value = mock_result

            with patch.object(gateway, "_get_adapter", return_value=mock_adapter):
                result = await gateway.sync_skill_from_marketplace(
                    mock_db_session, "market-001", "community/airtable"
                )

        # 验证更新现有记录（未调用 add）
        assert result == existing_def
        mock_db_session.add.assert_not_called()
        mock_db_session.flush.assert_called()

        # 验证字段更新
        assert existing_def.remote_version == "1.1.0"
        assert existing_def.local_version == "1.1.0"
        assert existing_def.skill_type == "knowledge"
        assert existing_def.runtime_type == "none"

    @pytest.mark.asyncio
    async def test_sync_skill_with_script_type(self, gateway, mock_db_session):
        """测试同步脚本类型 Skill"""
        mock_skill_info = MagicMock()
        mock_skill_info.plugin_id = "test/scraper"
        mock_skill_info.name = "scraper"
        mock_skill_info.description = "Web scraper"
        mock_skill_info.version = "1.0.0"
        mock_skill_info.author = "test"
        mock_skill_info.skill_type = "script"
        mock_skill_info.tags = ["scraper"]

        mock_adapter = AsyncMock()
        mock_adapter.get_plugin.return_value = mock_skill_info
        mock_adapter.download_plugin.return_value = (b"script data", "scriptchecksum")

        with patch(
            "tenant.services.plugin_storage_service.plugin_storage_service.upload_skill_package",
            new_callable=AsyncMock,
            return_value="skills/global/test/scraper/1.0.0/skill.zip",
        ):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db_session.execute.return_value = mock_result

            with patch.object(gateway, "_get_adapter", return_value=mock_adapter):
                result = await gateway.sync_skill_from_marketplace(
                    mock_db_session, "market-001", "test/scraper"
                )

        # 验证脚本类型使用 sandbox 运行时
        assert result.skill_type == "script"
        assert result.runtime_type == "sandbox"
        assert result.declaration["skill"]["runtime"] == "sandbox"

    @pytest.mark.asyncio
    async def test_sync_skill_marketplace_not_found(self, gateway, mock_db_session):
        """测试市场不存在时的错误处理"""
        mock_db_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        with pytest.raises(ValueError, match="市场不存在"):
            await gateway.sync_skill_from_marketplace(
                mock_db_session, "nonexistent-market", "some/skill"
            )

    @pytest.mark.asyncio
    async def test_sync_skill_skill_not_found(self, gateway, mock_marketplace, mock_db_session):
        """测试 Skill 不存在时的错误处理"""
        mock_adapter = AsyncMock()
        mock_adapter.get_plugin.return_value = None

        with patch.object(gateway, "_get_adapter", return_value=mock_adapter):
            with pytest.raises(ValueError, match="Skill 不存在"):
                await gateway.sync_skill_from_marketplace(
                    mock_db_session, "market-001", "nonexistent/skill"
                )
```

- [ ] **步骤 2：确认 mock_db_session fixture 可用**

运行：`cd server/python && cat tests/conftest.py 2>/dev/null | grep -A 10 "mock_db_session" || echo "需要创建 fixture"`

如果 fixture 不存在，在测试文件顶部添加：

```python
@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    session = AsyncMock()
    # Mock get_marketplace 返回的市场
    return session
```

并修改测试中对 `mock_db_session.execute` 的 Mock，确保 `get_marketplace` 能返回模拟市场。具体实现时根据现有 conftest.py 调整。

- [ ] **步骤 3：运行集成测试**

运行：`cd server/python && uv run pytest tests/tenant/integration/test_skill_sync_flow.py -v`

预期：5 个测试通过（如果 fixture 配置正确）

如果因 fixture 问题失败，根据实际 conftest.py 调整 mock 策略。

- [ ] **步骤 4：运行全部新增测试确认整体通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/marketplace/ tests/tenant/unit/services/test_plugin_storage_skill.py tests/tenant/integration/test_skill_sync_flow.py -v`

预期：所有测试通过

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add tests/tenant/integration/test_skill_sync_flow.py
git commit -m "test(tenant): 新增 Skill 同步流程集成测试

覆盖创建定义、更新定义、脚本类型、错误处理等场景

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 自检

### 规格覆盖度

对照设计规格 `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md` 检查：

| 规格章节 | 覆盖任务 | 状态 |
|---------|---------|------|
| 3.1 Plugin Definition 扩展 | 任务 2 | ✅ |
| 3.2 Skill 配置结构 | 任务 8（declaration 构建） | ✅ |
| 3.4 数据库迁移 | 任务 3 | ✅ |
| 4.1 适配器协议扩展 | 任务 1 | ✅ |
| 4.2 AgentSkills 适配器 | 任务 5 | ✅ |
| 4.3 ModelScope Skill 适配器 | 任务 6 | ✅ |
| 4.4 本地文件扫描适配器 | 任务 7 | ✅ |
| 4.5 Gateway 服务扩展 | 任务 8 | ✅ |
| 8.1 MinIO 存储结构 | 任务 4 | ✅ |
| 8.2 存储服务扩展 | 任务 4 | ✅ |

**未覆盖（属于后续计划）：**
- 第 5 章运行时实现（计划 2）
- 第 6 章 LangChain 集成（计划 2）
- 第 7 章前端集成（计划 3）
- 第 8.3-8.6 错误处理/事件监听器/监控（计划 2）

### 占位符扫描

✅ 无"待定"、"TODO"、"后续实现"占位符
✅ 所有代码步骤包含完整代码
✅ 所有测试步骤包含实际测试代码
✅ 无"类似任务 N"引用

### 类型一致性

- `RemotePluginInfo` 字段在任务 1 定义后，任务 5/6/7 一致使用
- `skill_type` 枚举值 `knowledge | script` 全文一致
- `runtime_type` 枚举值 `none | sandbox | local` 全文一致
- 市场类型 `agentskills | modelscope-skill | local-skill` 在任务 5/6/7/8 一致
- `upload_skill_package` 方法签名在任务 4 定义，任务 8 调用一致

### 修复记录

无需修复，计划与规格一致。

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-07-06-skills-marketplace-backend-foundation.md`。

**本计划覆盖范围：** Phase 1-3（数据模型 + 存储服务 + 市场适配器），共 9 个任务，能独立产出可测试的后端基础功能。

**后续计划：**
- 计划 2：运行时与 LangChain 集成（Phase 4-6）
- 计划 3：前端集成（Phase 7）

**两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**
