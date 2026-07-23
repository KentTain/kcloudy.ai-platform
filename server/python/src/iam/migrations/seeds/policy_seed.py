"""
企业策略种子数据初始化

为默认租户创建默认企业策略，包括：
- 默认分类策略（deny，未分类资源拒绝访问）
- 默认下载策略（allow，允许下载）
- 默认预览策略（allow，允许预览）
- 默认入库策略（allow，允许入库）
"""

from __future__ import annotations

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import Policy

# 默认策略定义
DEFAULT_POLICIES = [
    {
        "code": "default_classification",
        "name": "默认分类策略",
        "policy_type": "classification",
        "effect": "deny",
        "priority": 100,
        "enabled": True,
        "condition_json": None,
        "action_json": None,
    },
    {
        "code": "default_download",
        "name": "默认下载策略",
        "policy_type": "download",
        "effect": "allow",
        "priority": 100,
        "enabled": True,
        "condition_json": None,
        "action_json": None,
    },
    {
        "code": "default_preview",
        "name": "默认预览策略",
        "policy_type": "preview",
        "effect": "allow",
        "priority": 100,
        "enabled": True,
        "condition_json": None,
        "action_json": None,
    },
    {
        "code": "default_ingestion",
        "name": "默认入库策略",
        "policy_type": "ingestion",
        "effect": "allow",
        "priority": 100,
        "enabled": True,
        "condition_json": None,
        "action_json": None,
    },
]


async def run(*, dry_run: bool = False) -> int:
    """初始化默认企业策略数据

    为默认租户创建默认分类、下载、预览、入库策略。
    种子数据幂等：重复运行不报错。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session

    settings = get_settings()
    tenant_id = settings.tenant.default_tenant_id

    async with get_session() as session:
        created_count = 0

        for policy_data in DEFAULT_POLICIES:
            # 幂等检查：按 tenant_id + code 查询
            result = await session.execute(
                select(Policy).where(
                    Policy.tenant_id == tenant_id,
                    Policy.code == policy_data["code"],
                ).limit(1)
            )
            existing = result.scalar_one_or_none()

            if existing:
                write_info(f"策略已存在，跳过: {policy_data['code']}")
                continue

            if dry_run:
                write_info(f"[DRY-RUN] 将创建策略: {policy_data['code']} - {policy_data['name']}")
                created_count += 1
                continue

            # 创建策略
            policy = Policy(
                tenant_id=tenant_id,
                code=policy_data["code"],
                name=policy_data["name"],
                policy_type=policy_data["policy_type"],
                effect=policy_data["effect"],
                priority=policy_data["priority"],
                enabled=policy_data["enabled"],
                condition_json=policy_data["condition_json"],
                action_json=policy_data["action_json"],
            )
            session.add(policy)
            created_count += 1
            write_success(f"创建策略: {policy_data['code']} - {policy_data['name']}")

        if not dry_run and created_count > 0:
            await session.commit()

        return created_count
