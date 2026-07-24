"""文档库服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.library_service import LibraryService


@pytest.mark.asyncio
class TestLibraryService:
    async def test_create_personal_library_auto_owner(self):
        """创建个人文档库，创建者自动成为 owner"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.LibraryService.has_personal_library", new_callable=AsyncMock, return_value=False):
            lib = await LibraryService.create(
                session, library_type="personal", code="personal-u1", name="我的文档库",
            )
        assert lib.owner_id == "u1"
        session.add.assert_called()

    async def test_create_personal_library_reject_if_exists(self):
        """已存在个人文档库时拒绝创建"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.LibraryService.has_personal_library", new_callable=AsyncMock, return_value=True):
            with pytest.raises(ValueError, match="个人文档库"):
                await LibraryService.create(
                    session, library_type="personal", code="personal-u1", name="我的文档库",
                )

    async def test_create_team_library_reject_duplicate_name(self):
        """团队文档库名称重复拒绝"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.LibraryService.has_team_library_name", new_callable=AsyncMock, return_value=True):
            with pytest.raises(ValueError, match="名称已存在"):
                await LibraryService.create(
                    session, library_type="team", code="team-rd", name="研发库",
                )

    async def test_delete_library_soft_delete(self):
        """删除文档库为软删除（enabled=False）"""
        session = AsyncMock(spec=AsyncSession)
        mock_lib = MagicMock()
        mock_lib.id = "lib-1"
        mock_lib.enabled = True
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_lib
        session.execute = AsyncMock(return_value=result)
        await LibraryService.soft_delete(session, library_id="lib-1")
        assert mock_lib.enabled is False

    async def test_delete_library_not_found(self):
        """删除不存在的文档库抛出异常"""
        session = AsyncMock(spec=AsyncSession)
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)
        with pytest.raises(ValueError, match="文档库不存在"):
            await LibraryService.soft_delete(session, library_id="lib-999")

    async def test_get_by_id(self):
        """按 ID 查询文档库"""
        session = AsyncMock(spec=AsyncSession)
        mock_lib = MagicMock()
        mock_lib.id = "lib-1"
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_lib
        session.execute = AsyncMock(return_value=result)
        lib = await LibraryService.get_by_id(session, library_id="lib-1")
        assert lib is not None
        assert lib.id == "lib-1"

    async def test_list_libraries(self):
        """分页查询文档库列表"""
        session = AsyncMock(spec=AsyncSession)
        # count query
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        # list query
        mock_lib = MagicMock()
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_lib]

        session.execute = AsyncMock(side_effect=[count_result, list_result])
        items, total = await LibraryService.list_libraries(session, tenant_id="t1")
        assert total == 1
        assert len(items) == 1
