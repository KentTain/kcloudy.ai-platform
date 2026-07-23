"""
Framework 权限引擎基础设施

提供：
- Policy 求值器（deny 优先，JSON 条件匹配）
- 权限判定引擎（编排第2层资源权限 + 第3层 Policy）
- 审计写入辅助（延迟导入 iam，避免循环依赖）
"""

from framework.permission.policy_evaluator import PolicyEvaluator, PolicyResult
from framework.permission.engine import PermissionEngine, PermissionEngineProtocol, PermissionCheckResult

__all__ = [
    "PolicyEvaluator",
    "PolicyResult",
    "PermissionEngine",
    "PermissionEngineProtocol",
    "PermissionCheckResult",
]
