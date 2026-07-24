"""文档库权限判定引擎单元测试

测试 PermissionService（高层门面）和 DocumentPermissionChecker（Protocol 实现）。
所有测试使用 mock DB 查询，不依赖真实数据库。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.permission_service import (
    ACTION_LEVEL_MAP,
    PermissionService,
    DocumentPermissionChecker,
    _pick_highest_level,
)
from document.models.enums import LibraryMemberRole, ResourceAclEffect
from framework.permission.engine import (
    PermissionCheckResult,
    PermissionEngine,
    PermissionEngineProtocol,
)


# ---------------------------------------------------------------------------
# 辅助工具
# ---------------------------------------------------------------------------


def _make_service() -> PermissionService:
    """创建 PermissionService 实例"""
    return PermissionService()


def _make_checker(session: AsyncMock, library_id: str = "lib-1") -> DocumentPermissionChecker:
    """创建 DocumentPermissionChecker 实例"""
    return DocumentPermissionChecker(session=session, library_id=library_id)


def _make_mock_acl(effect: str, action: str) -> MagicMock:
    """构造 mock ACL 对象"""
    acl = MagicMock()
    acl.effect = effect
    acl.action = action
    return acl


def _setup_session_with_acls(session: AsyncMock, acls: list[MagicMock]) -> None:
    """配置 session 返回指定 ACL 列表"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = acls
    mock_result.scalars.return_value = mock_scalars
    session.execute = AsyncMock(return_value=mock_result)


# ---------------------------------------------------------------------------
# PermissionService 门面委托测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPermissionService:
    """权限判定引擎测试（高层门面 - 委托 DocumentPermissionChecker）"""

    async def test_no_policies_delegates_to_checker(self):
        """无 policies 时委托给 DocumentPermissionChecker"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="editable",
        ):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "editable"

    async def test_with_policies_uses_engine(self):
        """有 policies 时委托给 PermissionEngine"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="editable",
        ):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
                policies=[{"id": "p1", "effect": "allow", "enabled": True, "conditions": []}],
            )
        assert result == "editable"

    async def test_engine_deny_returns_none(self):
        """PermissionEngine deny 时返回 none"""
        service = _make_service()
        session = AsyncMock()
        deny_policy = {
            "id": "p-deny-1",
            "effect": "deny",
            "enabled": True,
            "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}],
        }
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="editable",
        ):
            result = await service.check_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
                policies=[deny_policy],
            )
        assert result == "none"

    async def test_permission_not_amplified_for_non_member(self):
        """非文档库成员返回 none（不放大权限）"""
        service = _make_service()
        session = AsyncMock()
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="none",
        ):
            result = await service.check_permission(
                session, user_id="outsider", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "none"


# ---------------------------------------------------------------------------
# DocumentPermissionChecker（Protocol 实现）测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDocumentPermissionChecker:
    """DocumentPermissionChecker 测试（实现 PermissionEngineProtocol）"""

    async def test_implements_protocol(self):
        """DocumentPermissionChecker 满足 PermissionEngineProtocol"""
        checker = _make_checker(AsyncMock())
        assert isinstance(checker, PermissionEngineProtocol)

    async def test_owner_returns_editable(self):
        """owner 角色返回 editable"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "editable"

    async def test_admin_returns_editable(self):
        """admin 角色返回 editable"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.ADMIN):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="edit",
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
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "readonly"

    async def test_member_with_readonly(self):
        """普通成员获得 readonly 权限"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "readonly"

    async def test_contributor_role(self):
        """contributor 角色走普通成员判定流程"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.CONTRIBUTOR), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="editable"):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="edit",
            )
        assert result == "editable"

    async def test_inheritance_truncated_when_disabled(self):
        """关闭继承后资源权限截断 — 验证不查父级 ACL 场景

        当 folder 的 acl_inherit_enabled=False 时，_compute_resource_permission
        只查当前资源的 ACL，不查父级，若无直授权则返回 none。
        """
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="none"):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "none"

    async def test_deny_acl_short_circuits_to_none(self):
        """deny ACL 短路返回 none"""
        session = AsyncMock()
        checker = _make_checker(session)
        with patch.object(checker, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="none"):
            result = await checker.check_resource_permission(
                user_id="u1", resource_type="document", resource_id="d1", operation="edit",
            )
        assert result == "none"


