"""回收站服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.recycle_service import RecycleService


@pytest.mark.asyncio
class TestRecycleService:
    async def test_list_recycle_items(self):
        """查看回收站列表"""
        session = AsyncMock(spec=AsyncSession)
        count_result = MagicMock()
        count_result.scalar.return_value = 2
        item1 = MagicMock(spec=[])
        item1.id = "r1"
        item2 = MagicMock(spec=[])
        item2.id = "r2"
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [item1, item2]
        session.execute = AsyncMock(side_effect=[count_result, list_result])
        items, total = await RecycleService.list_items(session, library_id="lib-1")
        assert total == 2
        assert len(items) == 2

    async def test_restore_item(self):
        """恢复回收站项目"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r1"
        mock_item.resource_id = "doc-1"
        mock_item.original_parent_id = "folder-1"
        mock_item.status = "in_recycle"
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_item
        session.execute = AsyncMock(return_value=result)
        with patch("document.services.recycle_service.get_user_id", return_value="u1"):
            await RecycleService.restore(session, item_id="r1")
        assert mock_item.status == "restored"
        assert mock_item.restored_by == "u1"

    async def test_purge_item(self):
        """永久删除回收站项目"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r1"
        mock_item.status = "in_recycle"
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_item
        session.execute = AsyncMock(return_value=result)
        await RecycleService.purge(session, item_id="r1")
        assert mock_item.status == "purged"

    async def test_clear_all(self):
        """清空回收站"""
        session = AsyncMock(spec=AsyncSession)
        mock_item1 = MagicMock(spec=[])
        mock_item1.id = "r1"
        mock_item1.status = "in_recycle"
        mock_item2 = MagicMock(spec=[])
        mock_item2.id = "r2"
        mock_item2.status = "in_recycle"
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_item1, mock_item2]
        session.execute = AsyncMock(return_value=list_result)
        count = await RecycleService.clear(session, library_id="lib-1")
        assert count == 2
        assert mock_item1.status == "purged"
        assert mock_item2.status == "purged"

    async def test_restore_item_not_found(self):
        """恢复不存在的项目抛出异常"""
        session = AsyncMock(spec=AsyncSession)
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)
        with pytest.raises(ValueError, match="回收站项目不存在"):
            await RecycleService.restore(session, item_id="r-999")
