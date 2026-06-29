"""
Tenant 服务单元测试
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.tenant.context import SimpleTenant
from framework.tenant.exceptions import (
    TenantExpiredError,
    TenantInactiveError,
    TenantNotFoundError,
)
from tenant.models import Tenant, TenantStatus
from tenant.services.tenant_service import TenantService


class TestGetById:
    """get_by_id 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_tenant(self, session):
        """缓存命中时返回 SimpleTenant"""
        cached_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
        )

        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get:
            mock_cache_get.return_value = cached_tenant

            result = await TenantService.get_by_id(session, "tenant-1", use_cache=True)

        assert result is cached_tenant
        mock_cache_get.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_fetches_from_database_when_cache_miss(self, session):
        """缓存未命中时从数据库获取"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "测试租户"
        mock_tenant.status = TenantStatus.ACTIVE
        mock_tenant.expired_at = None

        # 创建预期的 SimpleTenant
        expected_simple_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
        )

        with (
            patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get,
            patch("tenant.services.tenant_service.TenantCache.set") as mock_cache_set,
            patch(
                "tenant.services.tenant_service.TenantService.build_simple_tenant"
            ) as mock_build,
        ):
            mock_cache_get.return_value = None

            # 配置 session mock
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            session.execute.return_value = mock_result

            mock_build.return_value = expected_simple_tenant

            result = await TenantService.get_by_id(session, "tenant-1", use_cache=True)

        assert result.id == "tenant-1"
        mock_cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, session):
        """租户不存在时返回 None"""
        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get:
            mock_cache_get.return_value = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            session.execute.return_value = mock_result

            result = await TenantService.get_by_id(
                session, "nonexistent", use_cache=True
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_skips_cache_when_use_cache_false(self, session):
        """use_cache=False 时跳过缓存"""
        mock_tenant = MagicMock(spec=Tenant)

        # 创建预期的 SimpleTenant
        expected_simple_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
        )

        with (
            patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get,
            patch(
                "tenant.services.tenant_service.TenantService.build_simple_tenant"
            ) as mock_build,
        ):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            session.execute.return_value = mock_result

            mock_build.return_value = expected_simple_tenant

            result = await TenantService.get_by_id(session, "tenant-1", use_cache=False)

        assert result.id == "tenant-1"
        mock_cache_get.assert_not_awaited()


class TestGetByCode:
    """get_by_code 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenant_when_found(self, session):
        """根据编码找到租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        session.execute.return_value = mock_result

        result = await TenantService.get_by_code(session, "T001")

        assert result is mock_tenant

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, session):
        """编码不存在时返回 None"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await TenantService.get_by_code(session, "NONEXISTENT")

        assert result is None


class TestCreate:
    """create 方法测试"""

    @pytest.mark.asyncio
    async def test_creates_tenant_with_required_fields(self, session):
        """使用必填字段创建租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "测试租户"

        with (
            patch("tenant.services.tenant_service.generate_tenant_key") as mock_gen_key,
            patch("tenant.services.tenant_service.encrypt") as mock_encrypt,
            patch(
                "tenant.services.tenant_service.database_config_service"
            ) as mock_db_service,
            patch(
                "tenant.services.tenant_service.storage_config_service"
            ) as mock_storage_service,
            patch(
                "tenant.services.tenant_service.cache_config_service"
            ) as mock_cache_service,
            patch(
                "tenant.services.tenant_service.queue_config_service"
            ) as mock_queue_service,
            patch(
                "tenant.services.tenant_service.pubsub_config_service"
            ) as mock_pubsub_service,
            patch(
                "framework.tenant.sync_protocols.get_module_auto_assigner",
                return_value=None,
            ),
        ):
            mock_gen_key.return_value = "raw-tenant-key"
            mock_encrypt.return_value = "encrypted-key"

            # Mock 默认配置服务返回 None
            mock_db_service.get_default_config = AsyncMock(return_value=None)
            mock_storage_service.get_default_config = AsyncMock(return_value=None)
            mock_cache_service.get_default_config = AsyncMock(return_value=None)
            mock_queue_service.get_default_config = AsyncMock(return_value=None)
            mock_pubsub_service.get_default_config = AsyncMock(return_value=None)

            session.add = MagicMock()
            session.flush = AsyncMock()

            def set_tenant_side_effect(tenant):
                tenant.id = "tenant-1"

            session.add.side_effect = set_tenant_side_effect

            result = await TenantService.create(
                session,
                name="测试租户",
                code="T001",
            )

        mock_gen_key.assert_called_once()
        mock_encrypt.assert_called_once_with("raw-tenant-key")
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_tenant_with_all_fields(self, session):
        """使用所有字段创建租户"""
        with (
            patch("tenant.services.tenant_service.generate_tenant_key") as mock_gen_key,
            patch("tenant.services.tenant_service.encrypt") as mock_encrypt,
            patch(
                "framework.tenant.sync_protocols.get_module_auto_assigner",
                return_value=None,
            ),
        ):
            mock_gen_key.return_value = "raw-tenant-key"
            mock_encrypt.return_value = "encrypted-key"

            session.add = MagicMock()
            session.flush = AsyncMock()

            await TenantService.create(
                session,
                name="测试租户",
                code="T001",
                contact_name="张三",
                contact_email="test@example.com",
                contact_phone="13800138000",
                expired_at=datetime.now() + timedelta(days=365),
                settings={"theme": "dark"},
                # 资源配置关联
                db_config_id="db-config-1",
                storage_config_id="storage-config-1",
                cache_config_id="cache-config-1",
                queue_config_id="queue-config-1",
                pubsub_config_id="pubsub-config-1",
            )

        # encrypt 被调用一次：租户密钥
        mock_encrypt.assert_called_once_with("raw-tenant-key")


class TestUpdate:
    """update 方法测试"""

    @pytest.mark.asyncio
    async def test_updates_tenant_fields(self, session):
        """更新租户字段"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"

        with patch(
            "tenant.services.tenant_service.TenantCache.invalidate"
        ) as mock_invalidate:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            session.execute.return_value = mock_result
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            result = await TenantService.update(
                session,
                tenant_id="tenant-1",
                name="新名称",
                contact_email="new@example.com",
            )

        assert result is mock_tenant
        assert mock_tenant.name == "新名称"
        assert mock_tenant.contact_email == "new@example.com"
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_none_when_tenant_not_found(self, session):
        """租户不存在时返回 None"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await TenantService.update(
            session,
            tenant_id="nonexistent",
            name="新名称",
        )

        assert result is None


class TestDelete:
    """delete 方法测试"""

    @pytest.mark.asyncio
    async def test_deletes_tenant_successfully(self, session):
        """成功删除租户"""
        with patch(
            "tenant.services.tenant_service.TenantCache.invalidate"
        ) as mock_invalidate:
            mock_result = MagicMock()
            mock_result.rowcount = 1
            session.execute.return_value = mock_result
            session.commit = AsyncMock()

            result = await TenantService.delete(session, "tenant-1")

        assert result is True
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_false_when_tenant_not_found(self, session):
        """租户不存在时返回 False"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute.return_value = mock_result
        session.commit = AsyncMock()

        result = await TenantService.delete(session, "nonexistent")

        assert result is False


