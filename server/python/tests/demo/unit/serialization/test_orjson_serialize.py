"""orjson Serialization Tests"""

import pytest
import orjson
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class TestOrjsonSerialize:
    """orjson serialization tests"""

    def test_serialize_simple_dict(self):
        """Test serializing a simple dictionary"""
        data = {"key": "value", "number": 123}
        result = orjson.dumps(data)
        assert isinstance(result, bytes)
        assert b'"key"' in result

    def test_serialize_nested_dict(self):
        """Test serializing nested dictionary"""
        data = {"outer": {"inner": {"value": 123}}}
        result = orjson.dumps(data)
        parsed = orjson.loads(result)
        assert parsed == data

    def test_serialize_datetime(self):
        """Test serializing datetime object"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = orjson.dumps(dt)
        parsed = orjson.loads(result)
        assert "2024-01-15" in parsed

    def test_serialize_date(self):
        """Test serializing date object"""
        d = date(2024, 1, 15)
        result = orjson.dumps(d)
        parsed = orjson.loads(result)
        assert "2024-01-15" in parsed

    def test_serialize_list(self):
        """Test serializing list"""
        data = [1, 2, 3, "four", True]
        result = orjson.dumps(data)
        parsed = orjson.loads(result)
        assert parsed == data

    def test_serialize_none(self):
        """Test serializing None"""
        result = orjson.dumps(None)
        parsed = orjson.loads(result)
        assert parsed is None

    def test_serialize_bool(self):
        """Test serializing boolean values"""
        assert orjson.loads(orjson.dumps(True)) is True
        assert orjson.loads(orjson.dumps(False)) is False

    def test_serialize_decimal(self):
        """Test serializing Decimal"""
        d = Decimal("123.45")
        # orjson requires a default handler for Decimal
        result = orjson.dumps(d, default=lambda x: str(x))
        parsed = orjson.loads(result)
        assert parsed == "123.45"

    def test_serialize_uuid(self):
        """Test serializing UUID"""
        u = UUID("12345678-1234-5678-1234-567812345678")
        result = orjson.dumps(u)
        parsed = orjson.loads(result)
        assert "12345678" in parsed
