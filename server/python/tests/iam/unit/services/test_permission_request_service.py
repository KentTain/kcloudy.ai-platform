"""
权限申请服务单元测试
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam.models import PermissionRequest
from iam.services.permission_request_service import permission_request_service

# 测试常量
TEST_USER_ID = "user-001"
TEST_TENANT_ID = "tenant-001"
TEST_HANDLER_ID = "handler-001"


def _build_mock_result(scalars_return=None, scalar_return=None, all_return=None):
    """构建 mock 的 execute 返回值"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_return or []
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = scalar_return
    if all_return is not None:
        mock_result.all.return_value = all_return
    return mock_result


def _make_permission_request(
    id="pr-001",
    applicant_id=TEST_USER_ID,
    request_type="library_join",
    status="pending",
    resource_type="library",
    resource_id="lib-001",
):
    """构造测试用 PermissionRequest 实例"""
    return PermissionRequest(
        id=id,
        applicant_id=applicant_id,
        request_type=request_type,
        status=status,
        tenant_id=TEST_TENANT_ID,
        resource_type=resource_type,
        resource_id=resource_id,
    )


@pytest.mark.unit
class TestPermissionRequestService:
    """权限申请服务测试"""

    @pytest.mark.asyncio
    async def test_submit_request(self, mock_session):
        """
        场景：提交权限申请
        WHEN: 用户提交权限申请
        THEN: 创建申请记录并返回
        """
        # Mock: session.add + flush + refresh
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        req = await permission_request_service.submit_request(
            mock_session,
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            request_type="library_join",
            resource_type="library",
            resource_id="lib-001",
            reason="申请加入文库",
        )

        # 验证 add 被调用
        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_approve_request(self, mock_session):
        """
        场景：审批通过权限申请
        WHEN: 管理员审批通过
        THEN: 状态变为 approved
        """
        pr = _make_permission_request(status="pending")

        # Mock: one_by_id 返回申请记录
        with (
            patch.object(
                PermissionRequest, "one_by_id", new_callable=AsyncMock
            ) as mock_get,
        ):
            mock_get.return_value = pr
            mock_session.flush = AsyncMock()

            result = await permission_request_service.approve_request(
                mock_session,
                request_id="pr-001",
                handler_id=TEST_HANDLER_ID,
                result_comment="同意",
            )

            assert result is not None
            assert result.status == "approved"
            assert result.handler_id == TEST_HANDLER_ID

    @pytest.mark.asyncio
    async def test_approve_request_not_found(self, mock_session):
        """
        场景：审批不存在的申请
        WHEN: 申请 ID 不存在
        THEN: 返回 None
        """
        with (
            patch.object(
                PermissionRequest, "one_by_id", new_callable=AsyncMock
            ) as mock_get,
        ):
            mock_get.return_value = None

            result = await permission_request_service.approve_request(
                mock_session,
                request_id="pr-nonexist",
                handler_id=TEST_HANDLER_ID,
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_reject_request(self, mock_session):
        """
        场景：审批拒绝权限申请
        WHEN: 管理员拒绝
        THEN: 状态变为 rejected
        """
        pr = _make_permission_request(status="pending")

        with (
            patch.object(
                PermissionRequest, "one_by_id", new_callable=AsyncMock
            ) as mock_get,
        ):
            mock_get.return_value = pr
            mock_session.flush = AsyncMock()

            result = await permission_request_service.reject_request(
                mock_session,
                request_id="pr-001",
                handler_id=TEST_HANDLER_ID,
                result_comment="不允许",
            )

            assert result is not None
            assert result.status == "rejected"

    @pytest.mark.asyncio
    async def test_list_my_requests_empty(self, mock_session):
        """
        场景：查询我的申请（空）
        WHEN: 没有申请记录
        THEN: 返回空列表
        """
        mock_session.execute = AsyncMock()
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute.side_effect = [mock_result_count, mock_result_list]

        items, total = await permission_request_service.list_my_requests(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
        )

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_list_my_requests_with_data(self, mock_session):
        """
        场景：查询我的申请
        WHEN: 有申请记录
        THEN: 返回申请列表
        """
        pr = _make_permission_request()

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[pr])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await permission_request_service.list_my_requests(
            mock_session,
            user_id=TEST_USER_ID,
            page=1,
            page_size=20,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].request_type == "library_join"

    @pytest.mark.asyncio
    async def test_list_pending_approvals_empty(self, mock_session):
        """
        场景：查询待我审批（空）
        WHEN: 没有待审批记录
        THEN: 返回空列表
        """
        mock_session.execute = AsyncMock()
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute.side_effect = [mock_result_count, mock_result_list]

        items, total = await permission_request_service.list_pending_approvals(
            mock_session,
            user_id=TEST_HANDLER_ID,
            page=1,
            page_size=20,
        )

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_list_pending_approvals_with_data(self, mock_session):
        """
        场景：查询待我审批
        WHEN: 有待审批记录
        THEN: 返回待审批列表
        """
        pr = _make_permission_request(status="pending")

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[pr])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await permission_request_service.list_pending_approvals(
            mock_session,
            user_id=TEST_HANDLER_ID,
            page=1,
            page_size=20,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].status == "pending"
