"""
权限申请控制器单元测试
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from iam.models import PermissionRequest


def _make_permission_request(
    id="pr-001",
    applicant_id="user-001",
    request_type="library_join",
    status="pending",
):
    """构造测试用 PermissionRequest 实例"""
    return PermissionRequest(
        id=id,
        applicant_id=applicant_id,
        request_type=request_type,
        status=status,
        tenant_id="tenant-001",
        resource_type="library",
        resource_id="lib-001",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _parse_response(result):
    """解析 ORJSONResponse"""
    return json.loads(result.body)


@pytest.mark.unit
class TestConsolePermissionRequestController:
    """Console 权限申请控制器测试"""

    @pytest.mark.asyncio
    async def test_submit_request(self, mock_session):
        """
        场景：提交权限申请
        WHEN: 调用 submit_request 接口
        THEN: 返回创建的申请
        """
        from iam.controllers.console.permission_request_controller import (
            submit_request,
        )
        from iam.schemas.permission_request import PermissionRequestCreate

        pr = _make_permission_request()

        with patch(
            "iam.services.permission_request_service.permission_request_service.submit_request",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = pr

            body = PermissionRequestCreate(
                request_type="library_join",
                resource_type="library",
                resource_id="lib-001",
                reason="申请加入",
            )
            result = await submit_request(
                body=body,
                session=mock_session,
                user_id="user-001",
                tenant_id="tenant-001",
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_list_my_requests(self, mock_session):
        """
        场景：查询我的申请
        WHEN: 调用 list_my_requests 接口
        THEN: 返回分页数据
        """
        from iam.controllers.console.permission_request_controller import (
            list_my_requests,
        )
        from iam.schemas.permission_request import PermissionRequestPaginatedQuery

        pr = _make_permission_request()

        with patch(
            "iam.services.permission_request_service.permission_request_service.list_my_requests",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = ([pr], 1)

            query = PermissionRequestPaginatedQuery(page=1, page_size=20)
            result = await list_my_requests(
                query=query,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_list_pending_approvals(self, mock_session):
        """
        场景：查询待审批
        WHEN: 调用 list_pending_approvals 接口
        THEN: 返回分页数据
        """
        from iam.controllers.console.permission_request_controller import (
            list_pending_approvals,
        )
        from iam.schemas.permission_request import PermissionRequestPaginatedQuery

        pr = _make_permission_request(status="pending")

        with patch(
            "iam.services.permission_request_service.permission_request_service.list_pending_approvals",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = ([pr], 1)

            query = PermissionRequestPaginatedQuery(page=1, page_size=20)
            result = await list_pending_approvals(
                query=query,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_approve_request(self, mock_session):
        """
        场景：审批通过
        WHEN: 调用 approve_request 接口
        THEN: 返回更新后的申请
        """
        from iam.controllers.console.permission_request_controller import (
            approve_request,
        )
        from iam.schemas.permission_request import PermissionRequestHandle

        pr = _make_permission_request(status="approved")

        with patch(
            "iam.services.permission_request_service.permission_request_service.approve_request",
            new_callable=AsyncMock,
        ) as mock_approve:
            mock_approve.return_value = pr

            body = PermissionRequestHandle(result_comment="同意")
            result = await approve_request(
                request_id="pr-001",
                body=body,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_reject_request(self, mock_session):
        """
        场景：审批拒绝
        WHEN: 调用 reject_request 接口
        THEN: 返回更新后的申请
        """
        from iam.controllers.console.permission_request_controller import (
            reject_request,
        )
        from iam.schemas.permission_request import PermissionRequestHandle

        pr = _make_permission_request(status="rejected")

        with patch(
            "iam.services.permission_request_service.permission_request_service.reject_request",
            new_callable=AsyncMock,
        ) as mock_reject:
            mock_reject.return_value = pr

            body = PermissionRequestHandle(result_comment="不允许")
            result = await reject_request(
                request_id="pr-001",
                body=body,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_approve_request_not_found(self, mock_session):
        """
        场景：审批不存在的申请
        WHEN: 申请 ID 不存在
        THEN: 返回 404
        """
        from iam.controllers.console.permission_request_controller import (
            approve_request,
        )
        from iam.schemas.permission_request import PermissionRequestHandle

        with patch(
            "iam.services.permission_request_service.permission_request_service.approve_request",
            new_callable=AsyncMock,
        ) as mock_approve:
            mock_approve.return_value = None

            body = PermissionRequestHandle(result_comment="同意")
            result = await approve_request(
                request_id="pr-nonexist",
                body=body,
                session=mock_session,
                user_id="user-001",
            )

            assert result.status_code == 404


@pytest.mark.unit
class TestAdminPermissionRequestController:
    """Admin 权限申请控制器测试"""

    @pytest.mark.asyncio
    async def test_list_permission_requests(self, mock_session):
        """
        场景：管理端查询权限申请
        WHEN: 调用 list_permission_requests 接口
        THEN: 返回分页数据
        """
        from iam.controllers.admin.permission_request_controller import (
            list_permission_requests,
        )
        from iam.schemas.permission_request import PermissionRequestPaginatedQuery

        pr = _make_permission_request()

        with patch(
            "iam.services.permission_request_service.permission_request_service.list_my_requests",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = ([pr], 1)

            query = PermissionRequestPaginatedQuery(page=1, page_size=20)
            result = await list_permission_requests(
                query=query,
                session=mock_session,
            )

            assert result.status_code == 200


@pytest.mark.unit
class TestInnerPermissionRequestController:
    """Inner 权限申请控制器测试"""

    @pytest.mark.asyncio
    async def test_apply_permission_request(self, mock_session):
        """
        场景：审批回调 inner 接口
        WHEN: 调用 apply_permission_request 接口
        THEN: 返回成功响应（Phase 1 占位）
        """
        from iam.controllers.inner.permission_request_controller import (
            apply_permission_request,
        )

        result = await apply_permission_request(
            request_id="pr-001",
            session=mock_session,
        )

        assert result.status_code == 200
        body = _parse_response(result)
        assert body["data"]["request_id"] == "pr-001"
        assert body["data"]["status"] == "applied"
