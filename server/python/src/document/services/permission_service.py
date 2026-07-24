"""文档库权限判定引擎

判定流程（见迁移方案 §3.1 第 2 层）：
  1. owner/admin 命中 → 全部资源可编辑
  2. 计算 全员权限 + 自定义权限组 + 用户直授权，取最高等级
  3. 沿继承链计算资源权限（文档库根 → 目录 → 文件），取最高等级
  4. 显式 deny 覆盖继承 allow（在 _compute_resource_permission 中统一处理）
  5. 叠加第 3 层企业 Policy（由 framework PermissionEngine 编排）

精简实现：不迁移 kbhub permission.py 的 7.8 万行 Alon 平台特有逻辑。

设计：
  - PermissionService：高层门面服务，接收 session + library_id + 详细参数，
    委托 DocumentPermissionChecker 执行判定
  - DocumentPermissionChecker：实现 PermissionEngineProtocol（无 session/library_id），
    持有 session 和 library_id 引用，供 PermissionEngine 编排第2+3层
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryMember, ResourceAcl
from document.models.enums import (
    LibraryMemberRole,
    LibraryMemberStatus,
    ResourceAclEffect,
    ResourceAclStatus,
)
from framework.permission.engine import (
    PermissionCheckResult,
    PermissionEngine,
    PermissionEngineProtocol,
)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 只读操作集合
READ_OPERATIONS: set[str] = {"read", "preview"}

# 权限等级优先级（用于 _pick_highest_level）
_LEVEL_PRIORITY: dict[str, int] = {
    "editable": 2,
    "readonly": 1,
    "none": 0,
    "deny": -1,
}

# ACL action → 权限等级映射
ACTION_LEVEL_MAP: dict[str, str] = {
    "read": "readonly",
    "preview": "readonly",
    "download": "readonly",  # 下载归为只读
    "edit": "editable",
    "delete": "editable",
    "write": "editable",
}


# ---------------------------------------------------------------------------
# DocumentPermissionChecker — 第2层资源权限判定器
# ---------------------------------------------------------------------------


class DocumentPermissionChecker(PermissionEngineProtocol):
    """document 第2层资源权限判定器（实现 framework Protocol）

    持有 session 和 library_id 引用，供 PermissionEngine 编排第2+3层。
    Protocol 签名无 session/library_id，通过 __init__ 注入。
    """

    def __init__(self, session: AsyncSession, library_id: str) -> None:
        self._session = session
        self._library_id = library_id

    async def check_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """实现 Protocol：供 framework PermissionEngine 调用

        Returns: editable / readonly / none
        """
        # 1. 查成员角色
        member_role = await self._get_member_role(user_id)

        # 非成员直接 none
        if member_role is None:
            return "none"

        # 2. owner/admin 全可编辑
        if member_role in (LibraryMemberRole.OWNER, LibraryMemberRole.ADMIN):
            return "editable"

        # 3. 普通成员：计算资源权限（deny 在 _compute_resource_permission 中统一处理）
        return await self._compute_resource_permission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            operation=operation,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _get_member_role(self, user_id: str) -> str | None:
        """获取用户在文档库的成员角色"""
        stmt = select(LibraryMember.role).where(
            LibraryMember.library_id == self._library_id,
            LibraryMember.user_id == user_id,
            LibraryMember.status == LibraryMemberStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _compute_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """沿继承链计算权限（文档库根 → 目录 → 文件），取最高等级。

        deny ACL 具有最高优先级，遇到即短路返回 "none"。
        非 deny ACL 根据 action 映射权限等级（ACTION_LEVEL_MAP）。
        """
        stmt = select(ResourceAcl).where(
            ResourceAcl.library_id == self._library_id,
            ResourceAcl.resource_id.in_([self._library_id, resource_id]),
            ResourceAcl.subject_id == user_id,
            ResourceAcl.action == operation,
            ResourceAcl.status == ResourceAclStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        acls = list(result.scalars().all())

        levels: list[str] = []
        for acl in acls:
            if acl.effect == ResourceAclEffect.DENY:
                # deny 具有最高优先级，短路返回
                return "none"
            level = ACTION_LEVEL_MAP.get(acl.action, "readonly")
            levels.append(level)

        if not levels:
            return "none"
        return _pick_highest_level(levels)


# ---------------------------------------------------------------------------
# PermissionService — 高层门面服务
# ---------------------------------------------------------------------------


class PermissionService:
    """文档库权限判定服务（高层门面）

    对外 API：check_permission() + diagnose()
    委托 DocumentPermissionChecker 执行实际判定。
    """

    async def check_permission(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        policies: list[dict] | None = None,
    ) -> str:
        """判定用户对资源的权限等级。

        若传入 policies，叠加第3层 Policy（由 PermissionEngine 编排）。

        Returns: editable / readonly / none
        """
        checker = DocumentPermissionChecker(session=session, library_id=library_id)

        if policies:
            # 完整编排：第2层 + 第3层
            engine = PermissionEngine(resource_checker=checker)
            result = await engine.check(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                operation=operation,
                policies=policies,
            )
            # 返回资源权限等级（而非 allowed/denied），保持接口语义
            if not result.allowed:
                return "none"
            return result.resource_permission

        # 仅第2层判定：委托给 checker
        return await checker.check_resource_permission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            operation=operation,
        )

    async def check_permission_full(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        policies: list[dict] | None = None,
    ) -> PermissionCheckResult:
        """完整权限判定，返回 PermissionCheckResult（含 Policy 命中信息）"""
        checker = DocumentPermissionChecker(session=session, library_id=library_id)
        engine = PermissionEngine(resource_checker=checker)
        return await engine.check(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            operation=operation,
            policies=policies,
        )

    async def diagnose(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> dict:
        """权限排障：输出最终允许/拒绝及命中原因"""
        checker = DocumentPermissionChecker(session=session, library_id=library_id)
        perm = await checker.check_resource_permission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            operation=operation,
        )
        allowed = perm == "editable" or (perm == "readonly" and operation in READ_OPERATIONS)
        member_role = await checker._get_member_role(user_id)
        return {
            "allowed": allowed,
            "resource_permission": perm,
            "reasons": [
                f"最终权限等级={perm}",
                f"操作={operation}",
                f"成员身份={member_role}",
            ],
        }


# ---------------------------------------------------------------------------
# 模块级辅助函数
# ---------------------------------------------------------------------------


def _pick_highest_level(levels: list[str]) -> str:
    """多个权限来源取最高等级"""
    if not levels:
        return "none"
    return max(levels, key=lambda lv: _LEVEL_PRIORITY.get(lv, 0))


permission_service = PermissionService()