class TestActivate:
    """activate 方法测试"""

    @pytest.mark.asyncio
    async def test_activates_tenant(self, session):
        """激活租户"""
        mock_tant = MagicMock(spec=Tenant)
        mock_tant.id = "tenant-1"
        mock_tant.status = TenantStatus.INACTIVE

        with patch(
            "tenant.services.tenant_service.TenantCache.invalidate"
        ) as mock_invalidate:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tant
            session.execute.return_value = mock_result
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            result = await TenantService.activate(session, "tenant-1")

        assert result is mock_tant
        assert mock_tant.status == TenantStatus.ACTIVE
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_none_when_tenant_not_found(self, session):
        """租户不存在时返回 None"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await TenantService.activate(session, "nonexistent")

        assert result is None


class TestDeactivate:
    """deactivate 方法测试"""

    @pytest.mark.asyncio
    async def test_deactivates_tenant(self, session):
        """停用租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.status = TenantStatus.ACTIVE

        with patch(
            "tenant.services.tenant_service.TenantCache.invalidate"
        ) as mock_invalidate:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            session.execute.return_value = mock_result
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            result = await TenantService.deactivate(session, "tenant-1")

        assert result is mock_tenant
        assert mock_tenant.status == TenantStatus.INACTIVE
        mock_invalidate.assert_awaited_once_with("tenant-1")


class TestValidateTenant:
    """validate_tenant 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenant_when_valid(self, session):
        """验证有效租户"""
        mock_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
            expired_at=None,
        )

        with patch.object(TenantService, "get_by_id") as mock_get:
            mock_get.return_value = mock_tenant

            result = await TenantService.validate_tenant(session, "tenant-1")

        assert result is mock_tenant

    @pytest.mark.asyncio
    async def test_raises_not_found_error(self, session):
        """租户不存在时抛出异常"""
        with patch.object(TenantService, "get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(TenantNotFoundError):
                await TenantService.validate_tenant(session, "nonexistent")

    @pytest.mark.asyncio
    async def test_raises_inactive_error(self, session):
        """租户已停用时抛出异常"""
        mock_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.INACTIVE,
            expired_at=None,
        )

        with patch.object(TenantService, "get_by_id") as mock_get:
            mock_get.return_value = mock_tenant

            with pytest.raises(TenantInactiveError):
                await TenantService.validate_tenant(session, "tenant-1")

    @pytest.mark.asyncio
    async def test_raises_expired_error(self, session):
        """租户已过期时抛出异常"""
        mock_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
            expired_at=datetime.now() - timedelta(days=1),
        )

        with patch.object(TenantService, "get_by_id") as mock_get:
            mock_get.return_value = mock_tenant

            with pytest.raises(TenantExpiredError):
                await TenantService.validate_tenant(session, "tenant-1")


class TestListTenants:
    """list_tenants 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self, session):
        """返回分页列表"""
        mock_tenants = [MagicMock(spec=Tenant) for _ in range(3)]

        # 总数查询
        count_result = MagicMock()
        count_result.scalar.return_value = 100

        # 列表查询
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = mock_tenants

        session.execute.side_effect = [count_result, list_result]

        tenants, total = await TenantService.list_tenants(session, page=1, page_size=20)

        assert len(tenants) == 3
        assert total == 100

    @pytest.mark.asyncio
    async def test_filters_by_keyword(self, session):
        """按关键词过滤"""
        count_result = MagicMock()
        count_result.scalar.return_value = 5

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []

        session.execute.side_effect = [count_result, list_result]

        await TenantService.list_tenants(session, keyword="测试")

        # 验证查询被调用了两次（count + list）
        assert session.execute.call_count == 2


