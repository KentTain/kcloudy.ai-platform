"""权限申请回调服务（供 iam 审批后调用）"""

from sqlalchemy.ext.asyncio import AsyncSession

from document.models.enums import ResourceAclEffect
from document.services.member_service import member_service
from document.services.permission_config_service import permission_config_service


class PermissionRequestService:
    """权限申请回调服务"""

    @staticmethod
    async def apply_callback(
        session: AsyncSession,
        request_type: str,
        target_resource_id: str,
        applicant_id: str,
        requested_role: str | None = None,
        requested_permission: str | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """处理权限申请审批通过后的回调落地

        Args:
            request_type: 申请类型 (library_join/library_resource/library_role)
            target_resource_id: 目标资源ID
            applicant_id: 申请人ID
            requested_role: 申请角色
            requested_permission: 申请权限
            extra_data: 额外数据
        """
        extra = extra_data or {}

        if request_type == "library_join":
            await member_service.add_member(
                session,
                library_id=target_resource_id,
                user_id=applicant_id,
                user_name=applicant_id,
                role=requested_role or "member",
            )
        elif request_type == "library_resource":
            library_id = extra.get("library_id")
            resource_type = extra.get("resource_type", "document")
            if not library_id:
                raise ValueError("library_resource 申请缺少 library_id")
            await permission_config_service.create_resource_acl(
                session,
                library_id=library_id,
                resource_type=resource_type,
                resource_id=target_resource_id,
                subject_id=applicant_id,
                subject_type="user",
                action=requested_permission or "read",
                effect=ResourceAclEffect.ALLOW,
            )
        elif request_type == "library_role":
            library_id = extra.get("library_id")
            if not library_id:
                raise ValueError("library_role 申请缺少 library_id")
            await permission_config_service.add_role_member(
                session,
                library_id=library_id,
                role_id=target_resource_id,
                user_id=applicant_id,
            )
        else:
            raise ValueError(f"不支持的申请类型: {request_type}")


permission_request_service = PermissionRequestService()
