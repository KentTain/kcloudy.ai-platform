# """
# 工具相关API路由
# 支持工具调用、凭证验证、运行时参数获取等功能
# """

# from typing import Any, Dict, List, Optional

# from fastapi import APIRouter, HTTPException
# from loguru import logger
# from pydantic import BaseModel

# from ai.components.plugin.engine.core.plugin_manager import PluginManager


# router = APIRouter()

# # 全局插件管理器实例
# _plugin_manager: Optional[PluginManager] = None


# def get_plugin_manager() -> PluginManager:
#     """获取插件管理器实例"""
#     global _plugin_manager
#     if not _plugin_manager:
#         _plugin_manager = PluginManager()
#     return _plugin_manager


# class ToolInvokeRequest(BaseModel):
#     """工具调用请求"""

#     tool: str
#     tool_parameters: Dict[str, Any]
#     user_id: str
#     credentials: Optional[Dict[str, Any]] = None


# class ToolCredentialsRequest(BaseModel):
#     """工具凭证验证请求"""

#     tool: Optional[str] = None
#     tool_name: Optional[str] = None
#     credentials: Optional[Dict[str, Any]] = None

#     @property
#     def get_tool_name(self) -> str:
#         """获取工具名称，支持tool和tool_name字段"""
#         return self.tool_name or self.tool or ""

#     def model_post_init(self, __context):
#         """验证至少有一个工具名称字段"""
#         if not self.tool and not self.tool_name:
#             raise ValueError("Either 'tool' or 'tool_name' must be provided")


# class ToolRuntimeParametersRequest(BaseModel):
#     """工具运行时参数请求"""

#     tool: str
#     credentials: Optional[Dict[str, Any]] = None


# @router.post("/invoke")
# async def invoke_tool(request: ToolInvokeRequest):
#     """调用工具"""
#     try:
#         manager = get_plugin_manager()

#         # 查找支持工具的插件
#         tool_plugins = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running" and plugin_name in manager.runtimes:
#                 tool_plugins.append(plugin_name)

#         if not tool_plugins:
#             raise HTTPException(status_code=404, detail="No tool plugins available")

#         # 使用第一个可用的工具插件
#         plugin_name = tool_plugins[0]

#         result = await manager.invoke_plugin(
#             plugin_name,
#             "invoke_tool",
#             {"tool": request.tool, "tool_parameters": request.tool_parameters, "user_id": request.user_id},
#         )

#         return result

#     except HTTPException:
#         # 重新抛出HTTP异常（如404）
#         raise
#     except Exception as e:
#         logger.error(f"工具调用失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/validate_credentials")
# async def validate_tool_credentials(request: ToolCredentialsRequest):
#     """验证工具凭证"""
#     try:
#         manager = get_plugin_manager()

#         # 查找支持工具的插件
#         tool_plugins = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running" and plugin_name in manager.runtimes:
#                 tool_plugins.append(plugin_name)

#         if not tool_plugins:
#             raise HTTPException(status_code=404, detail="No tool plugins available")

#         # 使用第一个可用的工具插件进行验证
#         plugin_name = tool_plugins[0]

#         result = await manager.invoke_plugin(
#             plugin_name,
#             "validate_tool_credentials",
#             {"tool": request.get_tool_name, "credentials": request.credentials},
#         )

#         return result

#     except HTTPException:
#         # 重新抛出HTTP异常（如404）
#         raise
#     except Exception as e:
#         logger.error(f"凭证验证失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/validate-credentials")
# async def validate_tool_credentials_kebab(request: ToolCredentialsRequest):
#     """验证工具凭证 - kebab-case路径"""
#     return await validate_tool_credentials(request)


# @router.post("/get_runtime_parameters")
# async def get_tool_runtime_parameters(request: ToolCredentialsRequest):
#     """获取工具运行时参数"""
#     try:
#         manager = get_plugin_manager()

#         # 查找支持工具的插件
#         tool_plugins = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running" and plugin_name in manager.runtimes:
#                 tool_plugins.append(plugin_name)

#         if not tool_plugins:
#             raise HTTPException(status_code=404, detail="No tool plugins available")

#         # 使用第一个可用的工具插件获取参数
#         plugin_name = tool_plugins[0]

#         result = await manager.invoke_plugin(
#             plugin_name,
#             "get_tool_runtime_parameters",
#             {"tool": request.get_tool_name, "credentials": request.credentials},
#         )

#         return result

#     except HTTPException:
#         # 重新抛出HTTP异常（如404）
#         raise
#     except Exception as e:
#         logger.error(f"获取运行时参数失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/runtime-parameters")
# async def get_tool_runtime_parameters_kebab(request: ToolCredentialsRequest):
#     """获取工具运行时参数 - kebab-case路径"""
#     return await get_tool_runtime_parameters(request)


