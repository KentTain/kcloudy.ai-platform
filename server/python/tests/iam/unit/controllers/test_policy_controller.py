"""
企业策略控制器单元测试
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from iam.models import Policy


def _make_policy(
    id="policy-001",
    code="download-deny",
    name="下载拒绝策略",
    policy_type="download",
    effect="deny",
    priority=100,
    enabled=False,
):
    """构造测试用 Policy 实例"""
    return Policy(
        id=id,
        code=code,
        name=name,
        policy_type=policy_type,
        effect=effect,
        priority=priority,
        enabled=enabled,
        tenant_id="tenant-001",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _parse_response(result):
    """解析 ORJSONResponse"""
    return json.loads(result.body)


@pytest.mark.unit
class TestAdminPolicyController:
    """Admin 策略控制器测试"""

    @pytest.mark.asyncio
    async def test_list_policies(self, mock_session):
        """
        场景：查询策略列表
        WHEN: 调用 list_policies 接口
        THEN: 返回分页数据
        """
        from iam.controllers.admin.policy_controller import list_policies
        from iam.schemas.policy import PolicyPaginatedQuery

        policy = _make_policy()

        with patch(
            "iam.services.policy_service.policy_service.list_policies",
            new_callable=AsyncMock,
        ) as mock_list, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ):
            mock_list.return_value = ([policy], 1)

            query = PolicyPaginatedQuery(page=1, page_size=20)
            result = await list_policies(
                query=query,
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_create_policy(self, mock_session):
        """
        场景：创建策略
        WHEN: 调用 create_policy 接口
        THEN: 返回创建的策略
        """
        from iam.controllers.admin.policy_controller import create_policy
        from iam.schemas.policy import PolicyCreate

        policy = _make_policy()

        with patch(
            "iam.services.policy_service.policy_service.create_policy",
            new_callable=AsyncMock,
        ) as mock_create, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_create.return_value = policy

            body = PolicyCreate(
                code="download-deny",
                name="下载拒绝策略",
                policy_type="download",
                effect="deny",
            )
            result = await create_policy(
                data=body,
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_get_policy(self, mock_session):
        """
        场景：获取策略详情
        WHEN: 策略存在
        THEN: 返回策略详情
        """
        from iam.controllers.admin.policy_controller import get_policy

        policy = _make_policy()

        with patch(
            "iam.services.policy_service.policy_service.get_policy",
            new_callable=AsyncMock,
        ) as mock_get, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ):
            mock_get.return_value = policy

            result = await get_policy(
                policy_id="policy-001",
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_get_policy_not_found(self, mock_session):
        """
        场景：获取不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 抛出 404 异常
        """
        from iam.controllers.admin.policy_controller import get_policy

        with patch(
            "iam.services.policy_service.policy_service.get_policy",
            new_callable=AsyncMock,
        ) as mock_get, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ):
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_policy(
                    policy_id="policy-nonexist",
                    session=mock_session,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_policy(self, mock_session):
        """
        场景：更新策略
        WHEN: 策略存在
        THEN: 返回更新后的策略
        """
        from iam.controllers.admin.policy_controller import update_policy
        from iam.schemas.policy import PolicyUpdate

        policy = _make_policy(name="新策略名称")

        with patch(
            "iam.services.policy_service.policy_service.update_policy",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_update.return_value = policy

            body = PolicyUpdate(name="新策略名称")
            result = await update_policy(
                policy_id="policy-001",
                data=body,
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_update_policy_not_found(self, mock_session):
        """
        场景：更新不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 抛出 404 异常
        """
        from iam.controllers.admin.policy_controller import update_policy
        from iam.schemas.policy import PolicyUpdate

        with patch(
            "iam.services.policy_service.policy_service.update_policy",
            new_callable=AsyncMock,
        ) as mock_update, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_update.return_value = None

            body = PolicyUpdate(name="新名称")
            with pytest.raises(HTTPException) as exc_info:
                await update_policy(
                    policy_id="policy-nonexist",
                    data=body,
                    session=mock_session,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_policy(self, mock_session):
        """
        场景：删除策略
        WHEN: 策略存在
        THEN: 返回成功
        """
        from iam.controllers.admin.policy_controller import delete_policy

        with patch(
            "iam.services.policy_service.policy_service.delete_policy",
            new_callable=AsyncMock,
        ) as mock_delete, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ):
            mock_delete.return_value = True

            result = await delete_policy(
                policy_id="policy-001",
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_policy_not_found(self, mock_session):
        """
        场景：删除不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 抛出 404 异常
        """
        from iam.controllers.admin.policy_controller import delete_policy

        with patch(
            "iam.services.policy_service.policy_service.delete_policy",
            new_callable=AsyncMock,
        ) as mock_delete, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ):
            mock_delete.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await delete_policy(
                    policy_id="policy-nonexist",
                    session=mock_session,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_enable_policy(self, mock_session):
        """
        场景：启用策略
        WHEN: 策略存在
        THEN: 返回启用后的策略
        """
        from iam.controllers.admin.policy_controller import enable_policy

        policy = _make_policy(enabled=True)

        with patch(
            "iam.services.policy_service.policy_service.enable_policy",
            new_callable=AsyncMock,
        ) as mock_enable, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_enable.return_value = policy

            result = await enable_policy(
                policy_id="policy-001",
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_enable_policy_not_found(self, mock_session):
        """
        场景：启用不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 抛出 404 异常
        """
        from iam.controllers.admin.policy_controller import enable_policy

        with patch(
            "iam.services.policy_service.policy_service.enable_policy",
            new_callable=AsyncMock,
        ) as mock_enable, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_enable.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await enable_policy(
                    policy_id="policy-nonexist",
                    session=mock_session,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disable_policy(self, mock_session):
        """
        场景：停用策略
        WHEN: 策略存在
        THEN: 返回停用后的策略
        """
        from iam.controllers.admin.policy_controller import disable_policy

        policy = _make_policy(enabled=False)

        with patch(
            "iam.services.policy_service.policy_service.disable_policy",
            new_callable=AsyncMock,
        ) as mock_disable, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_disable.return_value = policy

            result = await disable_policy(
                policy_id="policy-001",
                session=mock_session,
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_disable_policy_not_found(self, mock_session):
        """
        场景：停用不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 抛出 404 异常
        """
        from iam.controllers.admin.policy_controller import disable_policy

        with patch(
            "iam.services.policy_service.policy_service.disable_policy",
            new_callable=AsyncMock,
        ) as mock_disable, patch(
            "iam.controllers.admin.policy_controller.get_tenant_id",
            return_value="tenant-001",
        ), patch(
            "iam.controllers.admin.policy_controller.get_user_id",
            return_value="user-001",
        ):
            mock_disable.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await disable_policy(
                    policy_id="policy-nonexist",
                    session=mock_session,
                )

            assert exc_info.value.status_code == 404