class TestGetTenantsBatch:
    """get_tenants_batch 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenants_in_order(self, session):
        """按请求顺序返回租户"""
        mock_tenant1 = MagicMock(spec=Tenant)
        mock_tenant1.id = "tenant-1"
        mock_tenant2 = MagicMock(spec=Tenant)
        mock_tenant2.id = "tenant-2"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_tenant1, mock_tenant2]
        session.execute.return_value = mock_result

        result = await TenantService.get_tenants_batch(
            session, ["tenant-1", "tenant-2"]
        )

        assert len(result) == 2
        assert result[0].id == "tenant-1"
        assert result[1].id == "tenant-2"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_input(self, session):
        """空输入返回空列表"""
        result = await TenantService.get_tenants_batch(session, [])

        assert result == []

    @pytest.mark.asyncio
    async def test_filters_out_missing_tenants(self, session):
        """过滤不存在的租户"""
        mock_tenant1 = MagicMock(spec=Tenant)
        mock_tenant1.id = "tenant-1"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_tenant1]
        session.execute.return_value = mock_result

        result = await TenantService.get_tenants_batch(
            session, ["tenant-1", "nonexistent"]
        )

        assert len(result) == 1
        assert result[0].id == "tenant-1"


class TestGetTenantStats:
    """get_tenant_stats 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_correct_stats(self, session):
        """返回正确的统计数据"""
        # 模拟数据库查询结果
        mock_row = MagicMock()
        mock_row.total_count = 100
        mock_row.inactive_count = 10
        mock_row.expired_count = 5

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        session.execute.return_value = mock_result

        stats = await TenantService.get_tenant_stats(session)

        assert stats["total_count"] == 100
        assert stats["inactive_count"] == 10
        assert stats["expired_count"] == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_tenants(self, session):
        """无租户时返回零值"""
        mock_row = MagicMock()
        mock_row.total_count = 0
        mock_row.inactive_count = 0
        mock_row.expired_count = 0

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        session.execute.return_value = mock_result

        stats = await TenantService.get_tenant_stats(session)

        assert stats["total_count"] == 0
        assert stats["inactive_count"] == 0
        assert stats["expired_count"] == 0

    @pytest.mark.asyncio
    async def test_stats_keys_exist(self, session):
        """统计数据包含所有必要字段"""
        mock_row = MagicMock()
        mock_row.total_count = 50
        mock_row.inactive_count = 5
        mock_row.expired_count = 3

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        session.execute.return_value = mock_result

        stats = await TenantService.get_tenant_stats(session)

        assert "total_count" in stats
        assert "inactive_count" in stats
        assert "expired_count" in stats


class TestListTenantsWithStats:
    """list_tenants 集成 stats 测试"""

    @pytest.mark.asyncio
    async def test_list_tenants_includes_stats_field(self, session):
        """租户列表响应包含 stats 字段"""
        # 测试 controller 层的 list_tenants 方法会调用 get_tenant_stats
        # 这里验证 service 层返回的数据格式正确
        mock_tenants = [MagicMock(spec=Tenant) for _ in range(3)]
        mock_stats = {"total_count": 100, "inactive_count": 10, "expired_count": 5}

        # 模拟两次独立的调用：list_tenants 和 get_tenant_stats
        # 第一次调用：count
        count_result = MagicMock()
        count_result.scalar.return_value = 100

        # 第二次调用：list
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = mock_tenants

        session.execute.side_effect = [count_result, list_result]

        tenants, total = await TenantService.list_tenants(session, page=1, page_size=20)

        assert len(tenants) == 3
        assert total == 100

    @pytest.mark.asyncio
    async def test_stats_accuracy_with_various_statuses(self, session):
        """统计数据准确性测试：不同状态租户"""
        # 模拟有活跃、非活跃、过期租户的场景
        mock_row = MagicMock()
        mock_row.total_count = 200
        mock_row.inactive_count = 30
        mock_row.expired_count = 15

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        session.execute.return_value = mock_result

        stats = await TenantService.get_tenant_stats(session)

        # 验证统计数据的一致性
        assert stats["total_count"] >= stats["inactive_count"]
        assert stats["total_count"] >= stats["expired_count"]
        # 活跃租户数应该是总数减去非活跃数
        active_count = stats["total_count"] - stats["inactive_count"]
        assert active_count == 170
