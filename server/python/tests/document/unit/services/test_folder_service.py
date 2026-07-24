"""文件夹服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.folder_service import FolderService


@pytest.mark.asyncio
class TestFolderService:
    async def test_create_folder_uses_treenode(self):
        """创建文件夹使用 TreeNodeMixin.create_node"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.folder_service.Folder.create_node", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock(id="f1")
            folder = await FolderService.create(
                session, library_id="lib-1", name="子文件夹", parent_id="root",
            )
            mock_create.assert_called_once()

    async def test_move_folder_detects_cycle(self):
        """移动文件夹检测循环引用"""
        session = AsyncMock(spec=AsyncSession)

        # 当前节点
        mock_current = MagicMock()
        mock_current.id = "f1"
        mock_current.parent_ids = "root,"

        # 目标父节点是当前节点的子孙
        mock_target = MagicMock()
        mock_target.id = "f2"
        mock_target.parent_ids = "root,f1,f2,"

        current_result = MagicMock()
        current_result.scalar_one_or_none.return_value = mock_current
        target_result = MagicMock()
        target_result.scalar_one_or_none.return_value = mock_target

        # first call for target, second for current
        session.execute = AsyncMock(side_effect=[target_result, current_result])

        with pytest.raises(ValueError, match="循环引用"):
            await FolderService.move(session, folder_id="f1", new_parent_id="f2")

    async def test_rename_folder(self):
        """重命名文件夹"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.folder_service.Folder.update_node", new_callable=AsyncMock) as mock_update:
            mock_folder = MagicMock(spec=[])
            mock_folder.id = "f1"
            mock_folder.name = "新名称"
            mock_update.return_value = mock_folder
            folder = await FolderService.rename(session, folder_id="f1", name="新名称")
            mock_update.assert_called_once()
            assert folder.name == "新名称"

    async def test_delete_folder(self):
        """删除文件夹（软删除，创建回收站记录）"""
        session = AsyncMock(spec=AsyncSession)

        mock_folder = MagicMock()
        mock_folder.id = "f1"
        mock_folder.library_id = "lib-1"
        mock_folder.parent_ids = "root,"
        mock_folder.tree_names = "测试文件夹"
        mock_folder.is_root_node.return_value = False
        mock_folder.parent_id = "root"
        mock_folder.descendant_parent_ids_prefix.return_value = "root,f1,"

        async def mock_flush():
            """模拟 flush 后为 RecycleItem 赋予 id"""
            for call_args in session.add.call_args_list:
                item = call_args[0][0]
                if hasattr(item, "resource_type"):
                    item.id = "recycle-1"

        with patch("document.services.folder_service.Folder.one_node", new_callable=AsyncMock) as mock_one_node, \
             patch("document.services.folder_service.get_tenant_id", return_value="t1"), \
             patch("document.services.folder_service.get_user_id", return_value="u1"):
            mock_one_node.return_value = mock_folder
            session.execute = AsyncMock()
            session.add = MagicMock()
            session.flush = mock_flush
            recycle_id = await FolderService.delete(session, folder_id="f1")
            assert recycle_id == "recycle-1"
            mock_one_node.assert_called_once()
            assert session.add.call_count == 2

    async def test_list_tree(self):
        """获取文件夹树"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.folder_service.Folder.list_nodes", new_callable=AsyncMock) as mock_list, \
             patch("document.services.folder_service.Folder.build_tree") as mock_build:
            mock_list.return_value = []
            mock_build.return_value = [{"id": "f1", "children": []}]
            tree = await FolderService.list_tree(session, library_id="lib-1")
            mock_list.assert_called_once()
            mock_build.assert_called_once()
            assert len(tree) == 1
