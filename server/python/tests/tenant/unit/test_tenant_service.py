"""
Tenant 服务单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from tenant.services.tenant_service import TenantService
from tenant.models import Tenant, TenantStatus
from framework.tenant.context import SimpleTenant
from framework.tenant.exceptions import (
    TenantNotFoundError,
    TenantInactiveError,
    TenantExpiredError,
)


class TestGetById:
    """get_by_id 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_tenant(self):
        """缓存命中时返回 SimpleTenant"""
        cached_tenant = SimpleTenant(
            id="tenant-1",
            code="T001",
            name="测试租户",
            status=TenantStatus.ACTIVE,
        )

        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get:
            mock_cache_get.return_value = cached_tenant

            result = await TenantService.get_by_id("tenant-1", use_cache=True)

        assert result is cached_tenant
        mock_cache_get.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_fetches_from_database_when_cache_miss(self):
        """缓存未命中时从数据库获取"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "测试租户"
        mock_tenant.status = TenantStatus.ACTIVE
        mock_tenant.expired_at = None

        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get, \
             patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.TenantCache.set") as mock_cache_set:

            mock_cache_get.return_value = None

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_by_id("tenant-1", use_cache=True)

        assert result is mock_tenant
        mock_cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """租户不存在时返回 None"""
        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get, \
             patch("tenant.services.tenant_service.async_session") as mock_session:

            mock_cache_get.return_value = None

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_by_id("nonexistent", use_cache=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_skips_cache_when_use_cache_false(self):
        """use_cache=False 时跳过缓存"""
        mock_tenant = MagicMock(spec=Tenant)

        with patch("tenant.services.tenant_service.TenantCache.get") as mock_cache_get, \
             patch("tenant.services.tenant_service.async_session") as mock_session:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_by_id("tenant-1", use_cache=False)

        assert result is mock_tenant
        mock_cache_get.assert_not_awaited()


class TestGetByCode:
    """get_by_code 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenant_when_found(self):
        """根据编码找到租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"

        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_by_code("T001")

        assert result is mock_tenant

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """编码不存在时返回 None"""
        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_by_code("NONEXISTENT")

        assert result is None


class TestCreate:
    """create 方法测试"""

    @pytest.mark.asyncio
    async def test_creates_tenant_with_required_fields(self):
        """使用必填字段创建租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.code = "T001"
        mock_tenant.name = "测试租户"

        with patch("tenant.services.tenant_service.generate_tenant_key") as mock_gen_key, \
             patch("tenant.services.tenant_service.encrypt") as mock_encrypt, \
             patch("tenant.services.tenant_service.async_session") as mock_session:

            mock_gen_key.return_value = "raw-tenant-key"
            mock_encrypt.return_value = "encrypted-key"

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context
            mock_session_context.add = MagicMock()
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            def set_tenant_side_effect(tenant):
                tenant.id = "tenant-1"
            mock_session_context.add.side_effect = set_tenant_side_effect

            result = await TenantService.create(
                name="测试租户",
                code="T001",
            )

        mock_gen_key.assert_called_once()
        mock_encrypt.assert_called_once_with("raw-tenant-key")
        mock_session_context.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_tenant_with_all_fields(self):
        """使用所有字段创建租户"""
        with patch("tenant.services.tenant_service.generate_tenant_key") as mock_gen_key, \
             patch("tenant.services.tenant_service.encrypt") as mock_encrypt, \
             patch("tenant.services.tenant_service.async_session") as mock_session:

            mock_gen_key.return_value = "raw-tenant-key"
            mock_encrypt.return_value = "encrypted-key"

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context
            mock_session_context.add = MagicMock()
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            await TenantService.create(
                name="测试租户",
                code="T001",
                contact_name="张三",
                contact_email="test@example.com",
                contact_phone="13800138000",
                expired_at=datetime.now() + timedelta(days=365),
                settings={"theme": "dark"},
                db_type="postgresql",
                db_host="localhost",
                db_port=5432,
                db_name="tenant_db",
                db_username="tenant_user",
                db_password="password123",
                storage_type="minio",
                storage_bucket="tenant-bucket",
                cache_db=1,
            )

        # encrypt 被调用两次：租户密钥和数据库密码
        assert mock_encrypt.call_count == 2


class TestUpdate:
    """update 方法测试"""

    @pytest.mark.asyncio
    async def test_updates_tenant_fields(self):
        """更新租户字段"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"

        with patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.TenantCache.invalidate") as mock_invalidate:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            result = await TenantService.update(
                tenant_id="tenant-1",
                name="新名称",
                contact_email="new@example.com",
            )

        assert result is mock_tenant
        assert mock_tenant.name == "新名称"
        assert mock_tenant.contact_email == "new@example.com"
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_none_when_tenant_not_found(self):
        """租户不存在时返回 None"""
        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.update(
                tenant_id="nonexistent",
                name="新名称",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_encrypts_db_password_on_update(self):
        """更新数据库密码时加密"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"

        with patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.encrypt") as mock_encrypt, \
             patch("tenant.services.tenant_service.TenantCache.invalidate"):

            mock_encrypt.return_value = "encrypted-password"

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            await TenantService.update(
                tenant_id="tenant-1",
                db_password="new_password",
            )

        mock_encrypt.assert_called_once_with("new_password")
        assert mock_tenant.db_password == "encrypted-password"


