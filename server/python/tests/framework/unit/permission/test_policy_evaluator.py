"""
企业 Policy 求值器单元测试
"""
import pytest
from framework.permission.policy_evaluator import PolicyEvaluator, PolicyResult


class TestPolicyEvaluator:
    """Policy 求值器测试"""

    def test_deny_policy_overrides_allow(self):
        """deny 优先于所有 allow"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "allow", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
            {"id": "p2", "effect": "deny", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        result = evaluator.evaluate(policies, {"resource_type": "document"})
        assert result.effect == "deny"
        assert result.matched_policy_id == "p2"

    def test_no_policy_returns_none(self):
        """无 Policy 命中返回 None"""
        evaluator = PolicyEvaluator()
        result = evaluator.evaluate([], {"resource_type": "document"})
        assert result.effect is None

    def test_allow_when_only_allow_matches(self):
        """仅有 allow 命中时返回 allow"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "allow", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        result = evaluator.evaluate(policies, {"resource_type": "document"})
        assert result.effect == "allow"

    def test_condition_all_must_match(self):
        """所有条件均匹配才命中"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [
                {"field": "resource_type", "op": "eq", "value": "document"},
                {"field": "operation", "op": "eq", "value": "download"},
            ]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "document", "operation": "read"}).effect is None
        assert evaluator.evaluate(policies, {"resource_type": "document", "operation": "download"}).effect == "deny"

    def test_disabled_policy_not_evaluated(self):
        """停用的 Policy 不参与求值"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "enabled": False, "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect is None

    def test_in_operator(self):
        """in 操作符"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [{"field": "resource_type", "op": "in", "value": ["document", "folder"]}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect == "deny"
        assert evaluator.evaluate(policies, {"resource_type": "library"}).effect is None

    def test_ne_operator(self):
        """ne 操作符"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "allow", "conditions": [{"field": "resource_type", "op": "ne", "value": "document"}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "folder"}).effect == "allow"
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect is None

    def test_not_in_operator(self):
        """not_in 操作符"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [{"field": "resource_type", "op": "not_in", "value": ["document", "folder"]}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "library"}).effect == "deny"
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect is None

    def test_contains_operator(self):
        """contains 操作符"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [{"field": "tags", "op": "contains", "value": "confidential"}]},
        ]
        assert evaluator.evaluate(policies, {"tags": ["confidential", "internal"]}).effect == "deny"
        assert evaluator.evaluate(policies, {"tags": ["public"]}).effect is None

    def test_no_conditions_always_matches(self):
        """无条件的 Policy 总是命中"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": []},
        ]
        result = evaluator.evaluate(policies, {"resource_type": "document"})
        assert result.effect == "deny"
