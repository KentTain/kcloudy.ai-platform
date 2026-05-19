"""
租户事件

提供多租户隔离的事件监听。
"""

from typing import Any

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from framework.common.ctx import get_tenant_id


class TenantEventListener:
    """租户事件监听器"""

    @staticmethod
    def before_insert(mapper: Any, connection: Any, target: Any) -> None:
        """插入前事件 - 自动设置租户 ID"""
        if hasattr(target, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id and target.tenant_id is None:
                target.tenant_id = tenant_id


def register_tenant_events(base_class: type) -> None:
    """
    注册租户事件监听器

    Args:
        base_class: 基础模型类
    """
    event.listen(base_class, "before_insert", TenantEventListener.before_insert)


class TenantQueryInterceptor:
    """租户查询拦截器"""

    @staticmethod
    def inject_tenant_filter(query: Any, model_class: type) -> Any:
        """
        注入租户过滤条件

        Args:
            query: 查询对象
            model_class: 模型类

        Returns:
            添加租户过滤后的查询
        """
        if hasattr(model_class, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id:
                query = query.where(model_class.tenant_id == tenant_id)

        return query
