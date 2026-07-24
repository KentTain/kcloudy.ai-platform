"""文档库权限判定引擎单元测试

测试 PermissionService（高层门面）和 DocumentPermissionChecker（Protocol 实现）。
所有测试使用 mock DB 查询，不依赖真实数据库。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.permission_service import PermissionService, DocumentPermissionChecker
from document.models.enums import LibraryMemberRole, PermissionLevel
from framework.permission.engine import PermissionEngine, PermissionCheckResult


# ---------------------------------------------------------------------------
# 辅助工具
# ---------------------------------------------------------------------------


def _make_service() -> PermissionService:
    """创建 PermissionService 实例"""
    return PermissionService()


def _make_checker(session: AsyncMock, library_id: str = "lib-1") -> DocumentPermissionChecker:
    """创建 DocumentPermissionChecker 实例"""
    return DocumentPermissionChecker(session=session, library_id=library_id)


# ---------------------------------------------------------------------------
# PermissionService 核心判定测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPermissionService:
    """权限判定引擎测试（高层门面）"""

    async def test_owner_has_full_editable(self):
        """owner 全部资源可编辑"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "editable"

    async def test_admin_has_full_editable(self):
        """admin 全部资源可编辑"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.ADMIN):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert result == "editable"

    async def test_member_permission_from_acl_inheritance(self):
        """普通成员通过继承链计算权限，取最高等级"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="editable"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "editable"

    async def test_no_permission_returns_none(self):
        """非成员无权限返回 none"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=None), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="none"):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "none"

    async def test_deny_acl_overrides_allow(self):
        """显式 deny 覆盖继承 allow"""
        service = _make_service()
        result = service._merge_permission_levels(inherited="editable", direct_deny=True)
        assert result == "none"

    async def test_highest_permission_wins(self):
        """多个权限来源取最高等级"""
        service = _make_service()
        result = service._pick_highest_level(["readonly", "editable", "none"])
        assert result == "editable"

    async def test_all_deny_returns_none(self):
        """所有来源均为 none/deny 返回 none"""
        service = _make_service()
        result = service._pick_highest_level(["none", "none", "none"])
        assert result == "none"

    async def test_permission_not_amplified_for_non_member(self):
        """非文档库成员返回 none（不放大权限）"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=None):
            result = await service.check_permission(
                session, user_id="outsider", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "none"

    async def test_inheritance_truncated_when_disabled(self):
        """关闭继承后父级权限截断 — mock 返回 none 验证流程"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="none"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
            assert result == "none"

    async def test_member_with_readonly(self):
        """普通成员获得 readonly 权限"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "readonly"

    async def test_contributor_role(self):
        """contributor 角色走普通成员判定流程"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.CONTRIBUTOR), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="editable"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert result == "editable"


# ---------------------------------------------------------------------------
# DocumentPermissionChecker（Protocol 实现）测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDocumentPermissionChecker:
    """DocumentPermissionChecker 测试（实现 PermissionEngineProtocol）"""

    async def test_implements_protocol(self):
        """DocumentPermissionChecker 满足 PermissionEngineProtocol"""
        checker = _make_checker(AsyncMock())
        assert isinstance(checker, DocumentPermissionChecker)
        # 验证有 check_resource_permission 方法
        assert hasattr(checker, "check_resource_permission")

    async def test_owner_returns_editable(self):
        """owner 角色返回 editable"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "editable"

    async def test_non_member_returns_none(self):
        """非成员返回 none"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=None):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "none"

    async def test_member_inherited_permission(self):
        """普通成员返回继承链计算的权限"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"), \
             patch.object(checker, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "readonly"


# ---------------------------------------------------------------------------
# PermissionEngine 编排测试（第2层 + 第3层叠加）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPermissionEngineIntegration:
    """PermissionEngine 编排第2层 + 第3层"""

    async def test_resource_deny_blocks_all(self):
        """资源权限 none/deny 直接拒绝，不查 Policy"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=None):
            engine = PermissionEngine(resource_checker=checker)
            result = await engine.check(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert isinstance(result, PermissionCheckResult)
        assert result.allowed is False
        assert result.resource_permission == "none"

    async def test_policy_deny_overrides_resource_allow(self):
        """Policy deny 覆盖资源 allow"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            engine = PermissionEngine(resource_checker=checker)
            deny_policy = {
                "id": "p-deny-1",
                "effect": "deny",
                "enabled": True,
                "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}],
            }
            result = await engine.check(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
                policies=[deny_policy],
            )
        assert result.allowed is False
        assert result.denied_by_policy is True
        assert result.policy_effect == "deny"

    async def test_resource_readonly_blocks_write_operation(self):
        """readonly 权限阻止写操作"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"), \
             patch.object(checker, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            engine = PermissionEngine(resource_checker=checker)
            result = await engine.check(
                user_id="u1", resource_type="document", resource_id="d1", operation="edit",
            )
        assert result.allowed is False
        assert result.resource_permission == "readonly"

    async def test_full_permission_with_no_policy(self):
        """资源 editable 且无 Policy → 允许"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            engine = PermissionEngine(resource_checker=checker)
            result = await engine.check(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result.allowed is True
        assert result.resource_permission == "editable"


# ---------------------------------------------------------------------------
# 辅助方法测试
# ---------------------------------------------------------------------------


class TestHelperMethods:
    """辅助方法单元测试"""

    def test_pick_highest_level_editable_wins(self):
        """editable > readonly > none"""
        service = _make_service()
        assert service._pick_highest_level(["none", "readonly", "editable"]) == "editable"

    def test_pick_highest_level_readonly_wins_over_none(self):
        """readonly > none"""
        service = _make_service()
        assert service._pick_highest_level(["none", "readonly"]) == "readonly"

    def test_pick_highest_level_empty_list(self):
        """空列表返回 none"""
        service = _make_service()
        assert service._pick_highest_level([]) == "none"

    def test_merge_permission_levels_deny_overrides(self):
        """deny 覆盖继承 allow"""
        service = _make_service()
        assert service._merge_permission_levels(inherited="editable", direct_deny=True) == "none"

    def test_merge_permission_levels_no_deny(self):
        """无 deny 返回继承权限"""
        service = _make_service()
        assert service._merge_permission_levels(inherited="readonly", direct_deny=False) == "readonly"

    def test_permission_level_map(self):
        """PermissionLevel 枚举映射到字符串"""
        from document.services.permission_service import LEVEL_MAP
        assert LEVEL_MAP[PermissionLevel.UNCONFIGURED] == "none"
        assert LEVEL_MAP[PermissionLevel.NONE] == "none"
        assert LEVEL_MAP[PermissionLevel.READONLY] == "readonly"
        assert LEVEL_MAP[PermissionLevel.EDITABLE] == "editable"


# ---------------------------------------------------------------------------
# diagnose 排障方法测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDiagnose:
    """权限排障方法测试"""

    async def test_diagnose_editable_permission(self):
        """editable 权限排障输出"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            diag = await service.diagnose(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert diag["allowed"] is True
        assert diag["resource_permission"] == "editable"

    async def test_diagnose_readonly_for_read_op(self):
        """readonly + read 操作 → 允许"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            diag = await service.diagnose(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
        assert diag["allowed"] is True
        assert diag["resource_permission"] == "readonly"

    async def test_diagnose_readonly_for_write_op(self):
        """readonly + edit 操作 → 拒绝"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER), \
             patch.object(service, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"), \
             patch.object(service, "_has_direct_deny", new_callable=AsyncMock, return_value=False):
            diag = await service.diagnose(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert diag["allowed"] is False
        assert diag["resource_permission"] == "readonly"
