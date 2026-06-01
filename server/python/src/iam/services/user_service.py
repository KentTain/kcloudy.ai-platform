"""
用户管理服务

提供用户注册、信息管理、密码管理等功能。
"""

import secrets
import string
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import func, or_, select

from framework.database.core.engine import async_session
from framework.utils.crypto import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from framework.utils.session import delete_user_sessions
from iam.models import User, UserDepartment, UserStatus, UserTenant
from iam.schemas.user import UserVo

_logger = logger.bind(name=__name__)


class UserService:
    """用户管理服务"""

    @staticmethod
    async def register(
        username: str,
        password: str,
        tenant_id: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        用户注册

        Args:
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

        async with async_session() as session:
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
            await session.commit()
            await session.refresh(user)

            _logger.info(f"用户注册成功: {username}")
            return user

    @staticmethod
    async def get_by_id(user_id: str) -> User | None:
        """根据 ID 获取用户"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(username: str) -> User | None:
        """根据用户名获取用户"""
        async with async_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(user_ids: list[str]) -> list[User]:
        """批量获取用户"""
        if not user_ids:
            return []
        async with async_session() as session:
            stmt = select(User).where(User.id.in_(user_ids))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def update_profile(
        user_id: str,
        nickname: str | None = None,
        avatar: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        更新用户信息

        Args:
            user_id: 用户 ID
            nickname: 昵称
            avatar: 头像
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        async with async_session() as session:
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

            await session.commit()
            await session.refresh(user)

            _logger.info(f"更新用户信息: {user_id}")
            return user

    @staticmethod
    async def change_password(
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> bool:
        """
        修改密码

        Args:
            user_id: 用户 ID
            old_password: 原密码
            new_password: 新密码

        Returns:
            bool: 是否成功
        """
        # 验证新密码强度
        validate_password_strength(new_password)

        async with async_session() as session:
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
            await session.commit()

        # 使所有会话失效，强制重新登录
        deleted_count = await delete_user_sessions(user_id)
        _logger.info(f"修改密码成功: {user_id}, 已清除 {deleted_count} 个会话")

        return True

    @staticmethod
    async def reset_password(
        email: str | None = None,
        phone: str | None = None,
        code: str | None = None,
        new_password: str | None = None,
    ) -> bool:
        """
        重置密码

        Args:
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

        async with async_session() as session:
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
            await session.commit()

        # 使所有会话失效
        await delete_user_sessions(user.id)

        _logger.info(f"重置密码成功: {user.username}")
        return True

    @staticmethod
    async def complete_profile(
        user_id: str,
        password: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        OAuth 用户补全信息

        Args:
            user_id: 用户 ID
            password: 密码
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        validate_password_strength(password)

        async with async_session() as session:
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

            await session.commit()
            await session.refresh(user)

            _logger.info(f"OAuth 用户补全信息: {user_id}")
            return user

    @staticmethod
    async def list_users(
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        status: str | None = None,
    ) -> tuple[list[User], int]:
        """
        获取用户列表

        Args:
            tenant_id: 租户 ID（可选，不传则查所有租户）
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 状态过滤

        Returns:
            tuple[list[User], int]
        """
        from sqlalchemy import func, or_

        async with async_session() as session:
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
    async def create_user(
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

        async with async_session() as session:
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
            await session.commit()
            await session.refresh(user)

            _logger.info(f"管理员创建用户: {username}")
            return user

    @staticmethod
    async def update_user(
        user_id: str,
        nickname: str | None = None,
        avatar: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        管理员更新用户信息（带唯一性校验）

        Args:
            user_id: 用户 ID
            nickname: 昵称
            avatar: 头像
            email: 邮箱
            phone: 手机号

        Returns:
            User
        """
        async with async_session() as session:
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

            await session.commit()
            await session.refresh(user)

            _logger.info(f"管理员更新用户信息: {user_id}")
            return user

    @staticmethod
    async def set_status(user_id: str, status: str) -> User:
        """
        设置用户状态

        Args:
            user_id: 用户 ID
            status: 目标状态 (active/inactive/locked)

        Returns:
            User
        """
        # 验证状态值
        valid_statuses = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.LOCKED]
        if status not in valid_statuses:
            raise ValueError(f"无效的状态值，必须是: {[s for s in valid_statuses]}")

        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError("用户不存在")

            user.status = status
            await session.commit()
            await session.refresh(user)

            _logger.info(f"设置用户状态: {user_id} -> {status}")
            return user

    @staticmethod
    async def soft_delete(user_id: str) -> bool:
        """
        软删除用户（设置状态为 inactive）

        Args:
            user_id: 用户 ID

        Returns:
            bool
        """
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError("用户不存在")

            user.status = UserStatus.INACTIVE
            await session.commit()

            _logger.info(f"软删除用户: {user_id}")
            return True

    @staticmethod
    async def admin_reset_password(
        user_id: str,
        new_password: str | None = None,
    ) -> str:
        """
        管理员重置用户密码

        Args:
            user_id: 用户 ID
            new_password: 新密码，如果为空则生成随机密码

        Returns:
            str: 新密码（明文）
        """
        async with async_session() as session:
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
            await session.commit()

        # 使所有会话失效
        await delete_user_sessions(user_id)

        _logger.info(f"管理员重置用户密码: {user_id}")
        return password

    @staticmethod
    async def get_user_departments(user_id: str) -> list[dict]:
        """
        获取用户所属部门列表

        Args:
            user_id: 用户 ID

        Returns:
            list[dict]
        """
        async with async_session() as session:
            from iam.models import Department

            stmt = (
                select(Department, UserDepartment.is_leader)
                .join(UserDepartment, Department.id == UserDepartment.department_id)
                .where(UserDepartment.user_id == user_id)
                .order_by(Department.sort_order, Department.created_at)
            )
            result = await session.execute(stmt)

            departments = []
            for row in result:
                dept, is_leader = row
                departments.append(
                    {
                        "id": dept.id,
                        "name": dept.name,
                        "code": dept.code,
                        "is_leader": is_leader,
                    }
                )
            return departments

    @staticmethod
    async def get_user_tenant_ids(user_id: str) -> list[str]:
        """
        获取用户所属租户 ID 列表

        Args:
            user_id: 用户 ID

        Returns:
            list[str]: 租户 ID 列表
        """
        async with async_session() as session:
            stmt = select(UserTenant.tenant_id).where(UserTenant.user_id == user_id)
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    @staticmethod
    async def get_user_ids_by_tenant_id(tenant_id: str) -> list[str]:
        """
        根据用户 ID 获取租户 ID 列表

        Args:
            user_ids: 用户 ID 列表

        Returns:
            dict[str, list[str]]: 用户 ID 到租户 ID 列表的映射
        """
        async with async_session() as session:
            stmt = select(UserTenant.user_id).where(UserTenant.tenant_id == tenant_id)
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    @staticmethod
    async def get_user_tenants_detail(user_id: str) -> list[dict]:
        """
        获取用户所属租户详细信息列表

        Args:
            user_id: 用户 ID

        Returns:
            list[dict]: 包含 tenant_id、role、is_default 的字典列表
        """
        async with async_session() as session:
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


# 服务单例
user_service = UserService()
