"""回收站服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.models.enums import ResourceType
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

    async def test_restore_item_parent_exists_no_conflict(self):
        """恢复回收站项目 - 原父资源存在，无名称冲突"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r1"
        mock_item.resource_id = "doc-1"
        mock_item.resource_type = ResourceType.DOCUMENT
        mock_item.original_parent_id = "folder-1"
        mock_item.status = "in_recycle"

        # _get_item 返回
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = mock_item

        # _check_parent_exists 返回 True（文件夹存在）
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = MagicMock()  # folder exists

        # _restore_with_name_check -> get doc
        doc_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "doc-1"
        mock_doc.name = "test.pdf"
        mock_doc.folder_id = "folder-1"
        doc_result.scalar_one_or_none.return_value = mock_doc

        # _check_doc_name_conflict -> no conflict
        name_conflict_result = MagicMock()
        name_conflict_result.scalar.return_value = 0

        session.execute = AsyncMock(
            side_effect=[get_result, parent_result, doc_result, name_conflict_result]
        )

        with patch("document.services.recycle_service.get_user_id", return_value="u1"):
            await RecycleService.restore(session, item_id="r1")

        assert mock_item.status == "restored"
        assert mock_item.restored_by == "u1"
        # 名称未被修改
        assert mock_doc.name == "test.pdf"

    async def test_restore_item_parent_not_exists_restore_to_root(self):
        """恢复回收站项目 - 原父资源不存在，恢复到库根"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r1"
        mock_item.resource_id = "doc-1"
        mock_item.resource_type = ResourceType.DOCUMENT
        mock_item.original_parent_id = "folder-deleted"
        mock_item.status = "in_recycle"

        # _get_item 返回
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = mock_item

        # _check_parent_exists 返回 None（文件夹不存在）
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = None

        # _restore_to_root -> get doc
        doc_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "doc-1"
        mock_doc.folder_id = "folder-deleted"
        doc_result.scalar_one_or_none.return_value = mock_doc

        session.execute = AsyncMock(
            side_effect=[get_result, parent_result, doc_result]
        )

        with patch("document.services.recycle_service.get_user_id", return_value="u1"):
            await RecycleService.restore(session, item_id="r1")

        assert mock_item.status == "restored"
        # folder_id 被设为 None（库根）
        assert mock_doc.folder_id is None

    async def test_restore_item_name_conflict_append_restored(self):
        """恢复回收站项目 - 名称冲突，追加 '_restored' 后缀"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r1"
        mock_item.resource_id = "doc-1"
        mock_item.resource_type = ResourceType.DOCUMENT
        mock_item.original_parent_id = "folder-1"
        mock_item.status = "in_recycle"

        # _get_item 返回
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = mock_item

        # _check_parent_exists 返回 True
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = MagicMock()

        # _restore_with_name_check -> get doc
        doc_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "doc-1"
        mock_doc.name = "test.pdf"
        mock_doc.folder_id = "folder-1"
        doc_result.scalar_one_or_none.return_value = mock_doc

        # _check_doc_name_conflict -> conflict exists
        name_conflict_result = MagicMock()
        name_conflict_result.scalar.return_value = 1

        session.execute = AsyncMock(
            side_effect=[get_result, parent_result, doc_result, name_conflict_result]
        )

        with patch("document.services.recycle_service.get_user_id", return_value="u1"):
            await RecycleService.restore(session, item_id="r1")

        assert mock_item.status == "restored"
        # 名称追加了 '_restored' 后缀
        assert mock_doc.name == "test.pdf_restored"

    async def test_restore_folder_parent_not_exists(self):
        """恢复文件夹 - 原父文件夹不存在，恢复到库根"""
        session = AsyncMock(spec=AsyncSession)
        mock_item = MagicMock(spec=[])
        mock_item.id = "r2"
        mock_item.resource_id = "folder-1"
        mock_item.resource_type = ResourceType.FOLDER
        mock_item.original_parent_id = "parent-folder-deleted"
        mock_item.status = "in_recycle"

        # _get_item 返回
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = mock_item

        # _check_parent_exists 返回 None
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = None

        # _restore_to_root -> get folder
        folder_result = MagicMock()
        mock_folder = MagicMock()
        mock_folder.id = "folder-1"
        mock_folder.parent_id = "parent-folder-deleted"
        folder_result.scalar_one_or_none.return_value = mock_folder

        session.execute = AsyncMock(
            side_effect=[get_result, parent_result, folder_result]
        )

        with patch("document.services.recycle_service.get_user_id", return_value="u1"):
            await RecycleService.restore(session, item_id="r2")

        assert mock_item.status == "restored"
        # parent_id 被设为 "root"（库根）
        assert mock_folder.parent_id == "root"

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
