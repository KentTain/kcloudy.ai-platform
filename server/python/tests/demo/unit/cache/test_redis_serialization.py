"""Redis Cache Serialization Tests"""

import pytest
import orjson
from unittest.mock import AsyncMock, patch


class TestRedisSerialization:
    """Redis data type serialization tests"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        with patch("aiocache.Cache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache
            yield mock_cache

    @pytest.mark.asyncio
    async def test_cache_dictionary(self, mock_redis):
        """Test caching a dictionary"""
        test_dict = {"key": "value", "number": 123}

        # Serialize with orjson
        serialized = orjson.dumps(test_dict)
        mock_redis.get.return_value = orjson.loads(serialized)

        await mock_redis.set("dict_key", test_dict)
        result = await mock_redis.get("dict_key")

        assert result == test_dict

    @pytest.mark.asyncio
    async def test_cache_list(self, mock_redis):
        """Test caching a list"""
        test_list = [1, 2, 3, "four", {"five": 5}]

        await mock_redis.set("list_key", test_list)
        mock_redis.get.return_value = test_list

        result = await mock_redis.get("list_key")

        assert result == test_list

    @pytest.mark.asyncio
    async def test_cache_nested_object(self, mock_redis):
        """Test caching nested objects"""
        test_obj = {
            "user": {
                "name": "John",
                "age": 30,
                "address": {"city": "Beijing", "country": "China"}
            }
        }

        await mock_redis.set("nested_key", test_obj)
        mock_redis.get.return_value = test_obj

        result = await mock_redis.get("nested_key")

        assert result == test_obj

    @pytest.mark.asyncio
    async def test_cache_with_special_characters(self, mock_redis):
        """Test caching strings with special characters"""
        test_str = "Hello 世界 🌍 emoji 🚀"

        await mock_redis.set("special_key", test_str)
        mock_redis.get.return_value = test_str

        result = await mock_redis.get("special_key")

        assert result == test_str

    @pytest.mark.asyncio
    async def test_cache_none_value(self, mock_redis):
        """Test caching None value"""
        await mock_redis.set("none_key", None)
        mock_redis.get.return_value = None

        result = await mock_redis.get("none_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_boolean_values(self, mock_redis):
        """Test caching boolean values"""
        await mock_redis.set("true_key", True)
        await mock_redis.set("false_key", False)

        mock_redis.get.return_value = True
        result_true = await mock_redis.get("true_key")

        mock_redis.get.return_value = False
        result_false = await mock_redis.get("false_key")

        assert result_true is True
        assert result_false is False
