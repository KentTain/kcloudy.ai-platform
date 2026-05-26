"""
IAM 客户端

提供对 IAM 模块的统一调用入口。
"""

from typing import Any

from pydantic import BaseModel, Field

from framework.clients.inner_http_client import InnerHttpClient


class UserInfo(BaseModel):
    """用户信息"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str | None = Field(None, description="邮箱")
    phone: str | None = Field(None, description="手机号")
    nickname: str | None = Field(None, description="昵称")
    status: str = Field(..., description="状态")
    tenant_id: str | None = Field(None, description="当前租户ID")


class DepartmentInfo(BaseModel):
    """部门信息"""
    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parent_id: str | None = Field(None, description="父部门ID")


class IamClient:
    """
    IAM 模块客户端

    支持单体模式（直接 Service 调用）和微服务模式（HTTP 调用）。
    """

    def __init__(
        self,
        inner_url: str | None = None,
        inner_timeout: float = 30.0,
    ):
        """
        初始化客户端

        Args:
            inner_url: 内部接口 URL（微服务模式）
            inner_timeout: 超时时间（秒）
        """
        self.inner_url = inner_url
        self._http_client: InnerHttpClient | None = None

        if inner_url:
            self._http_client = InnerHttpClient(
                base_url=inner_url,
                timeout=inner_timeout,
                service_name="iam",
                health_path="/inner/v1/iam/health",
            )

    async def get_user(self, user_id: str) -> UserInfo | None:
        """
        获取单个用户

        Args:
            user_id: 用户 ID

        Returns:
            UserInfo | None
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/users/{user_id}",
                response_model=UserInfo,
            )
            return data
        else:
            # 单体模式
            from iam.services.user_service import UserService
            from iam.models import UserTenant
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            user = await UserService.get_by_id(user_id)
            if not user:
                return None

            # 获取用户的默认租户
            tenant_id = None
            async with async_session() as session:
                stmt = select(UserTenant).where(
                    UserTenant.user_id == user_id,
                    UserTenant.is_default == True
                )
                result = await session.execute(stmt)
                user_tenant = result.scalar_one_or_none()
                if user_tenant:
                    tenant_id = user_tenant.tenant_id

            return UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                nickname=user.nickname,
                status=user.status,
                tenant_id=tenant_id,
            )

    async def get_users_batch(self, user_ids: list[str]) -> list[UserInfo]:
        """
        批量获取用户

        Args:
            user_ids: 用户 ID 列表

        Returns:
            list[UserInfo]
        """
        if not user_ids:
            return []

        if self._http_client:
            # 微服务模式
            data = await self._http_client.post(
                "/inner/v1/users/batch",
                json={"user_ids": user_ids},
            )
            if data and isinstance(data, list):
                return [UserInfo.model_validate(item) for item in data]
            return []
        else:
            # 单体模式
            from iam.services.user_service import UserService
            from iam.models import UserTenant
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            users = await UserService.get_by_ids(user_ids)

            # 获取用户的默认租户
            user_tenant_map = {}
            async with async_session() as session:
                stmt = select(UserTenant).where(
                    UserTenant.user_id.in_(user_ids),
                    UserTenant.is_default == True
                )
                result = await session.execute(stmt)
                for ut in result.scalars().all():
                    user_tenant_map[ut.user_id] = ut.tenant_id

            return [
                UserInfo(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    phone=u.phone,
                    nickname=u.nickname,
                    status=u.status,
                    tenant_id=user_tenant_map.get(u.id),
                )
                for u in users if u
            ]

    async def get_user_departments(self, user_id: str) -> list[DepartmentInfo]:
        """
        获取用户部门

        Args:
            user_id: 用户 ID

        Returns:
            list[DepartmentInfo]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/users/{user_id}/departments",
            )
            if data and isinstance(data, dict) and "departments" in data:
                return [DepartmentInfo.model_validate(d) for d in data["departments"]]
            return []
        else:
            # 单体模式
            from iam.models import UserDepartment, Department
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            async with async_session() as session:
                stmt = select(UserDepartment).where(UserDepartment.user_id == user_id)
                result = await session.execute(stmt)
                user_departments = result.scalars().all()

                department_ids = [ud.department_id for ud in user_departments]
                if not department_ids:
                    return []

                stmt = select(Department).where(Department.id.in_(department_ids))
                result = await session.execute(stmt)
                departments = result.scalars().all()

                return [
                    DepartmentInfo(
                        id=d.id,
                        name=d.name,
                        parent_id=d.parent_id,
                    )
                    for d in departments
                ]

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否可用
        """
        if self._http_client:
            return await self._http_client.health_check()
        # 单体模式始终健康
        return True


# 默认客户端实例
_iam_client: IamClient | None = None


def get_iam_client() -> IamClient:
    """获取 IAM 客户端实例"""
    global _iam_client
    if _iam_client is None:
        from framework.configs import get_settings
        settings = get_settings()
        _iam_client = IamClient(
            inner_url=getattr(settings, "iam_inner_url", None),
            inner_timeout=getattr(settings, "iam_inner_timeout", 30.0),
        )
    return _iam_client
