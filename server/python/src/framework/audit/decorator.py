"""
审计日志装饰器

提供声明式的审计日志记录功能。
"""

from functools import wraps
from typing import Callable

from framework.audit.context import AuditContext
from framework.audit.service import audit_service
from framework.audit.utils import extract_session


def audit_log(
    module: str,
    resource: str,
    action: str,
    resource_id_getter: Callable | None = None,
    resource_name_getter: Callable | None = None,
    before_data_getter: Callable | None = None,
    detail_extra: dict | None = None,
):
    """
    审计日志装饰器

    Args:
        module: 模块名称
        resource: 资源类型
        action: 操作类型
        resource_id_getter: 从参数/返回值获取资源 ID
        resource_name_getter: 从参数/返回值获取资源名称
        before_data_getter: 获取操作前数据（更新/删除场景）
        detail_extra: 额外的 detail 信息

    Example:
        @audit_log(
            module="iam",
            resource="user",
            action="create",
            resource_id_getter=lambda result: result.id,
            resource_name_getter=lambda result: result.username,
        )
        async def create_user(self, session, user_create) -> User:
            pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 执行前：获取 before_data（如果有）
            before_data = None
            if before_data_getter:
                import asyncio

                result = before_data_getter(args, kwargs)
                if asyncio.iscoroutine(result):
                    before_data = await result
                else:
                    before_data = result

            # 2. 执行业务逻辑
            result = await func(*args, **kwargs)

            # 3. 执行后：构建审计上下文
            context = AuditContext(
                module=module,
                resource=resource,
                action=action,
                detail_extra=detail_extra,
            )

            # 4. 获取资源 ID 和名称
            if resource_id_getter:
                context.resource_id = resource_id_getter(result)

            if resource_name_getter:
                context.resource_name = resource_name_getter(result)

            # 5. 设置 before_data
            context.before_data = before_data

            # 6. 获取 after_data（从返回值）
            if result and hasattr(result, "to_dict"):
                context.after_data = result.to_dict()
            elif isinstance(result, dict):
                context.after_data = result

            # 7. 记录审计日志
            session = extract_session(args, kwargs)
            if session:
                await audit_service.record(session, context)

            return result

        return wrapper

    return decorator
