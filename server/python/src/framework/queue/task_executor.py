"""
租户感知的任务执行器

自动恢复和清理租户上下文。
"""

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger

from framework.queue.task_message import TaskMessage
from framework.tenant.context import TenantContext
from framework.tenant.protocols import get_tenant_provider

_logger = logger.bind(name=__name__)

# 任务处理器注册表
_task_handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}


def register_task_handler(task_type: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    """注册任务处理器"""
    _task_handlers[task_type] = handler


def get_task_handler(task_type: str) -> Callable[[dict[str, Any]], Awaitable[None]] | None:
    """获取任务处理器"""
    return _task_handlers.get(task_type)


class TenantTaskExecutor:
    """
    租户感知的任务执行器

    场景：任务执行恢复租户上下文
    WHEN 任务消息包含 `tenant_id: "tenant_001"`
    THEN 执行前加载租户信息并设置租户上下文
    AND 执行完成后清理租户上下文

    场景：任务执行时租户不存在
    WHEN 任务消息包含 `tenant_id` 但租户不存在
    THEN 记录警告日志，任务继续执行（无租户上下文）

    场景：任务执行无租户信息
    WHEN 任务消息不包含 `tenant_id`
    THEN 任务正常执行（无租户上下文）

    场景：任务异常后上下文清理
    WHEN 任务执行过程中发生异常
    THEN 租户上下文仍被清理
    """

    @staticmethod
    async def execute(message: TaskMessage) -> bool:
        """
        执行任务

        Args:
            message: 任务消息

        Returns:
            bool: 是否执行成功
        """
        try:
            # 恢复租户上下文
            if message.tenant_id:
                await TenantTaskExecutor._restore_tenant_context(message.tenant_id)

            # 获取处理器
            handler = get_task_handler(message.task_type)
            if not handler:
                _logger.warning(f"未找到任务处理器: {message.task_type}")
                return False

            # 执行任务
            await handler(message.payload)
            return True

        except Exception as e:
            _logger.exception(f"任务执行失败: {message.task_id}, error={e}")
            return False

        finally:
            # 清理租户上下文
            TenantContext.clear()

    @staticmethod
    async def _restore_tenant_context(tenant_id: str) -> None:
        """
        恢复租户上下文

        Args:
            tenant_id: 租户 ID
        """
        try:
            provider = get_tenant_provider()
            tenant = await provider.get_tenant(tenant_id)
            if tenant:
                TenantContext.set_current_tenant(tenant)
            else:
                _logger.warning(f"租户不存在，无法恢复上下文: {tenant_id}")
        except Exception as e:
            _logger.warning(f"恢复租户上下文失败: {tenant_id}, error={e}")


async def execute_task(message: TaskMessage) -> bool:
    """执行任务"""
    return await TenantTaskExecutor.execute(message)
