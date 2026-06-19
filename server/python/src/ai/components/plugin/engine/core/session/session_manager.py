"""
会话管理模块
管理插件会话、状态、生命周期等
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, ConfigDict


class SessionStatus:
    """会话状态常量"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PluginSession(BaseModel):
    """插件会话"""

    session_id: str
    plugin_name: str  # 对应Go中的plugin_id
    user_id: str | None = None
    created_at: datetime
    last_activity: datetime
    status: str = SessionStatus.PENDING  # 使用SessionStatus常量
    context: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    request_count: int = 0
    error_count: int = 0

    # 为测试兼容性添加的属性
    plugin_id: str | None = None  # 别名，指向plugin_name
    action: str | None = None
    parameters: dict[str, Any] = {}
    result: Any | None = None
    error: str | None = None
    progress: Any | None = None
    data: dict[str, Any] = {}  # 通用数据存储

    def __init__(self, **data):
        super().__init__(**data)
        # 设置plugin_id别名
        if self.plugin_id is None:
            self.plugin_id = self.plugin_name

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否过期"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()

    def increment_request(self):
        """增加请求计数"""
        self.request_count += 1
        self.update_activity()

    def increment_error(self):
        """增加错误计数"""
        self.error_count += 1
        self.update_activity()


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions: dict[str, PluginSession] = {}
        self.plugin_sessions: dict[str, set[str]] = {}  # plugin_name -> session_ids
        self.user_sessions: dict[str, set[str]] = {}  # user_id -> session_ids
        self.session_timeout = 30  # 会话超时时间（分钟）
        self._cleanup_task: asyncio.Task | None = None
        self._initialized = False

    async def initialize(self):
        """初始化会话管理器"""
        if self._initialized:
            return

        logger.info("正在初始化会话管理器...")

        # 启动定期清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

        self._initialized = True
        logger.info("会话管理器初始化完成")

    async def create_session(
        self,
        user_id: str,
        metadata: dict[str, Any] | None = None,
        plugin_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> PluginSession:
        """创建新会话"""
        session_id = str(uuid4())

        session = PluginSession(
            session_id=session_id,
            plugin_name=plugin_name or "default",
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            context=context or {},
            metadata=metadata or {},
        )

        # 存储会话
        self.sessions[session_id] = session

        # 添加到插件会话集合
        plugin_name = plugin_name or "default"
        if plugin_name not in self.plugin_sessions:
            self.plugin_sessions[plugin_name] = set()
        self.plugin_sessions[plugin_name].add(session_id)

        # 添加到用户会话集合
        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)

        logger.debug(f"创建会话: {session_id} 插件: {plugin_name} 用户: {user_id}")
        return session

    async def get_session(self, session_id: str) -> PluginSession | None:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session and not session.is_expired(self.session_timeout):
            return session
        elif session and session.is_expired(self.session_timeout):
            # 会话已过期，删除它
            await self.delete_session(session_id)
        return None

    def get_session_sync(self, session_id: str) -> PluginSession | None:
        """获取会话（同步版本）"""
        session = self.sessions.get(session_id)
        if session and not session.is_expired(self.session_timeout):
            return session
        elif session and session.is_expired(self.session_timeout):
            # 会话已过期，直接删除（同步版本）
            self.sessions.pop(session_id, None)
        return None

    def get_plugin_sessions(self, plugin_name: str) -> list[PluginSession]:
        """获取插件的所有活跃会话"""
        if plugin_name not in self.plugin_sessions:
            return []

        sessions = []
        for session_id in self.plugin_sessions[plugin_name]:
            session = self.get_session_sync(session_id)
            if session:
                sessions.append(session)

        return sessions

    def get_user_sessions(self, user_id: str) -> list[PluginSession]:
        """获取用户的所有活跃会话"""
        if user_id not in self.user_sessions:
            return []

        sessions = []
        for session_id in self.user_sessions[user_id]:
            session = self.get_session_sync(session_id)
            if session:
                sessions.append(session)

        return sessions

    async def update_session_context(
        self, session_id: str, context_update: dict[str, Any]
    ) -> bool:
        """更新会话上下文"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        session.context.update(context_update)
        session.update_activity()

        logger.debug(f"更新会话上下文: {session_id}")
        return True

    async def update_session(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        session.status = status
        session.update_activity()

        logger.debug(f"更新会话状态: {session_id} -> {status}")
        return True

    async def close_session(self, session_id: str) -> bool:
        """关闭会话（为测试兼容性）"""
        return await self.delete_session(session_id)

    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话（为测试兼容性）"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.delete_session(session_id)

        return len(expired_sessions)

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # 从插件会话集合中移除
        if session.plugin_name in self.plugin_sessions:
            self.plugin_sessions[session.plugin_name].discard(session_id)
            if not self.plugin_sessions[session.plugin_name]:
                del self.plugin_sessions[session.plugin_name]

        # 从用户会话集合中移除
        if session.user_id and session.user_id in self.user_sessions:
            self.user_sessions[session.user_id].discard(session_id)
            if not self.user_sessions[session.user_id]:
                del self.user_sessions[session.user_id]

        # 删除会话
        del self.sessions[session_id]

        logger.debug(f"删除会话: {session_id}")
        return True

    async def delete_plugin_sessions(self, plugin_name: str) -> int:
        """删除插件的所有会话"""
        if plugin_name not in self.plugin_sessions:
            return 0

        session_ids = list(self.plugin_sessions[plugin_name])
        deleted_count = 0

        for session_id in session_ids:
            if await self.delete_session(session_id):
                deleted_count += 1

        logger.info(f"删除插件 {plugin_name} 的 {deleted_count} 个会话")
        return deleted_count

    def get_session_stats(self) -> dict[str, Any]:
        """获取会话统计信息"""
        total_sessions = len(self.sessions)
        active_sessions = len(
            [
                s
                for s in self.sessions.values()
                if not s.is_expired(self.session_timeout)
            ]
        )

        plugin_stats = {}
        for plugin_name, session_ids in self.plugin_sessions.items():
            plugin_stats[plugin_name] = len(session_ids)

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions,
            "plugin_sessions": plugin_stats,
            "session_timeout_minutes": self.session_timeout,
        }

    async def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                expired_sessions = []
                for session_id, session in self.sessions.items():
                    if session.is_expired(self.session_timeout):
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    await self.delete_session(session_id)

                if expired_sessions:
                    logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

            except Exception as e:
                logger.error(f"清理过期会话时出错: {e}")

    async def start(self):
        """启动会话管理器"""
        await self.initialize()
        logger.info("会话管理器已启动")

    async def stop(self):
        """停止会话管理器"""
        await self.shutdown()

    async def shutdown(self):
        """关闭会话管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 清理所有会话
        session_count = len(self.sessions)
        self.sessions.clear()
        self.plugin_sessions.clear()
        self.user_sessions.clear()

        logger.info(f"会话管理器已关闭，清理了 {session_count} 个会话")

    # 为测试兼容性添加的方法
    def create_session_sync(
        self, plugin_id: str, action: str, parameters: dict[str, Any]
    ) -> PluginSession:
        """同步创建会话（为测试兼容性）"""
        session_id = str(uuid4())

        session = PluginSession(
            session_id=session_id,
            plugin_name=plugin_id,
            plugin_id=plugin_id,
            action=action,
            parameters=parameters,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            status=SessionStatus.PENDING,
        )

        # 存储会话
        self.sessions[session_id] = session

        # 添加到插件会话集合
        if plugin_id not in self.plugin_sessions:
            self.plugin_sessions[plugin_id] = set()
        self.plugin_sessions[plugin_id].add(session_id)

        logger.debug(f"创建会话: {session_id} 插件: {plugin_id} 动作: {action}")
        return session

    def update_session_sync(self, session_id: str, status: str) -> bool:
        """更新会话状态（同步版本）"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        session.status = status
        session.update_activity()

        logger.debug(f"更新会话 {session_id} 状态: {status}")
        return True

    def close_session_sync(self, session_id: str) -> bool:
        """关闭会话（同步版本的delete_session）"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # 从插件会话集合中移除
        plugin_name = session.plugin_name
        if plugin_name in self.plugin_sessions:
            self.plugin_sessions[plugin_name].discard(session_id)
            if not self.plugin_sessions[plugin_name]:
                del self.plugin_sessions[plugin_name]

        # 从用户会话集合中移除
        if session.user_id and session.user_id in self.user_sessions:
            self.user_sessions[session.user_id].discard(session_id)
            if not self.user_sessions[session.user_id]:
                del self.user_sessions[session.user_id]

        # 删除会话
        del self.sessions[session_id]

        logger.debug(f"关闭会话: {session_id}")
        return True

    def list_sessions(self, status: str | None = None) -> list[PluginSession]:
        """列出会话"""
        sessions = []
        for session in self.sessions.values():
            # 过滤已过期的会话
            if session.is_expired(self.session_timeout):
                continue

            # 按状态过滤
            if status is None or session.status == status:
                sessions.append(session)

        return sessions

    def get_session_statistics(self) -> dict[str, Any]:
        """获取会话统计信息"""
        all_sessions = list(self.sessions.values())
        active_sessions = [
            s for s in all_sessions if not s.is_expired(self.session_timeout)
        ]

        stats = {
            "total": len(active_sessions),
            "pending": len(
                [s for s in active_sessions if s.status == SessionStatus.PENDING]
            ),
            "running": len(
                [s for s in active_sessions if s.status == SessionStatus.RUNNING]
            ),
            "completed": len(
                [s for s in active_sessions if s.status == SessionStatus.COMPLETED]
            ),
            "failed": len(
                [s for s in active_sessions if s.status == SessionStatus.FAILED]
            ),
        }

        return stats

    def cleanup_expired_sessions_sync(self) -> int:
        """清理过期会话（同步版本）"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_sessions.append(session_id)

        cleaned_count = 0
        for session_id in expired_sessions:
            if self.close_session_sync(session_id):
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个过期会话")

        return cleaned_count

    def set_session_timeout(self, timeout_minutes: int):
        """设置会话超时时间"""
        self.session_timeout = timeout_minutes
        logger.debug(f"设置会话超时时间: {timeout_minutes} 分钟")

    def set_session_result(self, session_id: str, result: Any) -> bool:
        """设置会话结果"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        session.result = result
        session.update_activity()

        logger.debug(f"设置会话 {session_id} 结果")
        return True

    def set_session_error(self, session_id: str, error: Any) -> bool:
        """设置会话错误"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        session.error = error
        session.status = SessionStatus.FAILED
        session.update_activity()

        logger.debug(f"设置会话 {session_id} 错误")
        return True

    def update_session_progress(self, session_id: str, progress: Any) -> bool:
        """更新会话进度"""
        session = self.get_session_sync(session_id)
        if not session:
            return False

        # 添加progress字段到会话中
        if not hasattr(session, "progress"):
            session.progress = None
        session.progress = progress
        session.update_activity()

        logger.debug(f"更新会话 {session_id} 进度")
        return True
