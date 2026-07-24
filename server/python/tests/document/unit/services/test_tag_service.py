"""标签服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.tag_service import TagService


@pytest.mark.asyncio
class TestTagService:
    async def test_create_tag(self):
        """创建标签"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.tag_service.get_tenant_id", return_value="t1"), \
             patch("document.services.tag_service.get_user_id", return_value="u1"):
            tag = await TagService.create(session, name="Python", group_id="g1", color="#336699")
        assert tag is not None
        session.add.assert_called()

    async def test_get_by_id(self):
        """按 ID 查询标签"""
        session = AsyncMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=[])
        mock_tag.id = "tag-1"
        mock_tag.name = "Python"
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_tag
        session.execute = AsyncMock(return_value=result)
        tag = await TagService.get_by_id(session, tag_id="tag-1")
        assert tag is not None
        assert tag.id == "tag-1"

    async def test_delete_tag_with_doc_count_reject(self):
        """标签已被文档引用时拒绝删除"""
        session = AsyncMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=[])
        mock_tag.id = "tag-1"
        mock_tag.doc_count = 5
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_tag
        session.execute = AsyncMock(return_value=result)
        with pytest.raises(ValueError, match="已被文档引用"):
            await TagService.delete(session, tag_id="tag-1")

    async def test_delete_tag_with_persona_reject(self):
        """标签被人设引用时拒绝删除"""
        session = AsyncMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=[])
        mock_tag.id = "tag-1"
        mock_tag.doc_count = 0
        mock_tag.persona_id = "p1"
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_tag
        session.execute = AsyncMock(return_value=result)
        with pytest.raises(ValueError, match="被人设引用"):
            await TagService.delete(session, tag_id="tag-1")

    async def test_delete_tag_success(self):
        """无引用时删除标签成功"""
        session = AsyncMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=[])
        mock_tag.id = "tag-1"
        mock_tag.doc_count = 0
        mock_tag.persona_id = None
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_tag
        session.execute = AsyncMock(return_value=result)
        # Should not raise
        await TagService.delete(session, tag_id="tag-1")

    async def test_list_tags_by_group(self):
        """按分组查询标签列表"""
        session = AsyncMock(spec=AsyncSession)
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        mock_tag = MagicMock(spec=[])
        mock_tag.name = "Python"
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_tag]
        session.execute = AsyncMock(side_effect=[count_result, list_result])
        items, total = await TagService.list_tags(session, tenant_id="t1", group_id="g1")
        assert total == 1
        assert len(items) == 1
