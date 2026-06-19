# """
# WebSocket路由模块
# 提供实时通信功能，支持插件事件推送、双向通信等
# """

# import json
# from typing import Dict, List

# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from loguru import logger

# from ai.components.plugin.engine.core.communication import CommunicationManager
# from ai.components.plugin.engine.models.plugin import PluginEvent
# from ai.components.plugin.engine.utils.helpers import generate_id

# router = APIRouter()


# # 全局连接管理器
# class ConnectionManager:
#     """WebSocket连接管理器"""

#     def __init__(self):
#         self.connections: Dict[str, WebSocket] = {}
#         self.plugin_connections: Dict[str, List[str]] = {}
#         self.communication_manager: CommunicationManager = None

#     async def connect(self, websocket: WebSocket, client_id: str):
#         """连接WebSocket"""
#         await websocket.accept()
#         self.connections[client_id] = websocket
#         logger.info(f"WebSocket客户端连接: {client_id}")

#     def disconnect(self, client_id: str):
#         """断开WebSocket连接"""
#         if client_id in self.connections:
#             del self.connections[client_id]

#         # 清理插件连接
#         for plugin_name, client_ids in self.plugin_connections.items():
#             if client_id in client_ids:
#                 client_ids.remove(client_id)

#         logger.info(f"WebSocket客户端断开: {client_id}")

#     async def send_message(self, client_id: str, message: dict):
#         """发送消息给指定客户端"""
#         if client_id in self.connections:
#             try:
#                 await self.connections[client_id].send_text(json.dumps(message))
#             except Exception as e:
#                 logger.error(f"发送WebSocket消息失败: {e}")
#                 self.disconnect(client_id)

#     async def broadcast(self, message: dict, plugin_name: str = None):
#         """广播消息"""
#         if plugin_name and plugin_name in self.plugin_connections:
#             # 只发送给订阅特定插件的客户端
#             client_ids = self.plugin_connections[plugin_name]
#             for client_id in client_ids.copy():
#                 await self.send_message(client_id, message)
#         else:
#             # 广播给所有连接的客户端
#             for client_id in list(self.connections.keys()):
#                 await self.send_message(client_id, message)

#     def subscribe_plugin(self, client_id: str, plugin_name: str):
#         """订阅插件事件"""
#         if plugin_name not in self.plugin_connections:
#             self.plugin_connections[plugin_name] = []

#         if client_id not in self.plugin_connections[plugin_name]:
#             self.plugin_connections[plugin_name].append(client_id)

#         logger.debug(f"客户端 {client_id} 订阅插件 {plugin_name}")

#     def unsubscribe_plugin(self, client_id: str, plugin_name: str):
#         """取消订阅插件事件"""
#         if plugin_name in self.plugin_connections:
#             if client_id in self.plugin_connections[plugin_name]:
#                 self.plugin_connections[plugin_name].remove(client_id)

#         logger.debug(f"客户端 {client_id} 取消订阅插件 {plugin_name}")


# # 全局连接管理器实例
# connection_manager = ConnectionManager()


# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     """通用WebSocket端点"""
#     client_id = generate_id()

#     try:
#         await connection_manager.connect(websocket, client_id)

#         # 发送欢迎消息
#         await connection_manager.send_message(
#             client_id, {"type": "connected", "client_id": client_id, "message": "WebSocket连接已建立"}
#         )

#         while True:
#             try:
#                 # 接收客户端消息
#                 data = await websocket.receive_text()
#                 message = json.loads(data)

#                 # 处理消息
#                 await handle_websocket_message(client_id, message)

#             except WebSocketDisconnect:
#                 break
#             except json.JSONDecodeError:
#                 await connection_manager.send_message(
#                     client_id, {"type": "error", "message": "消息格式错误，请发送有效的JSON"}
#                 )
#             except Exception as e:
#                 logger.error(f"WebSocket消息处理错误: {e}")
#                 await connection_manager.send_message(client_id, {"type": "error", "message": "消息处理失败"})

#     except Exception as e:
#         logger.error(f"WebSocket连接错误: {e}")
#     finally:
#         connection_manager.disconnect(client_id)


# @router.websocket("/ws/plugins/{plugin_name}")
# async def plugin_websocket_endpoint(websocket: WebSocket, plugin_name: str):
#     """插件专用WebSocket端点"""
#     client_id = generate_id()

#     try:
#         await connection_manager.connect(websocket, client_id)

#         # 自动订阅指定插件
#         connection_manager.subscribe_plugin(client_id, plugin_name)

#         # 发送连接确认
#         await connection_manager.send_message(
#             client_id,
#             {
#                 "type": "plugin_connected",
#                 "plugin_name": plugin_name,
#                 "client_id": client_id,
#                 "message": f"已连接到插件 {plugin_name}",
#             },
#         )

#         while True:
#             try:
#                 # 接收客户端消息
#                 data = await websocket.receive_text()
#                 message = json.loads(data)

