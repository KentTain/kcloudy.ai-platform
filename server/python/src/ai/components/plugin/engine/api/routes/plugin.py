# """
# 插件管理路由
# 提供插件的安装、启动、停止、调用等接口
# """

# from typing import Optional

# from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# from loguru import logger

# from ai.components.plugin.engine.core.plugin_manager import PluginManager
# from ai.components.plugin.engine.models.request import (
#     InstallRequest,
#     InvokeRequest,
#     InvokeResponse,
#     MetricsResponse,
#     SuccessResponse,
# )


# router = APIRouter()

# # 全局插件管理器实例
# _plugin_manager: Optional[PluginManager] = None


# def get_plugin_manager() -> PluginManager:
#     """获取插件管理器实例"""
#     global _plugin_manager
#     if not _plugin_manager:
#         _plugin_manager = PluginManager()
#     return _plugin_manager


# @router.get("/")
# async def list_plugins(page: int = 1, page_size: int = 20, status: Optional[str] = None):
#     """获取插件列表"""

#     try:
#         manager = get_plugin_manager()
#         plugins = await manager.list_plugins()

#         # 状态过滤
#         if status:
#             plugins = [p for p in plugins if p.status == status]

#         # 分页
#         total = len(plugins)
#         start = (page - 1) * page_size
#         end = start + page_size
#         plugins = plugins[start:end]

#         # 转换为字典格式
#         plugin_data = []
#         for plugin in plugins:
#             plugin_data.append(
#                 {
#                     "name": plugin.get("name"),
#                     "version": plugin.get("version"),
#                     "description": plugin.get("description"),
#                     "author": plugin.get("author", "unknown"),
#                     "status": plugin.get("status"),
#                     "runtime_type": plugin.get("runtime_type"),
#                     "installed_at": plugin.get("installed_at"),
#                     "started_at": plugin.get("started_at"),
#                     "pid": plugin.get("pid"),
#                     "port": plugin.get("port"),
#                     "error_message": plugin.get("error_message"),
#                 }
#             )

#         return {
#             "plugins": plugin_data,
#             "pagination": {"total": total, "page": page, "limit": page_size, "page_size": page_size},
#         }

#     except Exception as e:
#         logger.error(f"获取插件列表失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/install", response_model=SuccessResponse)
# async def install_plugin(
#     file: UploadFile = File(...),
#     force: bool = Form(False),
#     auto_start: bool = Form(True),
#     config_override: str = Form("{}"),
# ):
#     """安装插件"""

#     try:
#         # 验证文件类型
#         if not file.filename.endswith(".zip"):
#             raise HTTPException(status_code=400, detail="只支持ZIP格式的插件文件")

#         # 读取文件内容
#         file_content = await file.read()

#         # 解析配置覆盖
#         import json

#         try:
#             config_override_dict = json.loads(config_override)
#         except json.JSONDecodeError:
#             config_override_dict = {}

#         # 创建安装请求
#         install_request = InstallRequest(force=force, auto_start=auto_start, config_override=config_override_dict)

#         # 安装插件
#         manager = get_plugin_manager()
#         plugin_name = await manager.install_plugin(file_content, install_request)

#         return SuccessResponse(message=f"插件 {plugin_name} 安装成功", data={"plugin_name": plugin_name})

#     except HTTPException:
#         raise
#     except ValueError as e:
#         # 插件解析失败等业务逻辑错误
#         error_msg = str(e)
#         if "File is not a zip file" in error_msg:
#             raise HTTPException(status_code=400, detail="文件格式无效，不是有效的ZIP文件")
#         elif "找不到manifest.yaml" in error_msg or "找不到plugin.yaml" in error_msg:
#             raise HTTPException(status_code=400, detail="插件包格式无效，缺少配置文件")
#         else:
#             raise HTTPException(status_code=400, detail=f"插件包解析失败: {error_msg}")
#     except Exception as e:
#         logger.error(f"安装插件失败: {e}")
#         if "插件包解析失败" in str(e):
#             raise HTTPException(status_code=400, detail=str(e))
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{plugin_name}", response_model=dict)
# async def get_plugin_info(plugin_name: str):
#     """获取插件详细信息"""

#     try:
#         manager = get_plugin_manager()
#         plugin_info = await manager.get_plugin_info(plugin_name)

#         if not plugin_info:
#             raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

#         # plugin_info 已经是字典，直接构建响应
#         return {
#             "config": {
#                 "name": plugin_info.get("name", ""),
#                 "version": plugin_info.get("version", ""),
#                 "description": plugin_info.get("description", ""),
#                 "author": plugin_info.get("author", ""),
#                 "type": plugin_info.get("type", ""),
#             },
#             "status": plugin_info.get("status", "unknown"),
#             "pid": plugin_info.get("pid"),
#             "port": plugin_info.get("port"),
#             "work_dir": plugin_info.get("work_dir"),
#             "log_file": plugin_info.get("log_file"),
#             "error_message": plugin_info.get("error_message"),
#             "installed_at": plugin_info.get("installed_at"),
#             "started_at": plugin_info.get("started_at"),
#             "stopped_at": plugin_info.get("stopped_at"),
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"获取插件信息失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{plugin_name}/start", response_model=SuccessResponse)
# async def start_plugin(plugin_name: str):
#     """启动插件"""

