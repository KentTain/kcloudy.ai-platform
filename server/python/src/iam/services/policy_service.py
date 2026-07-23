"""
企业策略服务

提供企业策略 CRUD、启用/停用等功能。
"""

from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Policy

_logger = logger.bind(name=__name__)


class PolicyService:
    """企业策略服务"""

    @staticmethod
    async def list_policies(
        session: AsyncSession,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        policy_type: str | None = None,
        effect: str | None = None,
        enabled: bool | None = None,
    ) -> tuple[list[Policy], int]:
        """
        查询策略列表

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            page: 页码
            page_size: 每页数量
            keyword: 关键词搜索（编码/名称）
            policy_type: 策略类型筛选
            effect: 策略效果筛选
            enabled: 是否启用筛选

        Returns:
            tuple[list[Policy], int]
        """
        conditions = [Policy.tenant_id == tenant_id]

        if keyword:
            conditions.append(
                or_(
                    Policy.code.ilike(f"%{keyword}%"),
                    Policy.name.ilike(f"%{keyword}%"),
                )
            )

        if policy_type:
            conditions.append(Policy.policy_type == policy_type)

        if effect:
            conditions.append(Policy.effect == effect)

        if enabled is not None:
            conditions.append(Policy.enabled == enabled)

        # 查询总数
        count_stmt = select(func.count(Policy.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(Policy)
            .where(*conditions)
            .order_by(Policy.priority.desc(), Policy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def create_policy(
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        code: str,
        name: str,
        policy_type: str,
        effect: str = "deny",
        priority: int = 100,
        enabled: bool = False,
        condition_json: dict | None = None,
        action_json: dict | None = None,
        starts_at=None,
        ends_at=None,
        meta_data: dict | None = None,
    ) -> Policy:
        """
        创建策略

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            user_id: 创建人 ID
            code: 策略编码
            name: 策略名称
            policy_type: 策略类型
            effect: 策略效果(allow/deny)
            priority: 优先级
            enabled: 是否启用
            condition_json: 命中条件
            action_json: 动作配置
            starts_at: 生效时间
            ends_at: 失效时间
            meta_data: 元数据

        Returns:
            Policy
        """
        policy = Policy(
            tenant_id=tenant_id,
            code=code,
            name=name,
            policy_type=policy_type,
            effect=effect,
            priority=priority,
            enabled=enabled,
            condition_json=condition_json,
            action_json=action_json,
            starts_at=starts_at,
            ends_at=ends_at,
            meta_data=meta_data,
            created_by=user_id,
        )
        session.add(policy)
        await session.flush()
        return policy

    @staticmethod
    async def update_policy(
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        policy_id: str,
        **kwargs,
    ) -> Policy | None:
        """
        更新策略

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            user_id: 更新人 ID
            policy_id: 策略 ID
            **kwargs: 更新字段

        Returns:
            Policy | None
        """
        policy = await Policy.one_by_id(session, policy_id)
        if policy is None or policy.tenant_id != tenant_id:
            return None

        # 只更新传入的非 None 字段
        update_fields = {
            k: v for k, v in kwargs.items() if v is not None
        }
        for field, value in update_fields.items():
            if hasattr(policy, field):
                setattr(policy, field, value)

        policy.updated_by = user_id
        await session.flush()
        return policy

    @staticmethod
    async def delete_policy(
        session: AsyncSession,
        tenant_id: str,
        policy_id: str,
    ) -> bool:
        """
        删除策略

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            policy_id: 策略 ID

        Returns:
            bool
        """
        policy = await Policy.one_by_id(session, policy_id)
        if policy is None or policy.tenant_id != tenant_id:
            return False

        await session.delete(policy)
        await session.flush()
        return True

    @staticmethod
    async def enable_policy(
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        policy_id: str,
    ) -> Policy | None:
        """
        启用策略

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            user_id: 更新人 ID
            policy_id: 策略 ID

        Returns:
            Policy | None
        """
        policy = await Policy.one_by_id(session, policy_id)
        if policy is None or policy.tenant_id != tenant_id:
            return None

        policy.enabled = True
        policy.updated_by = user_id
        await session.flush()
        return policy

    @staticmethod
    async def disable_policy(
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        policy_id: str,
    ) -> Policy | None:
        """
        停用策略

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            user_id: 更新人 ID
            policy_id: 策略 ID

        Returns:
            Policy | None
        """
        policy = await Policy.one_by_id(session, policy_id)
        if policy is None or policy.tenant_id != tenant_id:
            return None

        policy.enabled = False
        policy.updated_by = user_id
        await session.flush()
        return policy

    @staticmethod
    async def get_policy(
        session: AsyncSession,
        tenant_id: str,
        policy_id: str,
    ) -> Policy | None:
        """
        获取策略详情

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            policy_id: 策略 ID

        Returns:
            Policy | None
        """
        policy = await Policy.one_by_id(session, policy_id)
        if policy is None or policy.tenant_id != tenant_id:
            return None
        return policy


# 服务单例
policy_service = PolicyService()