# ---------------------------------------------------------------------------
# _compute_resource_permission 内部逻辑测试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestComputeResourcePermission:
    """_compute_resource_permission 内部逻辑测试（C2 + C3 修复验证）"""

    async def test_deny_acl_short_circuits(self):
        """deny ACL 短路返回 none，即使后续有 allow"""
        session = AsyncMock()
        checker = _make_checker(session)
        acls = [
            _make_mock_acl(ResourceAclEffect.ALLOW, "edit"),
            _make_mock_acl(ResourceAclEffect.DENY, "edit"),
        ]
        _setup_session_with_acls(session, acls)
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="edit",
        )
        assert result == "none"

    async def test_allow_read_action_maps_to_readonly(self):
        """allow + read action 映射为 readonly"""
        session = AsyncMock()
        checker = _make_checker(session)
        acls = [_make_mock_acl(ResourceAclEffect.ALLOW, "read")]
        _setup_session_with_acls(session, acls)
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="read",
        )
        assert result == "readonly"

    async def test_allow_edit_action_maps_to_editable(self):
        """allow + edit action 映射为 editable"""
        session = AsyncMock()
        checker = _make_checker(session)
        acls = [_make_mock_acl(ResourceAclEffect.ALLOW, "edit")]
        _setup_session_with_acls(session, acls)
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="edit",
        )
        assert result == "editable"

    async def test_no_acls_returns_none(self):
        """无 ACL 记录返回 none"""
        session = AsyncMock()
        checker = _make_checker(session)
        _setup_session_with_acls(session, [])
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="read",
        )
        assert result == "none"

    async def test_mixed_readonly_and_editable_takes_editable(self):
        """多个 allow ACL 取最高等级"""
        session = AsyncMock()
        checker = _make_checker(session)
        acls = [
            _make_mock_acl(ResourceAclEffect.ALLOW, "read"),
            _make_mock_acl(ResourceAclEffect.ALLOW, "edit"),
        ]
        _setup_session_with_acls(session, acls)
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="edit",
        )
        assert result == "editable"

    async def test_unknown_action_defaults_to_readonly(self):
        """未知 action 默认映射为 readonly"""
        session = AsyncMock()
        checker = _make_checker(session)
        acls = [_make_mock_acl(ResourceAclEffect.ALLOW, "unknown_action")]
        _setup_session_with_acls(session, acls)
        result = await checker._compute_resource_permission(
            user_id="u1", resource_type="document", resource_id="d1", operation="unknown_action",
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
             patch.object(checker, "_compute_resource_permission", new_callable=AsyncMock, return_value="readonly"):
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
# 辅助函数测试
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """模块级辅助函数单元测试"""

    def test_pick_highest_level_editable_wins(self):
        """editable > readonly > none"""
        assert _pick_highest_level(["none", "readonly", "editable"]) == "editable"

    def test_pick_highest_level_readonly_wins_over_none(self):
        """readonly > none"""
        assert _pick_highest_level(["none", "readonly"]) == "readonly"

    def test_pick_highest_level_empty_list(self):
        """空列表返回 none"""
        assert _pick_highest_level([]) == "none"

    def test_pick_highest_level_all_none(self):
        """所有来源均为 none 返回 none"""
        assert _pick_highest_level(["none", "none", "none"]) == "none"

    def test_action_level_map_readonly_actions(self):
        """read/preview/download 映射到 readonly"""
        assert ACTION_LEVEL_MAP["read"] == "readonly"
        assert ACTION_LEVEL_MAP["preview"] == "readonly"
        assert ACTION_LEVEL_MAP["download"] == "readonly"

    def test_action_level_map_editable_actions(self):
        """edit/delete/write 映射到 editable"""
        assert ACTION_LEVEL_MAP["edit"] == "editable"
        assert ACTION_LEVEL_MAP["delete"] == "editable"
        assert ACTION_LEVEL_MAP["write"] == "editable"


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
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="editable",
        ), patch.object(
            DocumentPermissionChecker, "_get_member_role",
            new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER,
        ):
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
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="readonly",
        ), patch.object(
            DocumentPermissionChecker, "_get_member_role",
            new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER,
        ):
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
        with patch.object(
            DocumentPermissionChecker, "check_resource_permission",
            new_callable=AsyncMock, return_value="readonly",
        ), patch.object(
            DocumentPermissionChecker, "_get_member_role",
            new_callable=AsyncMock, return_value=LibraryMemberRole.VIEWER,
        ):
            diag = await service.diagnose(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert diag["allowed"] is False
        assert diag["resource_permission"] == "readonly"
