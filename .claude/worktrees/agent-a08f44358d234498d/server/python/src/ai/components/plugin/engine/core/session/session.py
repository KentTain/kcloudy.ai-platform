"""
会话管理模块
管理插件调用会话和上下文
"""

import asyncio
import time
import uuid
from typing import Any

from loguru import logger


class Session:
    """会话对象"""

    def __init__(self, plugin_name: str, action: str, parameters: dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.plugin_name = plugin_name
        self.action = action
        self.parameters = parameters
        self.created_at = time.time()
        self.status = "created"
        self.result: Any | None = None
        self.error: str | None = None


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self._cleanup_task: asyncio.Task | None = None

    async def initialize(self):
        """初始化会话管理器"""
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        logger.info("会话管理器已初始化")

    def create_session(
        self, plugin_name: str, action: str, parameters: dict[str, Any]
    ) -> Session:
        """创建新会话"""
        session = Session(plugin_name, action, parameters)
        self.sessions[session.id] = session
        logger.debug(f"创建会话: {session.id}")
        return session

    def get_session(self, session_id: str) -> Session | None:
        """获取会话"""
        return self.sessions.get(session_id)

    def update_session(
        self, session_id: str, status: str, result: Any = None, error: str | None = None
    ):
        """更新会话状态"""
        session = self.sessions.get(session_id)
        if session:
            session.status = status
            session.result = result
            session.error = error
            logger.debug(f"更新会话 {session_id} 状态: {status}")

    def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug(f"关闭会话: {session_id}")

    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    # 删除超过1小时的会话
                    if current_time - session.created_at > 3600:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    self.close_session(session_id)

                if expired_sessions:
                    logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

                # 每5分钟清理一次
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"清理会话时出错: {e}")
                await asyncio.sleep(60)

    async def shutdown(self):
        """关闭会话管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.sessions.clear()
        logger.info("会话管理器已关闭")
