"""
用户管理服务

提供用户注册、信息管理、密码管理等功能。
"""

import asyncio
import secrets
import string

from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.utils.crypto import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from framework.utils.session import delete_user_sessions
from iam.models import User, UserOrganization, UserStatus, UserTenant
from iam.schemas.user import UserDetailResponse, UserTenantResponse

_logger = logger.bind(name=__name__)


class UserService:
    """用户管理服务"""

    @staticmethod
    async def register(
        session: AsyncSession,
        username: str,
        password: str,
        tenant_id: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        用户注册

        Args:
            session: 数据库会话
            username: 用户名
            password: 密码
            tenant_id: 租户 ID
            email: 邮箱
            phone: 手机号

        Returns:
            User

        Raises:
            ValueError: 注册失败
        """
        # 验证密码强度
        validate_password_strength(password)

        # 检查用户名是否已存在（同租户内）
        stmt = select(User).where(
            User.username == username, User.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在（同租户内）
        if email:
            stmt = select(User).where(
                User.email == email, User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("邮箱已被注册")

        # 检查手机号是否已存在（同租户内）
        if phone:
            stmt = select(User).where(
                User.phone == phone, User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("手机号已被注册")

        # 创建用户
        user = User(
            username=username,
            password_hash=hash_password(password),
            tenant_id=tenant_id,
            email=email,
            phone=phone,
            status=UserStatus.ACTIVE,
            profile_completed=True,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

        _logger.info(f"用户注册成功: {username}")
        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: str) -> User | None:
        """根据 ID 获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        """根据用户名获取用户"""
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(session: AsyncSession, user_ids: list[str]) -> list[User]:
        """批量获取用户"""
        if not user_ids:
            return []
        stmt = select(User).where(User.id.in_(user_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user_id: str,
        nickname: str | None = None,
        avatar: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        更新用户信息

        Args:
            session: 数据库会话
            user_id: 用户 ID
            nickname: 昵称
            avatar: 头像
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        if nickname is not None:
            user.nickname = nickname
        if avatar is not None:
            user.avatar = avatar
        if email is not None:
            # 检查邮箱唯一性
            if email != user.email:
                stmt = select(User).where(User.email == email, User.id != user_id)
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("邮箱已被其他用户使用")
            user.email = email
        if phone is not None:
            # 检查手机号唯一性
            if phone != user.phone:
                stmt = select(User).where(User.phone == phone, User.id != user_id)
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("手机号已被其他用户使用")
            user.phone = phone

        await session.flush()
        await session.refresh(user)

        _logger.info(f"更新用户信息: {user_id}")
        return user

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        修改密码

        Args:
            session: 数据库会话
            user_id: 用户 ID
            old_password: 原密码
            new_password: 新密码

        Returns:
            bool: 是否成功
        """
        # 验证新密码强度
        validate_password_strength(new_password)

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 验证原密码
        if not user.password_hash or not verify_password(
            old_password, user.password_hash
        ):
            raise ValueError("原密码错误")

        # 更新密码
        user.password_hash = hash_password(new_password)
        await session.flush()

        # 使所有会话失效，强制重新登录
        deleted_count = await delete_user_sessions(user_id)
        _logger.info(f"修改密码成功: {user_id}, 已清除 {deleted_count} 个会话")

        return True

    @staticmethod
    async def reset_password(
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        code: str | None = None,
        new_password: str | None = None,
    ) -> bool:
        """
        重置密码

        Args:
            session: 数据库会话
            email: 邮箱
            phone: 手机号
            code: 验证码
            new_password: 新密码

        Returns:
            bool: 是否成功
        """
        # TODO: 验证验证码

        if not new_password:
            raise ValueError("新密码不能为空")

        validate_password_strength(new_password)

        # 根据邮箱或手机号查找用户
        if email:
            stmt = select(User).where(User.email == email)
        elif phone:
            stmt = select(User).where(User.phone == phone)
        else:
            raise ValueError("请提供邮箱或手机号")

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 更新密码
        user.password_hash = hash_password(new_password)
        await session.flush()

        # 使所有会话失效
        await delete_user_sessions(user.id)

        _logger.info(f"重置密码成功: {user.username}")
        return True

    @staticmethod
    async def complete_profile(
        session: AsyncSession,
        user_id: str,
        password: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        OAuth 用户补全信息

        Args:
            session: 数据库会话
            user_id: 用户 ID
            password: 密码
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        validate_password_strength(password)

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 设置密码
        user.password_hash = hash_password(password)

        # 设置邮箱
        if email:
            user.email = email
            user.is_email_verified = True

        # 设置手机号
        if phone:
            user.phone = phone
            user.is_phone_verified = True

        # 标记信息已完整
        user.profile_completed = True

        await session.flush()
        await session.refresh(user)

        _logger.info(f"OAuth 用户补全信息: {user_id}")
        return user

    @staticmethod
    async def list_users(
        session: AsyncSession,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        status: str | None = None,
        org_id: str | None = None,
        include_children: bool = False,
    ) -> tuple[list[User], int]:
        """
        获取用户列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID（可选，不传则查所有租户）
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 状态过滤
            org_id: 组织 ID 过滤
            include_children: 是否包含子组织用户

        Returns:
            tuple[list[User], int]
        """
        from sqlalchemy import func

        from iam.models import Organization

        # 构建查询条件
        conditions = []
        if tenant_id:
            conditions.append(User.tenant_id == tenant_id)
        if keyword:
            conditions.append(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.nickname.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                )
            )
        if status:
            conditions.append(User.status == status)

        # 组织筛选
        if org_id:
            if include_children:
                # 获取组织及其所有子组织的 ID
                org = await session.get(Organization, org_id)
                if org:
                    # 使用 parent_ids 前缀匹配所有子组织
                    parent_ids_prefix = org.descendant_parent_ids_prefix()
                    org_stmt = select(Organization.id).where(
                        or_(
                            Organization.id == org_id,
                            Organization.parent_ids.like(f"{parent_ids_prefix}%"),
                        )
                    )
                    org_result = await session.execute(org_stmt)
                    org_ids = [row[0] for row in org_result.all()]
                else:
                    org_ids = [org_id]
            else:
                org_ids = [org_id]

            # 通过 UserOrganization 关联查询
            user_id_stmt = (
                select(UserOrganization.user_id)
                .where(UserOrganization.organization_id.in_(org_ids))
                .distinct()
            )
            user_id_result = await session.execute(user_id_stmt)
            user_ids = [row[0] for row in user_id_result.all()]
            conditions.append(User.id.in_(user_ids))

        # 查询总数
        count_stmt = select(func.count(User.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = select(User)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    @staticmethod
    async def get_user_stats(
        session: AsyncSession,
        tenant_id: str | None = None,
    ) -> dict:
        """
        获取用户统计信息

        Args:
            session: 数据库会话
            tenant_id: 租户 ID（可选，不传则统计所有租户）

        Returns:
            dict: 包含 total、enabled、disabled、multi_role 的统计数据
        """
        from iam.models import UserRole

        # 基础条件
        base_condition = []
        if tenant_id:
            base_condition.append(User.tenant_id == tenant_id)

        # 并行统计各项数据
        # 1. 用户总数
        total_stmt = select(func.count(User.id))
        if base_condition:
            total_stmt = total_stmt.where(*base_condition)

        # 2. 启用用户数
        enabled_stmt = select(func.count(User.id)).where(User.status == UserStatus.ACTIVE)
        if base_condition:
            enabled_stmt = enabled_stmt.where(*base_condition)

        # 3. 停用用户数
        disabled_stmt = select(func.count(User.id)).where(User.status == UserStatus.INACTIVE)
        if base_condition:
            disabled_stmt = disabled_stmt.where(*base_condition)

        # 执行查询
        total_result = await session.execute(total_stmt)
        enabled_result = await session.execute(enabled_stmt)
        disabled_result = await session.execute(disabled_stmt)

        total = total_result.scalar() or 0
        enabled = enabled_result.scalar() or 0
        disabled = disabled_result.scalar() or 0

        # 4. 多角色用户数
        # 查询有多个角色的用户
        multi_role_stmt = (
            select(UserRole.user_id)
            .join(User, UserRole.user_id == User.id)
            .where(User.status != UserStatus.LOCKED)  # 排除锁定用户
            .group_by(UserRole.user_id)
            .having(func.count(UserRole.role_id) > 1)
        )
        if base_condition:
            multi_role_stmt = multi_role_stmt.where(*base_condition)

        multi_role_result = await session.execute(multi_role_stmt)
        multi_role = len(multi_role_result.all())

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "multi_role": multi_role,
        }

    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        password: str,
        tenant_id: str,
        email: str | None = None,
        phone: str | None = None,
        nickname: str | None = None,
    ) -> User:
        """
        管理员创建用户

        Args:
            session: 数据库会话
            username: 用户名
            password: 密码
            tenant_id: 租户 ID
            email: 邮箱
            phone: 手机号
            nickname: 昵称

        Returns:
            User

        Raises:
            ValueError: 创建失败
        """
        # 验证密码强度
        validate_password_strength(password)

        # 检查用户名是否已存在（同租户内）
        stmt = select(User).where(
            User.username == username, User.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在（同租户内）
        if email:
            stmt = select(User).where(
                User.email == email, User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("邮箱已被注册")

        # 检查手机号是否已存在（同租户内）
        if phone:
            stmt = select(User).where(
                User.phone == phone, User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("手机号已被注册")

        # 创建用户
        user = User(
            username=username,
            password_hash=hash_password(password),
            tenant_id=tenant_id,
            email=email,
            phone=phone,
            nickname=nickname,
            status=UserStatus.ACTIVE,
            profile_completed=True,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

        _logger.info(f"管理员创建用户: {username}")
        return user

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: str,
        nickname: str | None = None,
        avatar: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        管理员更新用户信息（带唯一性校验）

        Args:
            session: 数据库会话
            user_id: 用户 ID
            nickname: 昵称
            avatar: 头像
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 检查邮箱唯一性
        if email is not None and email != user.email:
            stmt = select(User).where(User.email == email, User.id != user_id)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("邮箱已被其他用户使用")
            user.email = email

        # 检查手机号唯一性
        if phone is not None and phone != user.phone:
            stmt = select(User).where(User.phone == phone, User.id != user_id)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("手机号已被其他用户使用")
            user.phone = phone

        if nickname is not None:
            user.nickname = nickname
        if avatar is not None:
            user.avatar = avatar

        await session.flush()
        await session.refresh(user)

        _logger.info(f"管理员更新用户信息: {user_id}")
        return user

    @staticmethod
    async def set_status(session: AsyncSession, user_id: str, status: str) -> User:
        """
        设置用户状态

        Args:
            session: 数据库会话
            user_id: 用户 ID
            status: 目标状态 (active/inactive/locked)

        Returns:
            User
        """
        # 验证状态值
        valid_statuses = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.LOCKED]
        if status not in valid_statuses:
            raise ValueError(f"无效的状态值，必须是: {[s for s in valid_statuses]}")

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        user.status = status
        await session.flush()
        await session.refresh(user)

        _logger.info(f"设置用户状态: {user_id} -> {status}")
        return user

    @staticmethod
    async def soft_delete(session: AsyncSession, user_id: str) -> bool:
        """
        软删除用户（设置状态为 inactive）

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            bool
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        user.status = UserStatus.INACTIVE
        await session.flush()

        _logger.info(f"软删除用户: {user_id}")
        return True

    @staticmethod
    async def admin_reset_password(
        session: AsyncSession,
        user_id: str,
        new_password: str | None = None,
    ) -> str:
        """
        管理员重置用户密码

        Args:
            session: 数据库会话
            user_id: 用户 ID
            new_password: 新密码，如果为空则生成随机密码

        Returns:
            str: 新密码（明文）
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 生成随机密码或使用提供的密码
        if new_password:
            validate_password_strength(new_password)
            password = new_password
        else:
            # 生成 12 位随机密码
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = "".join(secrets.choice(alphabet) for _ in range(12))

        user.password_hash = hash_password(password)
        await session.flush()

        # 使所有会话失效
        await delete_user_sessions(user_id)

        _logger.info(f"管理员重置用户密码: {user_id}")
        return password

    @staticmethod
    async def get_user_organizations(session: AsyncSession, user_id: str) -> list[dict]:
        """
        获取用户所属组织列表

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[dict]
        """
        from iam.models import Organization

        stmt = (
            select(Organization, UserOrganization.is_leader)
            .join(UserOrganization, Organization.id == UserOrganization.organization_id)
            .where(UserOrganization.user_id == user_id)
            .order_by(Organization.sort_order, Organization.created_at)
        )
        result = await session.execute(stmt)

        organizations = []
        for row in result:
            org, is_leader = row
            organizations.append(
                {
                    "id": org.id,
                    "name": org.name,
                    "code": org.code,
                    "is_leader": is_leader,
                }
            )
        return organizations

    @staticmethod
    async def get_user_tenant_ids(session: AsyncSession, user_id: str) -> list[str]:
        """
        获取用户所属租户 ID 列表

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[str]: 租户 ID 列表
        """
        stmt = select(UserTenant.tenant_id).where(UserTenant.user_id == user_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    async def get_user_ids_by_tenant_id(session: AsyncSession, tenant_id: str) -> list[str]:
        """
        根据用户 ID 获取租户 ID 列表

        Args:
            session: 数据库会话
            user_ids: 用户 ID 列表

        Returns:
            dict[str, list[str]]: 用户 ID 到租户 ID 列表的映射
        """
        stmt = select(UserTenant.user_id).where(UserTenant.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    @staticmethod
    async def get_user_tenants_detail(session: AsyncSession, user_id: str) -> list[dict]:
        """
        获取用户所属租户详细信息列表

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[dict]: 包含 tenant_id、role、is_default 的字典列表
        """
        stmt = select(UserTenant).where(UserTenant.user_id == user_id)
        result = await session.execute(stmt)
        user_tenants = result.scalars().all()

        return [
            {
                "tenant_id": ut.tenant_id,
                "role": ut.role,
                "is_default": ut.is_default,
            }
            for ut in user_tenants
        ]

    @staticmethod
    async def get_user_detail(session: AsyncSession, user_id: str) -> UserDetailResponse | None:
        """
        获取用户详情聚合数据

        聚合用户基础信息、角色、权限、租户列表和菜单树。
        使用 asyncio.gather 并行查询优化性能。

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            UserDetailResponse | None: 用户详情聚合响应，用户不存在时返回 None
        """
        # 获取用户基础信息
        user = await UserService.get_by_id(session, user_id)
        if not user:
            return None

        # 并行查询角色、权限、租户
        from iam.services.permission_service import permission_check_service
        from iam.services.role_service import user_role_service as user_roles_service

        roles_task = user_roles_service.get_user_roles(session, user_id)
        permissions_task = permission_check_service.get_user_permissions(session, user_id)
        tenants_task = UserService._get_user_tenants_with_detail(session, user_id)

        roles, permissions, tenants = await asyncio.gather(
            roles_task, permissions_task, tenants_task
        )

        # 获取用户菜单树
        from framework.tenant.context import get_tenant_id
        from iam.services.user_menu_service import user_menu_service

        tenant_id = get_tenant_id()
        menus = await user_menu_service.get_user_menus(session, user_id, tenant_id)

        # 构建响应
        role_codes = [r.code for r in roles]
        return UserDetailResponse.from_user(
            user=user,
            role_codes=role_codes,
            permissions=permissions,
            tenants=tenants,
            menus=menus,
        )

    @staticmethod
    async def _get_user_tenants_with_detail(session: AsyncSession, user_id: str) -> list[UserTenantResponse]:
        """
        获取用户租户列表（包含租户详细信息）

        内部方法，用于聚合查询。跨模块调用 tenant_service。

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            list[UserTenantResponse]: 用户租户响应列表
        """
        # 获取用户租户关联
        user_tenants = await UserService.get_user_tenants_detail(session, user_id)
        if not user_tenants:
            return []

        # 获取租户详细信息（跨模块调用通过 inner 接口）
        tenant_ids = [ut["tenant_id"] for ut in user_tenants]
        from tenant.services.tenant_service import tenant_service
        tenants_info = await tenant_service.get_tenants_by_ids(session, tenant_ids)

        # 构建租户响应列表
        tenants_vo = []
        for ut in user_tenants:
            tenant_info = tenants_info.get(ut["tenant_id"])
            if tenant_info:
                tenants_vo.append(
                    UserTenantResponse(
                        id=ut["tenant_id"],
                        name=tenant_info.name,
                        code=tenant_info.code,
                        is_default=ut["is_default"],
                    )
                )
        return tenants_vo


# 服务单例
user_service = UserService()
