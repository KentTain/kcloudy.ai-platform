"""
Tenant Console 控制器单元测试

测试用户端租户控制器的参数校验和错误处理逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
class TestListUserTenants:
    """list_user_tenants 控制器测试"""

    async def test_list_user_tenants_success(self, mock_session):
        """成功获取用户租户列表"""
        from tenant.controllers.console.tenant_controller import list_user_tenants

        # Mock IAM client 返回用户租户关联
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-1"
        mock_user_tenant.role = "owner"
        mock_user_tenant.is_default = True

        # Mock TenantService 返回租户信息
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "测试租户"
        mock_tenant.code = "TEST001"
        mock_tenant.status = "active"

        with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
            mock_iam_client = MagicMock()
            mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
            mock_get_iam.return_value = mock_iam_client

            with patch(
                "tenant.controllers.console.tenant_controller.TenantService.get_tenants_batch"
            ) as mock_get_tenants:
                mock_get_tenants.return_value = [mock_tenant]

                # 执行测试
                result = await list_user_tenants(user_id="user-1", session=mock_session)

                # 验证返回对象
                assert result.status_code == 200
                import json

                data = json.loads(result.body.decode())
                assert data["code"] == 200
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "tenant-1"
                assert data["data"][0]["name"] == "测试租户"
                assert data["data"][0]["role"] == "owner"
                assert data["data"][0]["is_default"] is True

    async def test_list_user_tenants_empty(self, mock_session):
        """用户不属于任何租户时返回空列表"""
        from tenant.controllers.console.tenant_controller import list_user_tenants

        # Mock IAM client 返回空列表
        with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
            mock_iam_client = MagicMock()
            mock_iam_client.get_user_tenants = AsyncMock(return_value=[])
            mock_get_iam.return_value = mock_iam_client

            # 执行测试
            result = await list_user_tenants(user_id="user-1", session=mock_session)

            # 验证结果
            assert result.status_code == 200
            import json

            data = json.loads(result.body.decode())
            assert data["code"] == 200
            assert data["data"] == []


@pytest.mark.asyncio
class TestGetCurrentTenantInfo:
    """get_current_tenant_info 控制器测试"""

    async def test_get_current_tenant_info_success(self, mock_session):
        """成功获取当前租户信息"""
        from tenant.controllers.console.tenant_controller import get_current_tenant_info
        from tenant.models import TenantStatus

        # 准备测试数据
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "测试租户"
        mock_tenant.code = "TEST001"
        mock_tenant.status = TenantStatus.ACTIVE

        with patch(
            "tenant.controllers.console.tenant_controller.get_tenant_id"
        ) as mock_get_tenant_id:
            mock_get_tenant_id.return_value = "tenant-1"

            with patch(
                "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
            ) as mock_get:
                mock_get.return_value = mock_tenant

                # 执行测试
                result = await get_current_tenant_info(session=mock_session)

                # 验证结果
                assert result.status_code == 200
                import json

                data = json.loads(result.body.decode())
                assert data["code"] == 200
                assert data["data"]["id"] == "tenant-1"
                assert data["data"]["name"] == "测试租户"

    async def test_get_current_tenant_info_no_context(self, mock_session):
        """未设置租户上下文时抛出 400 错误"""
        from tenant.controllers.console.tenant_controller import get_current_tenant_info

        with patch(
            "tenant.controllers.console.tenant_controller.get_tenant_id"
        ) as mock_get_tenant_id:
            mock_get_tenant_id.return_value = None

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_current_tenant_info(session=mock_session)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "租户上下文未设置"

    async def test_get_current_tenant_info_not_found(self, mock_session):
        """租户不存在时抛出 404 错误"""
        from tenant.controllers.console.tenant_controller import get_current_tenant_info

        with patch(
            "tenant.controllers.console.tenant_controller.get_tenant_id"
        ) as mock_get_tenant_id:
            mock_get_tenant_id.return_value = "tenant-1"

            with patch(
                "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
            ) as mock_get:
                mock_get.return_value = None

                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_tenant_info(session=mock_session)

                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "租户不存在"


@pytest.mark.asyncio
class TestSwitchTenant:
    """switch_tenant 控制器测试"""

    async def test_switch_tenant_success(self, mock_session):
        """成功切换租户"""
        from tenant.controllers.console.tenant_controller import switch_tenant

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "测试租户"
        mock_tenant.status = "active"

        # Mock IAM client 返回用户租户关联
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-1"

        with patch(
            "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
                mock_iam_client = MagicMock()
                mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
                mock_get_iam.return_value = mock_iam_client

                with patch(
                    "tenant.controllers.console.tenant_controller.TenantContext.set_current_tenant"
                ):
                    # 执行测试
                    result = await switch_tenant(
                        tenant_id="tenant-1", user_id="user-1", session=mock_session
                    )

                    # 验证返回对象
                    assert result.status_code == 200
                    import json

                    data = json.loads(result.body.decode())
                    assert data["code"] == 200
                    assert data["data"]["tenant_id"] == "tenant-1"
                    assert data["data"]["tenant_name"] == "测试租户"
                    assert data["data"]["message"] == "租户切换成功"

    async def test_switch_tenant_not_found(self, mock_session):
        """切换到不存在的租户时抛出 404 错误"""
        from tenant.controllers.console.tenant_controller import switch_tenant

        with patch(
            "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await switch_tenant(
                    tenant_id="nonexistent", user_id="user-1", session=mock_session
                )

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "租户不存在"

    async def test_switch_tenant_inactive(self, mock_session):
        """切换到已停用的租户时抛出 403 错误"""
        from tenant.controllers.console.tenant_controller import switch_tenant

        # Mock TenantService 返回已停用租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.status = "inactive"

        with patch(
            "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await switch_tenant(
                    tenant_id="tenant-1", user_id="user-1", session=mock_session
                )

            # 验证异常信息
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "租户已停用"

    async def test_switch_tenant_no_permission(self, mock_session):
        """切换到无权限的租户时抛出 403 错误"""
        from tenant.controllers.console.tenant_controller import switch_tenant

        # Mock TenantService 返回租户
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.status = "active"

        # Mock IAM client 返回用户属于其他租户
        mock_user_tenant = MagicMock()
        mock_user_tenant.tenant_id = "tenant-2"

        with patch(
            "tenant.controllers.console.tenant_controller.TenantService.get_by_id"
        ) as mock_get:
            mock_get.return_value = mock_tenant

            with patch("framework.clients.iam_client.get_iam_client") as mock_get_iam:
                mock_iam_client = MagicMock()
                mock_iam_client.get_user_tenants = AsyncMock(return_value=[mock_user_tenant])
                mock_get_iam.return_value = mock_iam_client

                # 执行测试并验证异常
                with pytest.raises(HTTPException) as exc_info:
                    await switch_tenant(
                        tenant_id="tenant-1", user_id="user-1", session=mock_session
                    )

                # 验证异常信息
                assert exc_info.value.status_code == 403
                assert exc_info.value.detail == "无权访问该租户"
