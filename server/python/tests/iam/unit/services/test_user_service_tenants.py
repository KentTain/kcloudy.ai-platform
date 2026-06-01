"""
UserService 租户相关方法测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from iam.services.user_service import UserService


class TestGetUserTenantsDetail:
    """get_user_tenants_detail 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_list_of_user_tenant_info(self):
        """返回用户租户详细信息列表"""
        # 模拟 UserTenant 查询结果
        mock_user_tenant_1 = MagicMock()
        mock_user_tenant_1.tenant_id = "tenant-1"
        mock_user_tenant_1.role = "admin"
        mock_user_tenant_1.is_default = True

        mock_user_tenant_2 = MagicMock()
        mock_user_tenant_2.tenant_id = "tenant-2"
        mock_user_tenant_2.role = "member"
        mock_user_tenant_2.is_default = False

        with patch("iam.services.user_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                mock_user_tenant_1,
                mock_user_tenant_2,
            ]
            mock_session_context.execute.return_value = mock_result

            result = await UserService.get_user_tenants_detail("user-1")

        assert len(result) == 2
        assert result[0]["tenant_id"] == "tenant-1"
        assert result[0]["role"] == "admin"
        assert result[0]["is_default"] is True
        assert result[1]["tenant_id"] == "tenant-2"
        assert result[1]["role"] == "member"
        assert result[1]["is_default"] is False

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_tenants(self):
        """用户无租户时返回空列表"""
        with patch("iam.services.user_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await UserService.get_user_tenants_detail("user-no-tenants")

        assert result == []
