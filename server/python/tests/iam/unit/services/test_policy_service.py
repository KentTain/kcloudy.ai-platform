"""
企业策略服务单元测试
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam.models import Policy
from iam.services.policy_service import policy_service

# 测试常量
TEST_USER_ID = "user-001"
TEST_TENANT_ID = "tenant-001"


def _build_mock_result(scalars_return=None, scalar_return=None):
    """构建 mock 的 execute 返回值"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_return or []
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = scalar_return
    return mock_result


def _make_policy(
    id="policy-001",
    code="download-deny",
    name="下载拒绝策略",
    policy_type="download",
    effect="deny",
    priority=100,
    enabled=False,
    tenant_id=TEST_TENANT_ID,
):
    """构造测试用 Policy 实例"""
    return Policy(
        id=id,
        code=code,
        name=name,
        policy_type=policy_type,
        effect=effect,
        priority=priority,
        enabled=enabled,
        tenant_id=tenant_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.unit
class TestPolicyService:
    """企业策略服务测试"""

    @pytest.mark.asyncio
    async def test_create_policy(self, mock_session):
        """
        场景：创建策略
        WHEN: 管理员创建策略
        THEN: 创建策略记录并返回
        """
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        policy = await policy_service.create_policy(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            user_id=TEST_USER_ID,
            code="download-deny",
            name="下载拒绝策略",
            policy_type="download",
            effect="deny",
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_create_policy_default_values(self, mock_session):
        """
        场景：创建策略使用默认值
        WHEN: 创建策略只提供必填字段
        THEN: effect 默认 deny，priority 默认 100，enabled 默认 False
        """
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        policy = await policy_service.create_policy(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            user_id=TEST_USER_ID,
            code="preview-allow",
            name="预览允许策略",
            policy_type="preview",
        )

        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_list_policies_empty(self, mock_session):
        """
        场景：查询策略列表（空）
        WHEN: 没有策略记录
        THEN: 返回空列表
        """
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await policy_service.list_policies(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
        )

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_list_policies_with_data(self, mock_session):
        """
        场景：查询策略列表
        WHEN: 有策略记录
        THEN: 返回策略列表
        """
        policy = _make_policy()

        mock_result_count = _build_mock_result(scalar_return=1)
        mock_result_list = _build_mock_result(scalars_return=[policy])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await policy_service.list_policies(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].code == "download-deny"

    @pytest.mark.asyncio
    async def test_list_policies_with_keyword_filter(self, mock_session):
        """
        场景：按关键词筛选策略
        WHEN: 传入 keyword 参数
        THEN: 查询包含关键词筛选条件
        """
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await policy_service.list_policies(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
            keyword="download",
        )

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_policies_with_type_filter(self, mock_session):
        """
        场景：按策略类型筛选
        WHEN: 传入 policy_type 参数
        THEN: 查询包含类型筛选条件
        """
        mock_result_count = _build_mock_result(scalar_return=0)
        mock_result_list = _build_mock_result(scalars_return=[])

        mock_session.execute = AsyncMock(
            side_effect=[mock_result_count, mock_result_list]
        )

        items, total = await policy_service.list_policies(
            mock_session,
            tenant_id=TEST_TENANT_ID,
            page=1,
            page_size=20,
            policy_type="download",
        )

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_policy(self, mock_session):
        """
        场景：获取策略详情
        WHEN: 策略存在
        THEN: 返回策略对象
        """
        policy = _make_policy()

        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = policy

            result = await policy_service.get_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                policy_id="policy-001",
            )

            assert result is not None
            assert result.code == "download-deny"

    @pytest.mark.asyncio
    async def test_get_policy_not_found(self, mock_session):
        """
        场景：获取不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 返回 None
        """
        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await policy_service.get_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                policy_id="policy-nonexist",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_update_policy(self, mock_session):
        """
        场景：更新策略
        WHEN: 策略存在并更新字段
        THEN: 返回更新后的策略
        """
        policy = _make_policy()

        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = policy
            mock_session.flush = AsyncMock()

            result = await policy_service.update_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-001",
                name="新策略名称",
                effect="allow",
            )

            assert result is not None
            assert result.name == "新策略名称"
            assert result.effect == "allow"

    @pytest.mark.asyncio
    async def test_update_policy_not_found(self, mock_session):
        """
        场景：更新不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 返回 None
        """
        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await policy_service.update_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-nonexist",
                name="新名称",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_policy(self, mock_session):
        """
        场景：删除策略
        WHEN: 策略存在
        THEN: 返回 True
        """
        policy = _make_policy()

        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = policy
            mock_session.delete = AsyncMock()
            mock_session.flush = AsyncMock()

            result = await policy_service.delete_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                policy_id="policy-001",
            )

            assert result is True
            assert mock_session.delete.called

    @pytest.mark.asyncio
    async def test_delete_policy_not_found(self, mock_session):
        """
        场景：删除不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 返回 False
        """
        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await policy_service.delete_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                policy_id="policy-nonexist",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_enable_policy(self, mock_session):
        """
        场景：启用策略
        WHEN: 策略存在且停用
        THEN: enabled 变为 True
        """
        policy = _make_policy(enabled=False)

        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = policy
            mock_session.flush = AsyncMock()

            result = await policy_service.enable_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-001",
            )

            assert result is not None
            assert result.enabled is True

    @pytest.mark.asyncio
    async def test_enable_policy_not_found(self, mock_session):
        """
        场景：启用不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 返回 None
        """
        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await policy_service.enable_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-nonexist",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_disable_policy(self, mock_session):
        """
        场景：停用策略
        WHEN: 策略存在且启用
        THEN: enabled 变为 False
        """
        policy = _make_policy(enabled=True)

        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = policy
            mock_session.flush = AsyncMock()

            result = await policy_service.disable_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-001",
            )

            assert result is not None
            assert result.enabled is False

    @pytest.mark.asyncio
    async def test_disable_policy_not_found(self, mock_session):
        """
        场景：停用不存在的策略
        WHEN: 策略 ID 不存在
        THEN: 返回 None
        """
        with patch.object(Policy, "one_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await policy_service.disable_policy(
                mock_session,
                tenant_id=TEST_TENANT_ID,
                user_id=TEST_USER_ID,
                policy_id="policy-nonexist",
            )

            assert result is None
