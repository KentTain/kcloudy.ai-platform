"""
安装任务消费者单元测试

测试消息解析函数 _parse_message_data：
- 新格式（扁平字段）：task_id/plugin_id 直接在消息中
- 旧格式（payload 嵌套）：payload 为 JSON 字符串或 dict
- auto_start 字符串转布尔
- 边界场景：空消息、缺字段、无效 JSON
"""

from __future__ import annotations

import uuid

import pytest

from ai.listeners.services.queue.install_task_consumer import _parse_message_data


class TestParseMessageDataNewFormat:
    """新格式（扁平字段）解析测试"""

    def test_parse_flat_message_with_auto_start_true(self):
        """测试解析扁平消息，auto_start 为字符串 True"""
        task_id = str(uuid.uuid4())
        message_data = {
            "task_type": "plugin_install",
            "task_id": task_id,
            "tenant_id": "test-tenant",
            "plugin_id": "test/plugin",
            "plugin_unique_identifier": "test/plugin:1.0.0@abc",
            "auto_start": "True",
        }

        result = _parse_message_data(message_data)

        assert result is not None
        assert result["task_id"] == task_id
        assert result["tenant_id"] == "test-tenant"
        assert result["plugin_id"] == "test/plugin"
        # auto_start 字符串应被转为布尔
        assert result["auto_start"] is True

    def test_parse_flat_message_with_auto_start_false(self):
        """测试解析扁平消息，auto_start 为字符串 False"""
        message_data = {
            "task_id": str(uuid.uuid4()),
            "tenant_id": "test-tenant",
            "plugin_id": "test/plugin",
            "auto_start": "False",
        }

        result = _parse_message_data(message_data)

        assert result is not None
        assert result["auto_start"] is False

    def test_parse_flat_message_without_auto_start(self):
        """测试解析扁平消息，无 auto_start 字段"""
        message_data = {
            "task_id": str(uuid.uuid4()),
            "tenant_id": "test-tenant",
            "plugin_id": "test/plugin",
        }

        result = _parse_message_data(message_data)

        assert result is not None
        assert "auto_start" not in result or result.get("auto_start") is None


class TestParseMessageDataLegacyPayloadFormat:
    """旧格式（payload 嵌套）解析测试"""

    def test_parse_payload_json_string(self):
        """测试解析 payload 为 JSON 字符串"""
        import json

        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "tenant_id": "test-tenant",
            "plugin_id": "test/plugin",
            "plugin_unique_identifier": "test/plugin@1.0.0",
            "auto_start": True,
        }
        message_data = {
            "task_type": "plugin_install",
            "payload": json.dumps(payload),
        }

        result = _parse_message_data(message_data)

        assert result is not None
        assert result["task_id"] == task_id
        assert result["auto_start"] is True

    def test_parse_payload_dict(self):
        """测试解析 payload 为 dict"""
        task_id = str(uuid.uuid4())
        message_data = {
            "task_type": "plugin_install",
            "payload": {
                "task_id": task_id,
                "tenant_id": "test-tenant",
                "plugin_id": "test/plugin",
            },
        }

        result = _parse_message_data(message_data)

        assert result is not None
        assert result["task_id"] == task_id
        assert result["plugin_id"] == "test/plugin"

    def test_parse_payload_invalid_json_returns_none(self):
        """测试 payload 为无效 JSON 时返回 None"""
        message_data = {
            "task_type": "plugin_install",
            "payload": "invalid-json-string",
        }

        result = _parse_message_data(message_data)

        assert result is None


class TestParseMessageDataEdgeCases:
    """边界场景测试"""

    def test_parse_empty_dict_returns_none(self):
        """测试空字典返回 None"""
        assert _parse_message_data({}) is None

    def test_parse_none_returns_none(self):
        """测试 None 返回 None"""
        assert _parse_message_data(None) is None

    def test_parse_missing_required_fields_returns_none(self):
        """测试缺少 task_id 或 plugin_id 返回 None"""
        # 仅有 task_type，无 task_id/plugin_id/payload
        message_data = {"task_type": "plugin_install"}

        result = _parse_message_data(message_data)

        assert result is None

    def test_parse_missing_plugin_id_returns_none(self):
        """测试仅有 task_id 缺 plugin_id 返回 None"""
        message_data = {
            "task_id": str(uuid.uuid4()),
            "tenant_id": "test-tenant",
            # 缺少 plugin_id
        }

        result = _parse_message_data(message_data)

        assert result is None

    def test_parse_empty_payload_returns_none(self):
        """测试空 payload 字符串退化为新格式判断"""
        # payload 为空字符串时，走新格式分支；但缺少 task_id/plugin_id，返回 None
        message_data = {
            "task_type": "plugin_install",
            "payload": "",
        }

        result = _parse_message_data(message_data)

        assert result is None
