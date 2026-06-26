"""
安装任务服务

提供插件安装任务的管理功能：创建、状态更新、进度追踪、查询。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginInstallTask
from ai.schemas.plugin import (
    InstallTaskDetailVo,
    InstallTaskListResponse,
    InstallTaskVo,
    InstallPluginRequest,
    InstallPluginResponse,
)
from framework.common.ctx import get_tenant_id, get_user_id
from framework.common.exceptions import BadRequestError, NotFoundError
from framework.configs import get_settings
from framework.queue.task_queue import enqueue_task
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)

# 安装步骤定义
INSTALL_STEPS = [
    {"step": "download", "name": "下载插件包", "status": "pending"},
    {"step": "validate", "name": "校验插件包", "status": "pending"},
    {"step": "install", "name": "安装插件", "status": "pending"},
    {"step": "configure", "name": "初始化配置", "status": "pending"},
    {"step": "finalize", "name": "完成安装", "status": "pending"},
]


class InstallTaskService:
    """安装任务服务"""

    @staticmethod
    async def create_install_task(
        session: AsyncSession,
        request: InstallPluginRequest,
    ) -> InstallPluginResponse:
        """
        创建安装任务

        Args:
            session: 数据库会话
            request: 安装请求

        Returns:
            InstallPluginResponse: 安装任务响应

        Raises:
            NotFoundError: 插件定义不存在
            BadRequestError: 插件已禁用或已安装
        """
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        plugin_id = request.plugin_id

        # 1. 检查插件定义是否存在
        definition_stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id,
        )
        result = await session.execute(definition_stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        # 2. 检查插件是否已禁用
        if not definition.is_enabled:
            raise BadRequestError(message="插件已禁用，无法安装")

        # 3. 检查是否已安装
        existing_installation_stmt = select(TenantPluginInstallation).where(
            TenantPluginInstallation.tenant_id == tenant_id,
            TenantPluginInstallation.plugin_id == plugin_id,
        )
        existing_result = await session.execute(existing_installation_stmt)
        existing_installation = existing_result.scalar_one_or_none()

        if existing_installation:
            raise BadRequestError(message="插件已安装")

        # 4. 创建安装任务记录
        task_id = str(uuid.uuid4())
        task = PluginInstallTask(
            id=task_id,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            status="pending",
            progress=0,
            current_step=None,
            steps=[s.copy() for s in INSTALL_STEPS],
            created_by=get_user_id(),
        )
        session.add(task)

        # 5. 创建 Tenant 侧安装记录（PENDING 状态）
        installation = TenantPluginInstallation(
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            status="PENDING",
            auto_start=request.auto_start,
            plugin_type="local",
            runtime_type="local",
        )
        session.add(installation)

        await session.flush()

        # 6. 发送任务到 Redis Stream 队列
        try:
            await enqueue_task(
                task_type="plugin_install",
                payload={
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "plugin_id": plugin_id,
                    "plugin_unique_identifier": definition.plugin_unique_identifier,
                    "auto_start": request.auto_start,
                },
                queue_name="plugin_install_tasks",
            )
            _logger.info(f"安装任务已入队: task_id={task_id}, plugin_id={plugin_id}")
        except Exception as e:
            _logger.error(f"安装任务入队失败: {e}")
            # 回滚任务状态
            task.status = "failed"
            task.error_message = f"任务入队失败: {str(e)}"
            await session.flush()

        return InstallPluginResponse(
            task_id=task_id,
            plugin_id=plugin_id,
            message="安装任务已创建",
            status="pending",
        )

    @staticmethod
    async def update_task_status(
        session: AsyncSession,
        task_id: str,
        status: str,
        progress: int | None = None,
        current_step: str | None = None,
        error_message: str | None = None,
    ) -> PluginInstallTask | None:
        """
        更新任务状态

        Args:
            session: 数据库会话
            task_id: 任务ID
            status: 新状态
            progress: 进度百分比
            current_step: 当前步骤
            error_message: 错误信息

        Returns:
            PluginInstallTask | None: 更新后的任务
        """
        task = await PluginInstallTask.one_by_id(session, task_id)
        if not task:
            return None

        update_data: dict[str, Any] = {"status": status}

        if progress is not None:
            update_data["progress"] = progress

        if current_step is not None:
            update_data["current_step"] = current_step

        if status == "running" and not task.started_at:
            update_data["started_at"] = datetime.now()

        if status in ("completed", "failed", "timeout"):
            update_data["completed_at"] = datetime.now()

        if error_message is not None:
            update_data["error_message"] = error_message

        await task.update(session, update_data)
        await session.flush()

        _logger.info(
            f"任务状态更新: task_id={task_id}, status={status}, progress={progress}"
        )

        return task

    @staticmethod
    async def update_task_step(
        session: AsyncSession,
        task_id: str,
        step_name: str,
        step_status: str,
        progress: int | None = None,
    ) -> PluginInstallTask | None:
        """
        更新任务步骤状态

        Args:
            session: 数据库会话
            task_id: 任务ID
            step_name: 步骤名称
            step_status: 步骤状态
            progress: 进度百分比

        Returns:
            PluginInstallTask | None: 更新后的任务
        """
        task = await PluginInstallTask.one_by_id(session, task_id)
        if not task:
            return None

        steps = task.steps or []
        updated_steps = []
        for step in steps:
            if step.get("step") == step_name:
                updated_steps.append({**step, "status": step_status})
            else:
                updated_steps.append(step)

        update_data: dict[str, Any] = {
            "steps": updated_steps,
            "current_step": step_name,
        }

        if progress is not None:
            update_data["progress"] = progress

        await task.update(session, update_data)
        await session.flush()

        return task

    @staticmethod
    async def get_task_list(
        session: AsyncSession,
        status: str | None = None,
        plugin_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InstallTaskListResponse:
        """
        获取安装任务列表

        Args:
            session: 数据库会话
            status: 状态筛选
            plugin_id: 插件ID筛选
            page: 页码
            page_size: 每页条数

        Returns:
            InstallTaskListResponse: 任务列表响应
        """
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        conditions = [PluginInstallTask.tenant_id == tenant_id]

        if status:
            conditions.append(PluginInstallTask.status == status)

        if plugin_id:
            conditions.append(PluginInstallTask.plugin_id.ilike(f"%{plugin_id}%"))

        # 查询总数
        count_stmt = select(func.count(PluginInstallTask.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(PluginInstallTask)
            .where(*conditions)
            .order_by(PluginInstallTask.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        tasks = list(result.scalars().all())

        # 转换为 VO
        items = [InstallTaskService._to_task_vo(task) for task in tasks]

        return InstallTaskListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    async def get_task_detail(
        session: AsyncSession,
        task_id: str,
    ) -> InstallTaskDetailVo:
        """
        获取安装任务详情

        Args:
            session: 数据库会话
            task_id: 任务ID

        Returns:
            InstallTaskDetailVo: 任务详情

        Raises:
            NotFoundError: 任务不存在
        """
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        task = await PluginInstallTask.one_by_id(session, task_id)
        if not task:
            raise NotFoundError(message=f"任务不存在: {task_id}")

        # 检查租户权限
        if task.tenant_id != tenant_id:
            raise NotFoundError(message=f"任务不存在: {task_id}")

        return InstallTaskService._to_task_detail_vo(task)

    @staticmethod
    async def check_timeout_tasks(session: AsyncSession) -> int:
        """
        检查超时任务

        将超过 30 分钟的 running 状态任务标记为 timeout。

        Args:
            session: 数据库会话

        Returns:
            int: 超时任务数量
        """
        now = datetime.now()
        settings = get_settings()
        timeout_threshold = settings.plugin.install_task_timeout_seconds

        # 查询超时的 running 任务
        stmt = select(PluginInstallTask).where(
            PluginInstallTask.status == "running",
            PluginInstallTask.started_at.isnot(None),
        )
        result = await session.execute(stmt)
        tasks = list(result.scalars().all())

        timeout_count = 0
        for task in tasks:
            if task.started_at:
                elapsed = (now - task.started_at).total_seconds()
                if elapsed > timeout_threshold:
                    task.status = "timeout"
                    task.error_message = "安装任务超时"
                    task.completed_at = now
                    timeout_count += 1
                    _logger.warning(
                        f"任务超时: task_id={task.id}, "
                        f"elapsed={elapsed:.0f}s"
                    )

        if timeout_count > 0:
            await session.flush()

        return timeout_count

    @staticmethod
    def _to_task_vo(task: PluginInstallTask) -> InstallTaskVo:
        """转换任务为 VO"""
        return InstallTaskVo(
            id=str(task.id),
            plugin_id=task.plugin_id,
            status=task.status,
            progress=task.progress,
            current_step=task.current_step,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
        )

    @staticmethod
    def _to_task_detail_vo(task: PluginInstallTask) -> InstallTaskDetailVo:
        """转换任务为详情 VO"""
        return InstallTaskDetailVo(
            id=str(task.id),
            plugin_id=task.plugin_id,
            status=task.status,
            progress=task.progress,
            current_step=task.current_step,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            plugin_unique_identifier=task.plugin_unique_identifier,
            steps=task.steps,
            error_message=task.error_message,
            logs=None,  # 日志功能后续实现
        )


# 全局服务实例
install_task_service = InstallTaskService()