# @router.post("/check")
# async def check_tool_existence(request: dict):
#     """检查工具是否存在"""
#     try:
#         tool_names = request.get("tool_names", []) or request.get("tools", [])
#         if not tool_names:
#             raise HTTPException(status_code=400, detail="tool_names或tools参数是必需的")

#         manager = get_plugin_manager()

#         # 模拟检查工具存在性
#         results = {}
#         for tool_name in tool_names:
#             # 简单的存在性检查
#             exists = tool_name in ["weather", "calculator", "translator"]
#             results[tool_name] = {
#                 "exists": exists,
#                 "available": exists,
#                 "plugin": f"plugin_for_{tool_name}" if exists else None,
#             }

#         return {"results": results, "total_checked": len(tool_names)}

#     except Exception as e:
#         logger.error(f"检查工具存在性失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/")
# async def list_tools():
#     """获取可用工具列表"""
#     try:
#         manager = get_plugin_manager()

#         # 收集所有工具
#         tools = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running":
#                 # 模拟工具信息
#                 plugin_tools = [
#                     {
#                         "name": "weather",
#                         "display_name": "天气查询",
#                         "description": "获取指定城市的天气信息",
#                         "plugin": plugin_name,
#                         "category": "utility",
#                         "icon": "",
#                         "parameters": [{"name": "city", "type": "string", "required": True, "description": "城市名称"}],
#                     }
#                 ]
#                 tools.extend(plugin_tools)

#         return {"tools": tools, "total": len(tools)}

#     except Exception as e:
#         logger.error(f"获取工具列表失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/list")
# async def list_tools_legacy():
#     """获取可用工具列表"""
#     try:
#         manager = get_plugin_manager()

#         # 收集所有工具
#         tools = []
#         for plugin_name, plugin_info in manager.plugins.items():
#             if plugin_info.status == "running":
#                 # 模拟工具信息
#                 plugin_tools = [
#                     {
#                         "name": "weather",
#                         "display_name": "天气查询",
#                         "description": "获取指定城市的天气信息",
#                         "plugin": plugin_name,
#                         "category": "utility",
#                         "icon": "",
#                         "parameters": [{"name": "city", "type": "string", "required": True, "description": "城市名称"}],
#                     }
#                 ]
#                 tools.extend(plugin_tools)

#         return {"success": True, "data": {"tools": tools, "total": len(tools)}}

#     except Exception as e:
#         logger.error(f"获取工具列表失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/check_existence")
# async def check_tool_existence(tools: List[str]):
#     """检查工具是否存在"""
#     try:
#         manager = get_plugin_manager()

#         # 可用工具列表（模拟）
#         available_tools = ["weather"]

#         existence_check = {}
#         for tool in tools:
#             existence_check[tool] = tool in available_tools

#         return {"success": True, "data": existence_check}

#     except Exception as e:
#         logger.error(f"检查工具存在性失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/categories")
# async def get_tool_categories():
#     """获取工具分类"""
#     try:
#         categories = [
#             {"id": "utility", "name": "实用工具", "description": "常用的实用工具", "icon": "", "tools_count": 1},
#             {"id": "data", "name": "数据处理", "description": "数据分析和处理工具", "icon": "", "tools_count": 0},
#             {
#                 "id": "communication",
#                 "name": "通讯工具",
#                 "description": "邮件、消息等通讯工具",
#                 "icon": "📧",
#                 "tools_count": 0,
#             },
#         ]

#         return {"success": True, "data": {"categories": categories, "total": len(categories)}}

#     except Exception as e:
#         logger.error(f"获取工具分类失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{tool_name}")
# async def get_tool_info(tool_name: str):
#     """获取工具详细信息"""
#     try:
#         manager = get_plugin_manager()

#         # 查找工具
#         if tool_name == "weather":
#             tool_info = {
#                 "name": "weather",
#                 "display_name": "天气查询",
#                 "description": "获取指定城市的天气信息",
#                 "version": "1.0.0",
#                 "author": "Demo Plugin Team",
#                 "category": "utility",
#                 "icon": "",
#                 "parameters": [
#                     {
#                         "name": "city",
#                         "type": "string",
#                         "required": True,
#                         "description": "城市名称，如：北京、上海",
#                         "example": "北京",
#                     },
#                     {
#                         "name": "unit",
#                         "type": "string",
#                         "required": False,
#                         "description": "温度单位",
#                         "default": "celsius",
#                         "options": ["celsius", "fahrenheit"],
#                     },
#                 ],
#                 "examples": [{"title": "查询北京天气", "parameters": {"city": "北京", "unit": "celsius"}}],
#                 "supported_features": ["real_time_data", "multiple_units", "weather_forecast"],
#             }

#             return {"success": True, "data": tool_info}
#         else:
#             raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"获取工具信息失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
