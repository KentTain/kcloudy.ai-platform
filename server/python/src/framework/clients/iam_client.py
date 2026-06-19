"""
IAM 客户端

提供对 IAM 模块的统一调用入口。
"""


from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

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


class UserTenantInfo(BaseModel):
    """用户-租户关联信息"""
    tenant_id: str = Field(..., description="租户ID")
    role: str = Field(..., description="角色")
    is_default: bool = Field(..., description="是否默认租户")


class ModuleRoleUsageInfo(BaseModel):
    """模块角色使用信息"""

    module_role_id: str = Field(..., description="模块定义层角色ID")
    role_id: str = Field(..., description="IAM层角色ID")
    role_code: str = Field(..., description="角色编码")
    role_name: str = Field(..., description="角色名称")
    user_count: int = Field(..., description="使用该角色的用户数")


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
                health_path="/iam/inner/v1/health",
            )

    async def get_user(self, session: AsyncSession, user_id: str) -> UserInfo | None:
        """
        获取单个用户

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            UserInfo | None
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/iam/inner/v1/users/{user_id}",
                response_model=UserInfo,
            )
            return data
        else:
            # 单体模式
            from sqlalchemy import select

            from iam.models import UserTenant
            from iam.services.user_service import UserService

            user = await UserService.get_by_id(user_id)
            if not user:
                return None

            # 获取用户的默认租户
            tenant_id = None
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

    async def get_users_batch(
        self, session: AsyncSession, user_ids: list[str]
    ) -> list[UserInfo]:
        """
        批量获取用户

        Args:
            session: 数据库会话
            user_ids: 用户 ID 列表

        Returns:
            list[UserInfo]
        """
        if not user_ids:
            return []

        if self._http_client:
            # 微服务模式
            data = await self._http_client.post(
                "/iam/inner/v1/users/batch",
                json={"user_ids": user_ids},
            )
            if data and isinstance(data, list):
                return [UserInfo.model_validate(item) for item in data]
            return []
        else:
            # 单体模式
            from sqlalchemy import select

            from iam.models import UserTenant
            from iam.services.user_service import UserService

            users = await UserService.get_by_ids(user_ids)

            # 获取用户的默认租户
            user_tenant_map = {}
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

    async def get_user_departments(
        self, session: AsyncSession, user_id: str
    ) -> list[DepartmentInfo]:
        """
        获取用户部门

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[DepartmentInfo]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/iam/inner/v1/users/{user_id}/departments",
            )
            if data and isinstance(data, dict) and "departments" in data:
                return [DepartmentInfo.model_validate(d) for d in data["departments"]]
            return []
        else:
            # 单体模式
            from sqlalchemy import select

            from iam.models import Department, UserDepartment

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

    async def get_user_tenants(
        self, session: AsyncSession, user_id: str
    ) -> list[UserTenantInfo]:
        """
        获取用户租户列表

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[UserTenantInfo]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/iam/inner/v1/users/{user_id}/tenants",
            )
            if data and isinstance(data, dict) and "tenants" in data:
                return [UserTenantInfo.model_validate(t) for t in data["tenants"]]
            return []
        else:
            # 单体模式
            from sqlalchemy import select

            from iam.models import UserTenant

            stmt = select(UserTenant).where(UserTenant.user_id == user_id)
            result = await session.execute(stmt)
            user_tenants = result.scalars().all()

            return [
                UserTenantInfo(
                    tenant_id=ut.tenant_id,
                    role=ut.role,
                    is_default=ut.is_default,
                )
                for ut in user_tenants
            ]

    async def get_tenant_user_ids(
        self, session: AsyncSession, tenant_id: str
    ) -> list[str]:
        """
        获取租户下的用户 ID 列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID

        Returns:
            list[str]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/iam/inner/v1/tenants/{tenant_id}/users",
            )
            if data and isinstance(data, dict) and "user_ids" in data:
                return data["user_ids"]
            return []
        else:
            # 单体模式
            from sqlalchemy import select

            from iam.models import UserTenant

            stmt = select(UserTenant.user_id).where(
                UserTenant.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    async def check_module_role_usage(
        self,
        session: AsyncSession,
        tenant_id: str,
        module_role_ids: list[str],
    ) -> list[ModuleRoleUsageInfo]:
        """
        检查租户下模块角色的使用情况

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            module_role_ids: 模块定义层角色 ID 列表（ModuleRole.id）

        Returns:
            list[ModuleRoleUsageInfo]: 有用户使用的角色列表
        """
        if not module_role_ids:
            return []

        if self._http_client:
            # 微服务模式
            data = await self._http_client.post(
                f"/iam/inner/v1/tenants/{tenant_id}/module-roles/usage",
                json={"module_role_ids": module_role_ids},
            )
            if data and isinstance(data, dict) and "roles" in data:
                return [ModuleRoleUsageInfo.model_validate(r) for r in data["roles"]]
            return []
        else:
            # 单体模式
            from sqlalchemy import func, select

            from iam.models import Role, UserRole

            # 查找该租户下 ref_id 关联到这些模块角色的 IAM 角色
            stmt = select(Role).where(
                Role.tenant_id == tenant_id,
                Role.ref_id.in_(module_role_ids),
            )
            result = await session.execute(stmt)
            roles = result.scalars().all()

            if not roles:
                return []

            role_ids = [r.id for r in roles]
            role_map = {r.id: r for r in roles}

            # 统计每个角色的用户数
            stmt = select(
                UserRole.role_id,
                func.count(UserRole.user_id).label("user_count"),
            ).where(
                UserRole.tenant_id == tenant_id,
                UserRole.role_id.in_(role_ids),
            ).group_by(UserRole.role_id)
            result = await session.execute(stmt)
            role_usage = {row[0]: row[1] for row in result.all()}

            # 构建返回结果（只返回有用户使用的角色）
            usage_list = []
            for role in roles:
                user_count = role_usage.get(role.id, 0)
                if user_count > 0:
                    usage_list.append(
                        ModuleRoleUsageInfo(
                            module_role_id=role.ref_id,
                            role_id=role.id,
                            role_code=role.code,
                            role_name=role.name,
                            user_count=user_count,
                        )
                    )

            return usage_list

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
