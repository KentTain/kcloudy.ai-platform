"""Skill 存储服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tenant.services.plugin import PluginStorageService


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
            "test-bucket",
            "skills/global/community/airtable/1.1.0/skill.zip",
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