class TestDelete:
    """delete 方法测试"""

    @pytest.mark.asyncio
    async def test_deletes_tenant_successfully(self):
        """成功删除租户"""
        with patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.TenantCache.invalidate") as mock_invalidate:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()

            result = await TenantService.delete("tenant-1")

        assert result is True
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_false_when_tenant_not_found(self):
        """租户不存在时返回 False"""
        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.rowcount = 0
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()

            result = await TenantService.delete("nonexistent")

        assert result is False


class TestActivate:
    """activate 方法测试"""

    @pytest.mark.asyncio
    async def test_activates_tenant(self):
        """激活租户"""
        mock_tant = MagicMock(spec=Tenant)
        mock_tant.id = "tenant-1"
        mock_tant.status = TenantStatus.INACTIVE

        with patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.TenantCache.invalidate") as mock_invalidate:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tant
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            result = await TenantService.activate("tenant-1")

        assert result is mock_tant
        assert mock_tant.status == TenantStatus.ACTIVE
        mock_invalidate.assert_awaited_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_returns_none_when_tenant_not_found(self):
        """租户不存在时返回 None"""
        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.activate("nonexistent")

        assert result is None


class TestDeactivate:
    """deactivate 方法测试"""

    @pytest.mark.asyncio
    async def test_deactivates_tenant(self):
        """停用租户"""
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = "tenant-1"
        mock_tenant.status = TenantStatus.ACTIVE

        with patch("tenant.services.tenant_service.async_session") as mock_session, \
             patch("tenant.services.tenant_service.TenantCache.invalidate") as mock_invalidate:

            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_session_context.execute.return_value = mock_result
            mock_session_context.commit = AsyncMock()
            mock_session_context.refresh = AsyncMock()

            result = await TenantService.deactivate("tenant-1")

        assert result is mock_tenant
        assert mock_tenant.status == TenantStatus.INACTIVE
        mock_invalidate.assert_awaited_once_with("tenant-1")


class TestValidateTenant:
    """validate_tenant 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenant_when_valid(self):
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

            result = await TenantService.validate_tenant("tenant-1")

        assert result is mock_tenant

    @pytest.mark.asyncio
    async def test_raises_not_found_error(self):
        """租户不存在时抛出异常"""
        with patch.object(TenantService, "get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(TenantNotFoundError):
                await TenantService.validate_tenant("nonexistent")

    @pytest.mark.asyncio
    async def test_raises_inactive_error(self):
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
                await TenantService.validate_tenant("tenant-1")

    @pytest.mark.asyncio
    async def test_raises_expired_error(self):
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
                await TenantService.validate_tenant("tenant-1")


class TestListTenants:
    """list_tenants 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self):
        """返回分页列表"""
        mock_tenants = [MagicMock(spec=Tenant) for _ in range(3)]

        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            # 总数查询
            count_result = MagicMock()
            count_result.scalar.return_value = 100

            # 列表查询
            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = mock_tenants

            mock_session_context.execute.side_effect = [count_result, list_result]

            tenants, total = await TenantService.list_tenants(page=1, page_size=20)

        assert len(tenants) == 3
        assert total == 100

    @pytest.mark.asyncio
    async def test_filters_by_keyword(self):
        """按关键词过滤"""
        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            count_result = MagicMock()
            count_result.scalar.return_value = 5

            list_result = MagicMock()
            list_result.scalars.return_value.all.return_value = []

            mock_session_context.execute.side_effect = [count_result, list_result]

            await TenantService.list_tenants(keyword="测试")

        # 验证查询被调用了两次（count + list）
        assert mock_session_context.execute.call_count == 2


class TestGetTenantsBatch:
    """get_tenants_batch 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_tenants_in_order(self):
        """按请求顺序返回租户"""
        mock_tenant1 = MagicMock(spec=Tenant)
        mock_tenant1.id = "tenant-1"
        mock_tenant2 = MagicMock(spec=Tenant)
        mock_tenant2.id = "tenant-2"

        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_tenant1, mock_tenant2]
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_tenants_batch(["tenant-1", "tenant-2"])

        assert len(result) == 2
        assert result[0].id == "tenant-1"
        assert result[1].id == "tenant-2"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_input(self):
        """空输入返回空列表"""
        result = await TenantService.get_tenants_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_filters_out_missing_tenants(self):
        """过滤不存在的租户"""
        mock_tenant1 = MagicMock(spec=Tenant)
        mock_tenant1.id = "tenant-1"

        with patch("tenant.services.tenant_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_tenant1]
            mock_session_context.execute.return_value = mock_result

            result = await TenantService.get_tenants_batch(["tenant-1", "nonexistent"])

        assert len(result) == 1
        assert result[0].id == "tenant-1"
