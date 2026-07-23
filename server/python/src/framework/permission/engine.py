"""
权限判定引擎

编排三层权限判定：
  第1层 IAM RBAC（功能权限，由 module 声明，控制器层校验，不在此处）
  第2层 业务模块资源权限（由各模块实现 PermissionEngineProtocol）
  第3层 企业 Policy（Policy 求值器，deny 优先）

判定流程：资源权限 -> Policy 求值 -> 最终允许/拒绝
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from framework.permission.policy_evaluator import PolicyEvaluator, PolicyResult


@runtime_checkable
class PermissionEngineProtocol(Protocol):
    """第2层资源权限判定协议（各业务模块实现）"""

    async def check_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """返回资源权限等级：editable / readonly / none / deny"""
        ...


@dataclass
class PermissionCheckResult:
    """权限判定结果"""

    allowed: bool
    resource_permission: str = "none"
    policy_effect: str | None = None
    denied_by_policy: bool = False
    reasons: list[str] = field(default_factory=list)


class PermissionEngine:
    """权限判定引擎（编排第2层 + 第3层）"""

    def __init__(
        self,
        resource_checker: PermissionEngineProtocol,
        policy_evaluator: PolicyEvaluator | None = None,
    ):
        self.resource_checker = resource_checker
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()

    async def check(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        policies: list[dict] | None = None,
        context: dict | None = None,
    ) -> PermissionCheckResult:
        """
        执行权限判定。

        Args:
            user_id: 用户ID
            resource_type: 资源类型（document/folder/library 等）
            resource_id: 资源ID
            operation: 操作（read/preview/download/edit/delete）
            policies: 当前租户启用的 Policy 列表
            context: Policy 求值上下文

        Returns:
            PermissionCheckResult
        """
        reasons: list[str] = []
        ctx = context or {}
        ctx.setdefault("resource_type", resource_type)
        ctx.setdefault("operation", operation)
        ctx.setdefault("user_id", user_id)

        # 第2层：资源权限
        resource_perm = await self.resource_checker.check_resource_permission(
            user_id, resource_type, resource_id, operation
        )
        reasons.append(f"资源权限={resource_perm}")

        # 资源权限为 none/deny 直接拒绝
        if resource_perm in ("none", "deny"):
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                reasons=reasons,
            )

        # readonly 仅允许读类操作
        read_operations = {"read", "preview"}
        if resource_perm == "readonly" and operation not in read_operations:
            reasons.append(f"readonly 不允许操作={operation}")
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                reasons=reasons,
            )

        # 第3层：Policy 求值（deny 优先）
        policy_result: PolicyResult = self.policy_evaluator.evaluate(policies or [], ctx)
        if policy_result.effect == "deny":
            reasons.append(f"Policy deny 命中={policy_result.matched_policy_id}")
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                policy_effect="deny",
                denied_by_policy=True,
                reasons=reasons,
            )

        return PermissionCheckResult(
            allowed=True,
            resource_permission=resource_perm,
            policy_effect=policy_result.effect,
            reasons=reasons,
        )
