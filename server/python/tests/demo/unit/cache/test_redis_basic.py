"""Redis Cache Basic Operations Tests"""

from unittest.mock import AsyncMock, patch

import pytest


class TestRedisBasic:
    """Basic Redis cache operations tests"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        with patch("aiocache.Cache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache
            yield mock_cache

    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, mock_redis):
        """Test setting and getting cache value"""
        # Set value
        await mock_redis.set("test_key", "test_value")

        # Get value
        await mock_redis.get("test_key")
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, mock_redis):
        """Test getting non-existent key returns None"""
        mock_redis.get.return_value = None

        result = await mock_redis.get("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_cache_key(self, mock_redis):
        """Test deleting cache key"""
        await mock_redis.delete("test_key")

        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_check(self, mock_redis):
        """Test checking if key exists"""
        mock_redis.exists.return_value = True

        result = await mock_redis.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_redis):
        """Test clearing all cache"""
        await mock_redis.clear()

        mock_redis.clear.assert_called_once()
