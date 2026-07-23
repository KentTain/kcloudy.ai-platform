"""
权限判定引擎单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from framework.permission.engine import PermissionEngine, PermissionEngineProtocol, PermissionCheckResult


class FakeResourcePermissionChecker:
    """测试用第2层资源权限判定器"""

    def __init__(self, result: str):
        self._result = result

    async def check_resource_permission(self, user_id: str, resource_type: str, resource_id: str, operation: str) -> str:
        return self._result


@pytest.mark.asyncio
class TestPermissionEngine:
    """权限判定引擎测试"""

    async def test_deny_by_policy_overrides_resource_allow(self):
        """Policy deny 覆盖资源 allow"""
        checker = FakeResourcePermissionChecker("editable")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect="deny", matched_policy_id="p1")

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="download",
            policies=[],
        )
        assert result.allowed is False
        assert result.denied_by_policy is True

    async def test_resource_deny_blocks(self):
        """资源权限 deny 阻断"""
        checker = FakeResourcePermissionChecker("none")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is False
        assert result.resource_permission == "none"

    async def test_allow_when_resource_editable_and_no_policy_deny(self):
        """资源可编辑且无 Policy deny 则允许"""
        checker = FakeResourcePermissionChecker("editable")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is True

    async def test_readonly_blocks_write_operations(self):
        """readonly 仅允许读类操作"""
        checker = FakeResourcePermissionChecker("readonly")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="download",
            policies=[],
        )
        assert result.allowed is False
        assert result.resource_permission == "readonly"

    async def test_readonly_allows_read_operations(self):
        """readonly 允许读类操作"""
        checker = FakeResourcePermissionChecker("readonly")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is True

    async def test_policy_allow_does_not_override_resource_deny(self):
        """Policy allow 不能覆盖资源 deny"""
        checker = FakeResourcePermissionChecker("none")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect="allow", matched_policy_id="p1")

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is False