#                 # 添加插件上下文
#                 message["plugin_name"] = plugin_name

#                 # 处理消息
#                 await handle_plugin_websocket_message(client_id, plugin_name, message)

#             except WebSocketDisconnect:
#                 break
#             except json.JSONDecodeError:
#                 await connection_manager.send_message(
#                     client_id, {"type": "error", "message": "消息格式错误，请发送有效的JSON"}
#                 )
#             except Exception as e:
#                 logger.error(f"插件WebSocket消息处理错误: {e}")
#                 await connection_manager.send_message(client_id, {"type": "error", "message": "消息处理失败"})

#     except Exception as e:
#         logger.error(f"插件WebSocket连接错误: {e}")
#     finally:
#         connection_manager.disconnect(client_id)


# async def handle_websocket_message(client_id: str, message: dict):
#     """处理WebSocket消息"""
#     message_type = message.get("type")

#     if message_type == "subscribe":
#         # 订阅插件事件
#         plugin_name = message.get("plugin_name")
#         if plugin_name:
#             connection_manager.subscribe_plugin(client_id, plugin_name)
#             await connection_manager.send_message(
#                 client_id,
#                 {"type": "subscribed", "plugin_name": plugin_name, "message": f"已订阅插件 {plugin_name} 的事件"},
#             )

#     elif message_type == "unsubscribe":
#         # 取消订阅插件事件
#         plugin_name = message.get("plugin_name")
#         if plugin_name:
#             connection_manager.unsubscribe_plugin(client_id, plugin_name)
#             await connection_manager.send_message(
#                 client_id,
#                 {"type": "unsubscribed", "plugin_name": plugin_name, "message": f"已取消订阅插件 {plugin_name} 的事件"},
#             )

#     elif message_type == "ping":
#         # 心跳检测
#         await connection_manager.send_message(client_id, {"type": "pong", "timestamp": message.get("timestamp")})

#     elif message_type == "get_status":
#         # 获取连接状态
#         await connection_manager.send_message(
#             client_id,
#             {
#                 "type": "status",
#                 "client_id": client_id,
#                 "subscribed_plugins": [
#                     plugin for plugin, clients in connection_manager.plugin_connections.items() if client_id in clients
#                 ],
#             },
#         )

#     else:
#         await connection_manager.send_message(
#             client_id, {"type": "error", "message": f"未知的消息类型: {message_type}"}
#         )


# async def handle_plugin_websocket_message(client_id: str, plugin_name: str, message: dict):
#     """处理插件WebSocket消息"""
#     message_type = message.get("type")

#     if message_type == "invoke":
#         # 调用插件方法
#         action = message.get("action")
#         parameters = message.get("parameters", {})

#         try:
#             # 这里需要从插件管理器获取实例
#             from core.plugin_manager import PluginManager

#             manager = PluginManager()

#             result = await manager.invoke_plugin(plugin_name, action, parameters)

#             await connection_manager.send_message(
#                 client_id, {"type": "invoke_result", "action": action, "result": result}
#             )

#         except Exception as e:
#             await connection_manager.send_message(
#                 client_id, {"type": "invoke_error", "action": action, "error": str(e)}
#             )

#     elif message_type == "get_logs":
#         # 获取插件日志
#         limit = message.get("limit", 100)
#         level = message.get("level")

#         try:
#             from core.plugin_manager import PluginManager

#             manager = PluginManager()

#             logs = await manager.get_plugin_logs(plugin_name, limit, level)

#             await connection_manager.send_message(client_id, {"type": "logs", "logs": logs})

#         except Exception as e:
#             await connection_manager.send_message(client_id, {"type": "logs_error", "error": str(e)})

#     elif message_type == "get_metrics":
#         # 获取插件指标
#         try:
#             from core.plugin_manager import PluginManager

#             manager = PluginManager()

#             metrics = await manager.get_plugin_metrics(plugin_name)

#             await connection_manager.send_message(client_id, {"type": "metrics", "metrics": metrics})

#         except Exception as e:
#             await connection_manager.send_message(client_id, {"type": "metrics_error", "error": str(e)})

#     else:
#         # 转发给通用处理器
#         await handle_websocket_message(client_id, message)


# async def broadcast_plugin_event(event: PluginEvent):
#     """广播插件事件"""
#     await connection_manager.broadcast({"type": "plugin_event", "event": event.dict()}, event.plugin_name)


# # 设置通信管理器的事件处理
# async def setup_websocket_events():
#     """设置WebSocket事件处理"""
#     # 这里可以注册事件处理器
#     pass


# # 获取连接状态
# def get_websocket_stats() -> dict:
#     """获取WebSocket连接统计"""
#     return {
#         "total_connections": len(connection_manager.connections),
#         "plugin_subscriptions": {
#             plugin: len(clients) for plugin, clients in connection_manager.plugin_connections.items()
#         },
#     }
