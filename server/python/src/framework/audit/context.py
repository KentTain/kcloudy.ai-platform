"""
审计上下文

定义审计日志所需的数据结构。
"""

from dataclasses import dataclass


@dataclass
class AuditContext:
    """
    审计上下文，用于传递审计日志所需信息

    Attributes:
        module: 模块名称，如 iam, tenant, ai
        resource: 资源类型，如 user, role, organization
        action: 操作类型，如 create, update, delete
        resource_id: 资源 ID
        resource_name: 资源名称（用于展示）
        before_data: 操作前数据
        after_data: 操作后数据
        detail_extra: 额外上下文信息
    """

    # 基础信息（必填）
    module: str
    resource: str
    action: str

    # 资源信息（必填）
    resource_id: str | None = None
    resource_name: str = ""

    # 数据快照（可选）
    before_data: dict | None = None
    after_data: dict | None = None

    # 详情信息（可选）
    detail_extra: dict | None = None
