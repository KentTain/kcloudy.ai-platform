"""
权限申请服务

提供权限申请提交、审批、查询等功能。
"""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import PermissionRequest

_logger = logger.bind(name=__name__)


class PermissionRequestService:
    """权限申请服务"""

    @staticmethod
    async def submit_request(
        session: AsyncSession,
        user_id: str,
        tenant_id: str,
        request_type: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        reason: str | None = None,
        target_subject_type: str | None = None,
        target_subject_id: str | None = None,
        requested_actions: list[str] | None = None,
        request_payload: dict | None = None,
    ) -> PermissionRequest:
        """
        提交权限申请

        Args:
            session: 数据库会话
            user_id: 申请人 ID
            tenant_id: 租户 ID
            request_type: 申请类型
            resource_type: 资源类型
            resource_id: 资源 ID
            reason: 申请原因
            target_subject_type: 目标主体类型
            target_subject_id: 目标主体 ID
            requested_actions: 请求的操作列表
            request_payload: 申请附加数据

        Returns:
            PermissionRequest
        """
        req = PermissionRequest(
            applicant_id=user_id,
            tenant_id=tenant_id,
            request_type=request_type,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            target_subject_type=target_subject_type,
            target_subject_id=target_subject_id,
            requested_actions=requested_actions,
            request_payload=request_payload,
            status="pending",
            created_by=user_id,
        )
        session.add(req)
        await session.flush()
        return req

    @staticmethod
    async def approve_request(
        session: AsyncSession,
        request_id: str,
        handler_id: str,
        result_comment: str | None = None,
    ) -> PermissionRequest | None:
        """
        审批通过权限申请

        Args:
            session: 数据库会话
            request_id: 申请 ID
            handler_id: 审批人 ID
            result_comment: 审批意见

        Returns:
            PermissionRequest | None
        """
        req = await PermissionRequest.one_by_id(session, request_id)
        if req is None:
            return None

        req.status = "approved"
        req.handler_id = handler_id
        req.handled_at = datetime.now(UTC).replace(tzinfo=None)
        req.result_comment = result_comment
        await session.flush()
        return req

    @staticmethod
    async def reject_request(
        session: AsyncSession,
        request_id: str,
        handler_id: str,
        result_comment: str | None = None,
    ) -> PermissionRequest | None:
        """
        审批拒绝权限申请

        Args:
            session: 数据库会话
            request_id: 申请 ID
            handler_id: 审批人 ID
            result_comment: 审批意见

        Returns:
            PermissionRequest | None
        """
        req = await PermissionRequest.one_by_id(session, request_id)
        if req is None:
            return None

        req.status = "rejected"
        req.handler_id = handler_id
        req.handled_at = datetime.now(UTC).replace(tzinfo=None)
        req.result_comment = result_comment
        await session.flush()
        return req

    @staticmethod
    async def list_my_requests(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        request_type: str | None = None,
    ) -> tuple[list[PermissionRequest], int]:
        """
        查询我的权限申请

        Args:
            session: 数据库会话
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            request_type: 类型筛选

        Returns:
            tuple[list[PermissionRequest], int]
        """
        conditions = [PermissionRequest.applicant_id == user_id]

        if status:
            conditions.append(PermissionRequest.status == status)

        if request_type:
            conditions.append(PermissionRequest.request_type == request_type)

        # 查询总数
        count_stmt = select(func.count(PermissionRequest.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(PermissionRequest)
            .where(*conditions)
            .order_by(PermissionRequest.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def list_pending_approvals(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PermissionRequest], int]:
        """
        查询待我审批的权限申请

        当前实现：查询当前租户下所有 pending 状态的申请。
        后续可根据实际审批人分配规则优化。

        Args:
            session: 数据库会话
            user_id: 用户 ID（预留，当前查询所有 pending）
            page: 页码
            page_size: 每页数量

        Returns:
            tuple[list[PermissionRequest], int]
        """
        conditions = [PermissionRequest.status == "pending"]

        # 查询总数
        count_stmt = select(func.count(PermissionRequest.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(PermissionRequest)
            .where(*conditions)
            .order_by(PermissionRequest.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total


# 服务单例
permission_request_service = PermissionRequestService()
