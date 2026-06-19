"""
租户混入

提供租户隔离字段混入类。
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    """
    租户混入类

    提供租户 ID 字段，支持多租户隔离。
    """

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="租户ID"
    )


# 上下文标志，用于跳过租户过滤
_skip_tenant_context: dict[int, bool] = {}


def set_skip_tenant(skip: bool = True) -> None:
    """
    设置跳过租户过滤标志

    用于管理员场景，需要跨租户查询时使用。
    """
    import threading
    _skip_tenant_context[threading.get_ident()] = skip


def should_skip_tenant() -> bool:
    """检查是否应该跳过租户过滤"""
    import threading
    return _skip_tenant_context.get(threading.get_ident(), False)


def clear_skip_tenant() -> None:
    """清除跳过租户过滤标志"""
    import threading
    _skip_tenant_context.pop(threading.get_ident(), None)
