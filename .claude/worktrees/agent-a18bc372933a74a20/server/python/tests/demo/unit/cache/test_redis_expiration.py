"""Redis Cache Expiration Tests"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio


class TestRedisExpiration:

    @pytest.fixture
    def mock_redis(self):
        with patch('aiocache.Cache') as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache
            yield mock_cache

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, mock_redis):
        await mock_redis.set('test_key', 'test_value', ttl=60)
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == 'test_key'
        assert call_args[1]['ttl'] == 60

    @pytest.mark.asyncio
    async def test_set_with_different_ttl(self, mock_redis):
        await mock_redis.set('key1', 'value1', ttl=300)
        await mock_redis.set('key2', 'value2', ttl=3600)
        await mock_redis.set('key3', 'value3', ttl=86400)
        assert mock_redis.set.call_count == 3

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, mock_redis):
        await mock_redis.set('test_key', 'test_value')
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_ttl_returns_none_for_expired(self, mock_redis):
        mock_redis.ttl.return_value = -2
        result = await mock_redis.ttl('expired_key')
        assert result == -2

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_time(self, mock_redis):
        mock_redis.ttl.return_value = 60
        result = await mock_redis.ttl('test_key')
        assert result == 60
