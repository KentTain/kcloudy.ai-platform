"""
企业 Policy 求值器

求值租户级安全策略，deny 优先于所有 allow。

条件格式（JSON 结构化）：
    {"field": "resource_type", "op": "eq", "value": "document"}

支持操作符：eq / ne / in / not_in / contains
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyResult:
    """Policy 求值结果"""

    effect: str | None  # "allow" / "deny" / None
    matched_policy_id: str | None = None
    matched_conditions: list[dict] | None = None


class PolicyEvaluator:
    """企业 Policy 求值器"""

    def evaluate(self, policies: list[dict], context: dict[str, Any]) -> PolicyResult:
        """
        求值 Policy 列表，deny 优先。

        Args:
            policies: Policy 列表，每项含 id/effect/enabled/conditions
            context: 求值上下文（resource_type/operation/user_id 等）

        Returns:
            PolicyResult：deny 优先，无命中返回 effect=None
        """
        allow_hit = None

        for policy in policies:
            if not policy.get("enabled", True):
                continue

            conditions = policy.get("conditions", [])
            if self._match_all(conditions, context):
                if policy.get("effect") == "deny":
                    return PolicyResult(
                        effect="deny",
                        matched_policy_id=policy.get("id"),
                        matched_conditions=conditions,
                    )
                if allow_hit is None and policy.get("effect") == "allow":
                    allow_hit = PolicyResult(
                        effect="allow",
                        matched_policy_id=policy.get("id"),
                        matched_conditions=conditions,
                    )

        return allow_hit or PolicyResult(effect=None)

    def _match_all(self, conditions: list[dict], context: dict[str, Any]) -> bool:
        """所有条件均匹配才返回 True"""
        if not conditions:
            return True
        return all(self._match_one(cond, context) for cond in conditions)

    def _match_one(self, condition: dict, context: dict[str, Any]) -> bool:
        """匹配单个条件"""
        field = condition.get("field")
        op = condition.get("op", "eq")
        expected = condition.get("value")
        actual = context.get(field)

        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "contains":
            return expected in (actual or [])
        return False