#     try:
#         manager = get_plugin_manager()
#         success = await manager.start_plugin(plugin_name)

#         if success:
#             return SuccessResponse(message=f"插件 {plugin_name} 启动成功")
#         else:
#             raise HTTPException(status_code=500, detail=f"插件 {plugin_name} 启动失败")

#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         logger.error(f"启动插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{plugin_name}/stop", response_model=SuccessResponse)
# async def stop_plugin(plugin_name: str):
#     """停止插件"""

#     try:
#         manager = get_plugin_manager()

#         # 首先检查插件是否存在
#         if not manager.is_plugin_installed(plugin_name):
#             raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

#         success = await manager.stop_plugin(plugin_name)

#         if success:
#             return SuccessResponse(message=f"插件 {plugin_name} 停止成功")
#         else:
#             raise HTTPException(status_code=500, detail=f"插件 {plugin_name} 停止失败")

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"停止插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{plugin_name}/restart", response_model=SuccessResponse)
# async def restart_plugin(plugin_name: str):
#     """重启插件"""

#     try:
#         manager = get_plugin_manager()
#         # 重启 = 停止 + 启动，与Go框架保持一致
#         await manager.stop_plugin(plugin_name)
#         await manager.start_plugin(plugin_name)

#         return SuccessResponse(message=f"插件 {plugin_name} 重启成功")

#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         logger.error(f"重启插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{plugin_name}", response_model=SuccessResponse)
# async def uninstall_plugin(plugin_name: str):
#     """卸载插件"""

#     try:
#         manager = get_plugin_manager()
#         success = await manager.uninstall_plugin(plugin_name)

#         if success:
#             return SuccessResponse(message=f"插件 {plugin_name} 卸载成功")
#         else:
#             raise HTTPException(status_code=500, detail=f"插件 {plugin_name} 卸载失败")

#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         logger.error(f"卸载插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/uninstall", response_model=SuccessResponse)
# async def uninstall_plugin(plugin_data: dict):
#     """卸载插件"""

#     try:
#         plugin_name = plugin_data.get("plugin_name")
#         force = plugin_data.get("force", False)

#         if not plugin_name:
#             raise HTTPException(status_code=422, detail="plugin_name is required")

#         manager = get_plugin_manager()
#         success = await manager.uninstall_plugin(plugin_name)

#         if success:
#             return SuccessResponse(message=f"插件 {plugin_name} 卸载成功")
#         else:
#             raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"卸载插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/{plugin_name}/invoke", response_model=InvokeResponse)
# async def invoke_plugin(plugin_name: str, request: InvokeRequest):
#     """调用插件方法"""

#     try:
#         manager = get_plugin_manager()

#         import time

#         start_time = time.time()

#         result = await manager.invoke_plugin(plugin_name, request.action, request.parameters, request.timeout)

#         execution_time = (time.time() - start_time) * 1000  # 转换为毫秒

#         return InvokeResponse(
#             success=result.get("success", True),
#             data=result.get("data"),
#             error=result.get("error"),
#             error_code=result.get("error_code"),
#             execution_time=execution_time,
#             request_id=request.request_id,
#         )

#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         logger.error(f"调用插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{plugin_name}/metrics", response_model=MetricsResponse)
# async def get_plugin_metrics(plugin_name: str):
#     """获取插件性能指标"""

#     try:
#         manager = get_plugin_manager()
#         metrics = await manager.get_plugin_metrics(plugin_name)

#         if metrics is None:
#             raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 未运行或不存在")

#         return MetricsResponse(plugin_name=plugin_name, metrics=metrics)

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"获取插件指标失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{plugin_name}/logs")
# async def get_plugin_logs(plugin_name: str, limit: int = 100, level: Optional[str] = None):
#     """获取插件日志"""

#     try:
#         manager = get_plugin_manager()
#         logs = await manager.get_plugin_logs(plugin_name, limit, level)

#         return {"plugin_name": plugin_name, "logs": logs, "total": len(logs)}

#     except Exception as e:
#         logger.error(f"获取插件日志失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{plugin_name}/status")
# async def get_plugin_status(plugin_name: str):
#     """获取插件状态"""

#     try:
#         manager = get_plugin_manager()
#         plugin_info = await manager.get_plugin_info(plugin_name)

#         if not plugin_info:
#             raise HTTPException(status_code=404, detail=f"插件 {plugin_name} 不存在")

#         # 如果插件正在运行，获取健康状态
#         health_status = None
#         if plugin_name in manager.runtimes:
#             runtime = manager.runtimes[plugin_name]
#             try:
#                 health_status = await runtime.health_check()
#             except Exception:
#                 health_status = False

#         return {
#             "plugin_name": plugin_name,
#             "status": plugin_info.get("status", "unknown"),
#             "health": health_status,
#             "pid": plugin_info.get("pid"),
#             "port": plugin_info.get("port"),
#             "uptime": None,  # 待实现：计算插件运行时间
#             "error_message": plugin_info.get("error_message"),
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"获取插件状态失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
