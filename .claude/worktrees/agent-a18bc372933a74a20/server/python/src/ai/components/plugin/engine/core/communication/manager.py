"""
通信管理器
从communication.py中分离出来，避免循环导入
"""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger

from ai.components.plugin.engine.models.plugin import PluginEvent
from ai.components.plugin.engine.utils.helpers import generate_id


class EventBus:
    """事件总线"""

    def __init__(self):
        self.subscribers: dict[str, list] = {}
        self.event_history: list[PluginEvent] = []
        self.max_history = 1000

    def subscribe(self, event_type: str, handler):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler):
        """取消订阅"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                logger.debug(f"取消订阅事件: {event_type}")
            except ValueError:
                pass

    async def publish(self, event: PluginEvent):
        """发布事件"""
        event_type = event.event_type

        # 添加到历史记录
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # 通知订阅者
        if event_type in self.subscribers:
            tasks = []
            for handler in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(handler(event))
                    else:
                        pass
                        # 包装同步函数为异步
                        # tasks.append(
                        #     asyncio.create_task(asyncio.get_event_loop().run_in_executor(None, handler, event))
                        # )
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}")

            # 等待所有处理器完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"事件已发布: {event_type} 来自插件 {event.plugin_name}")

    def get_event_history(
        self,
        event_type: str | None = None,
        plugin_name: str | None = None,
        limit: int = 100,
    ) -> list[PluginEvent]:
        """获取事件历史"""
        events = self.event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if plugin_name:
            events = [e for e in events if e.plugin_name == plugin_name]

        return events[-limit:] if len(events) > limit else events


class MessageQueue:
    """消息队列"""

    def __init__(self):
        self.queues: dict[str, asyncio.Queue] = {}
        self.consumers: dict[str, set[str]] = {}  # queue_name -> consumer_ids

    def create_queue(self, queue_name: str, maxsize: int = 0):
        """创建队列"""
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue(maxsize=maxsize)
            self.consumers[queue_name] = set()
            logger.debug(f"创建消息队列: {queue_name}")

    async def send_message(self, queue_name: str, message: dict[str, Any]):
        """发送消息"""
        if queue_name not in self.queues:
            self.create_queue(queue_name)

        queue = self.queues[queue_name]
        await queue.put(
            {
                "id": generate_id(),
                "timestamp": datetime.now().isoformat(),
                "content": message,
            }
        )

        logger.debug(f"消息已发送到队列 {queue_name}")

    async def receive_message(
        self, queue_name: str, consumer_id: str, timeout: float | None = None
    ):
        """接收消息"""
        if queue_name not in self.queues:
            return None

        self.consumers[queue_name].add(consumer_id)
        queue = self.queues[queue_name]

        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()

            logger.debug(f"消费者 {consumer_id} 从队列 {queue_name} 接收消息")
            return message
        except TimeoutError:
            return None

    def get_queue_info(self, queue_name: str) -> dict[str, Any]:
        """获取队列信息"""
        if queue_name not in self.queues:
            return {}

        queue = self.queues[queue_name]
        return {
            "name": queue_name,
            "size": queue.qsize(),
            "consumers": len(self.consumers[queue_name]),
            "consumer_ids": list(self.consumers[queue_name]),
        }


class CommunicationManager:
    """通信管理器"""

    def __init__(self):
        self.event_bus = EventBus()
        self.message_queue = MessageQueue()
        self.plugin_connections: dict[str, Any] = {}  # plugin_name -> connection_info
        self.message_queues: dict[str, list[dict[str, Any]]] = {}  # 为测试兼容性添加
        self._initialized = False

    async def initialize(self):
        """初始化通信管理器"""
        if self._initialized:
            return

        logger.info("正在初始化通信管理器...")

        # 注册系统事件
        self.event_bus.subscribe("plugin.started", self._on_plugin_started)
        self.event_bus.subscribe("plugin.stopped", self._on_plugin_stopped)
        self.event_bus.subscribe("plugin.error", self._on_plugin_error)

        self._initialized = True
        logger.info("通信管理器初始化完成")

    async def register_plugin(self, plugin_name: str, connection_info: dict[str, Any]):
        """注册插件连接"""
        self.plugin_connections[plugin_name] = connection_info

        # 发布插件注册事件
        event = PluginEvent(
            plugin_name=plugin_name,
            event_type="plugin.registered",
            data=connection_info,
        )
        await self.event_bus.publish(event)

        logger.info(f"插件 {plugin_name} 已注册到通信管理器")

    async def unregister_plugin(self, plugin_name: str):
        """注销插件连接"""
        if plugin_name in self.plugin_connections:
            del self.plugin_connections[plugin_name]

            # 发布插件注销事件
            event = PluginEvent(
                plugin_name=plugin_name, event_type="plugin.unregistered", data={}
            )
            await self.event_bus.publish(event)

            logger.info(f"插件 {plugin_name} 已从通信管理器注销")

    async def send_message(self, target: str, message: dict[str, Any]) -> bool:
        """
        发送消息到指定目标

        Args:
            target: 目标（插件名称或队列名称）
            message: 消息内容

        Returns:
            bool: 发送是否成功
        """
        return await self._deliver_message(target, message)

    async def _deliver_message(self, target: str, message: dict[str, Any]) -> bool:
        """
        内部消息传递方法（为测试兼容性）

        Args:
            target: 目标
            message: 消息内容

        Returns:
            bool: 传递是否成功
        """
        try:
            # 如果目标是插件，发送插件消息
            if target in self.plugin_connections:
                queue_name = f"plugin.{target}"
                await self.message_queue.send_message(queue_name, message)
                logger.debug(f"向插件 {target} 发送消息: {message}")
                return True
            else:
                # 否则当作队列名称处理
                await self.message_queue.send_message(target, message)
                logger.debug(f"向队列 {target} 发送消息: {message}")
                return True
        except Exception as e:
            logger.error(f"消息传递失败: {e}")
            return False

    async def queue_message(self, plugin_name: str, message: dict[str, Any]):
        """
        将消息加入插件队列

        Args:
            plugin_name: 插件名称
            message: 消息内容
        """
        queue_name = f"plugin.{plugin_name}"
        await self.message_queue.send_message(queue_name, message)
        logger.debug(f"消息已加入插件 {plugin_name} 的队列")

        # 同时更新测试兼容性队列
        if plugin_name not in self.message_queues:
            self.message_queues[plugin_name] = []
        self.message_queues[plugin_name].append(message)

    async def broadcast_message(
        self, targets: list[str], message: dict[str, Any]
    ) -> list[bool]:
        """
        广播消息到多个目标

        Args:
            targets: 目标列表
            message: 消息内容

        Returns:
            List[bool]: 每个目标的发送结果
        """
        results = []
        for target in targets:
            result = await self.send_message(target, message)
            results.append(result)
        return results

    async def process_message_queue(self, plugin_name: str) -> int:
        """
        处理插件的消息队列

        Args:
            plugin_name: 插件名称

        Returns:
            int: 处理的消息数量
        """
        if plugin_name not in self.message_queues:
            return 0

        messages = self.message_queues[plugin_name].copy()
        processed_count = 0

        for message in messages:
            try:
                # 发送消息
                await self.send_message(plugin_name, message)
                processed_count += 1
            except Exception as e:
                logger.error(f"处理消息队列失败: {e}")

        # 清空队列
        self.message_queues[plugin_name] = []

        return processed_count

    async def send_plugin_message(
        self, from_plugin: str, to_plugin: str, action: str, data: dict[str, Any]
    ) -> bool:
        """发送插件间消息"""
        if to_plugin not in self.plugin_connections:
            logger.warning(f"目标插件 {to_plugin} 未连接")
            return False

        # 创建消息队列（如果不存在）
        queue_name = f"plugin.{to_plugin}.messages"
        self.message_queue.create_queue(queue_name)

        message = {"from": from_plugin, "to": to_plugin, "action": action, "data": data}

        await self.message_queue.send_message(queue_name, message)

        # 发布消息发送事件
        event = PluginEvent(
            plugin_name=from_plugin,
            event_type="message.sent",
            data={"to": to_plugin, "action": action},
        )
        await self.event_bus.publish(event)

        return True

    async def receive_plugin_message(
        self, plugin_name: str, timeout: float | None = None
    ) -> dict[str, Any] | None:
        """接收插件消息"""
        queue_name = f"plugin.{plugin_name}.messages"
        return await self.message_queue.receive_message(
            queue_name, plugin_name, timeout
        )

    async def broadcast_event(
        self,
        from_plugin: str,
        event_type: str,
        data: dict[str, Any],
        target_plugins: list[str] | None = None,
    ):
        """广播事件"""
        event = PluginEvent(plugin_name=from_plugin, event_type=event_type, data=data)

        # 如果指定了目标插件，只发送给这些插件
        if target_plugins:
            for plugin_name in target_plugins:
                if plugin_name in self.plugin_connections:
                    queue_name = f"plugin.{plugin_name}.events"
                    self.message_queue.create_queue(queue_name)
                    await self.message_queue.send_message(
                        queue_name, {"event": event.dict(), "from": from_plugin}
                    )

        # 发布到事件总线
        await self.event_bus.publish(event)

    def get_plugin_connections(self) -> dict[str, Any]:
        """获取所有插件连接信息"""
        return self.plugin_connections.copy()

    def get_communication_stats(self) -> dict[str, Any]:
        """获取通信统计信息"""
        return {
            "plugin_connections": len(self.plugin_connections),
            "event_subscribers": {
                k: len(v) for k, v in self.event_bus.subscribers.items()
            },
            "message_queues": {
                k: self.message_queue.get_queue_info(k)
                for k in self.message_queue.queues
            },
            "event_history_count": len(self.event_bus.event_history),
        }

    async def _on_plugin_started(self, event: PluginEvent):
        """插件启动事件处理器"""
        logger.debug(f"插件已启动: {event.plugin_name}")

    async def _on_plugin_stopped(self, event: PluginEvent):
        """插件停止事件处理器"""
        logger.debug(f"插件已停止: {event.plugin_name}")

    async def _on_plugin_error(self, event: PluginEvent):
        """插件错误事件处理器"""
        logger.error(f"插件错误: {event.plugin_name} - {event.data}")

    async def publish_event(
        self, event_type: str, data: dict[str, Any], plugin_name: str = "system"
    ):
        """发布事件的便捷方法"""
        event = PluginEvent(
            plugin_name=plugin_name,
            event_type=event_type,
            data=data,
        )
        await self.event_bus.publish(event)
        logger.debug(f"发布事件: {event_type} 来自 {plugin_name}")

    async def start(self):
        """启动通信管理器"""
        await self.initialize()

    async def stop(self):
        """停止通信管理器"""
        logger.info("通信管理器正在停止...")

    async def shutdown(self):
        """关闭通信管理器"""
        await self.stop()
        logger.info("通信管理器已关闭")
