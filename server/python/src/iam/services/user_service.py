"""
用户管理服务

提供用户注册、信息管理、密码管理等功能。
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from models.iam import User, UserStatus
from schemas.iam.user import UserVo
from framework.database.core.engine import async_session
from framework.utils.crypto import hash_password, verify_password, validate_password_strength

_logger = logger.bind(name=__name__)


class UserService:
    """用户管理服务"""

    @staticmethod
    async def register(
        username: str,
        password: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """
        用户注册

        Args:
            username: 用户名
            password: 密码
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
            # 检查用户名是否已存在
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("用户名已存在")

            # 检查邮箱是否已存在
            if email:
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("邮箱已被注册")

            # 检查手机号是否已存在
            if phone:
                stmt = select(User).where(User.phone == phone)
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("手机号已被注册")

            # 创建用户
            user = User(
                username=username,
                password_hash=hash_password(password),
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
                # TODO: 验证邮箱唯一性
                user.email = email
            if phone is not None:
                # TODO: 验证手机号唯一性
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
            if not user.password_hash or not verify_password(old_password, user.password_hash):
                raise ValueError("原密码错误")

            # 更新密码
            user.password_hash = hash_password(new_password)
            await session.commit()

            # TODO: 使所有会话失效，强制重新登录

            _logger.info(f"修改密码成功: {user_id}")
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
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        status: str | None = None,
    ) -> tuple[list[User], int]:
        """
        获取用户列表

        Args:
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


# 服务单例
user_service = UserService()
