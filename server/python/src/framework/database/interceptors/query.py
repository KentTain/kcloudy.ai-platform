"""
查询拦截器

提供查询级别的拦截功能。
"""

from typing import Any, Type

from sqlalchemy import select, delete, update
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select, Delete, Update

from framework.common.ctx import get_tenant_id


class SoftDeleteInterceptor:
    """软删除拦截器"""

    @staticmethod
    def inject_soft_delete_filter(statement: Any, model_class: Type) -> Any:
        """
        注入软删除过滤条件

        Args:
            statement: SQL 语句
            model_class: 模型类

        Returns:
            添加软删除过滤后的语句
        """
        if hasattr(model_class, "deleted_at"):
            if isinstance(statement, Select):
                statement = statement.where(model_class.deleted_at.is_(None))
            elif isinstance(statement, Delete):
                # 软删除：更新 deleted_at 而不是真正删除
                pass
            elif isinstance(statement, Update):
                statement = statement.where(model_class.deleted_at.is_(None))

        return statement


class TenantQueryInterceptor:
    """租户查询拦截器"""

    @staticmethod
    def inject_tenant_filter(statement: Any, model_class: Type) -> Any:
        """
        注入租户过滤条件

        Args:
            statement: SQL 语句
            model_class: 模型类

        Returns:
            添加租户过滤后的语句
        """
        if hasattr(model_class, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id:
                if isinstance(statement, (Select, Update, Delete)):
                    statement = statement.where(model_class.tenant_id == tenant_id)

        return statement


class QueryInterceptor:
    """查询拦截器管理器"""

    def __init__(self):
        self._interceptors: list = [
            SoftDeleteInterceptor(),
            TenantQueryInterceptor(),
        ]

    def add_interceptor(self, interceptor: Any) -> None:
        """添加拦截器"""
        self._interceptors.append(interceptor)

    def apply_select_interceptors(self, statement: Select, model_class: Type) -> Select:
        """应用 SELECT 拦截器"""
        for interceptor in self._interceptors:
            if hasattr(interceptor, "inject_soft_delete_filter"):
                statement = interceptor.inject_soft_delete_filter(statement, model_class)
            if hasattr(interceptor, "inject_tenant_filter"):
                statement = interceptor.inject_tenant_filter(statement, model_class)
        return statement

    def apply_update_interceptors(self, statement: Update, model_class: Type) -> Update:
        """应用 UPDATE 拦截器"""
        for interceptor in self._interceptors:
            if hasattr(interceptor, "inject_tenant_filter"):
                statement = interceptor.inject_tenant_filter(statement, model_class)
        return statement

    def apply_delete_interceptors(self, statement: Delete, model_class: Type) -> Delete:
        """应用 DELETE 拦截器"""
        for interceptor in self._interceptors:
            if hasattr(interceptor, "inject_tenant_filter"):
                statement = interceptor.inject_tenant_filter(statement, model_class)
        return statement


# 全局查询拦截器
query_interceptor = QueryInterceptor()
