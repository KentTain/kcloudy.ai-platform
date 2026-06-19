# """
# 安装任务管理API路由
# 对应Go版本中的安装任务管理功能
# """

# from typing import Any, Dict, List, Optional

# from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# from loguru import logger
# from pydantic import BaseModel

# from ai.components.plugin.engine.core.install_task_manager import InstallTaskManager, TaskStatus, TaskType
# from ai.components.plugin.engine.services.database_service import DatabaseError, get_install_task_service


# router = APIRouter(tags=["安装任务管理"])

# # 全局安装任务管理器
# _install_task_manager: Optional[InstallTaskManager] = None


# def get_install_task_manager() -> InstallTaskManager:
#     """获取安装任务管理器实例"""
#     global _install_task_manager
#     if not _install_task_manager:
#         # 初始化时注入数据库服务
#         try:
#             install_task_service = get_install_task_service()
#             _install_task_manager = InstallTaskManager()
#         except DatabaseError as e:
#             logger.warning(f"数据库不可用，使用内存存储: {e}")
#             _install_task_manager = InstallTaskManager()
#         except Exception as e:
#             logger.warning(f"初始化安装任务管理器时出错，使用默认配置: {e}")
#             _install_task_manager = InstallTaskManager()
#     return _install_task_manager


# class InstallFromIdentifiersRequest(BaseModel):
#     """从标识符安装请求"""

#     identifiers: List[str]
#     force: bool = False
#     auto_start: bool = True


# class UpgradePluginRequest(BaseModel):
#     """升级插件请求"""

#     plugin_name: str
#     version: Optional[str] = None
#     force: bool = False


# # ========== 插件安装相关接口 ==========


# @router.post("/create")
# async def create_install_task_from_package(
#     plugin_name: str = Form(...),
#     version: Optional[str] = Form(None),
#     force: bool = Form(False),
#     auto_start: bool = Form(True),
# ):
#     """从包信息创建安装任务"""
#     try:
#         identifier = f"{plugin_name}:{version}" if version else plugin_name

#         task_manager = get_install_task_manager()
#         task_id = await task_manager.create_install_task(
#             identifiers=[identifier],
#             task_type=TaskType.INSTALL,
#             metadata={"plugin_name": plugin_name, "version": version, "force": force, "auto_start": auto_start},
#         )

#         await task_manager.start_task(task_id)

#         return {"success": True, "message": f"创建安装任务: {plugin_name}", "task_id": task_id}

#     except Exception as e:
#         logger.error(f"创建安装任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/identifiers")
# async def install_plugin_from_identifiers(request: InstallFromIdentifiersRequest):
#     """从标识符安装插件"""
#     try:
#         task_manager = get_install_task_manager()
#         task_id = await task_manager.create_install_task(
#             identifiers=request.identifiers,
#             task_type=TaskType.INSTALL,
#             metadata={"force": request.force, "auto_start": request.auto_start},
#         )

#         # 自动启动任务
#         await task_manager.start_task(task_id)

#         return {
#             "success": True,
#             "message": f"创建安装任务，包含 {len(request.identifiers)} 个插件",
#             "task_id": task_id,
#             "identifiers": request.identifiers,
#         }

#     except Exception as e:
#         logger.error(f"从标识符安装插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/upload/package")
# async def upload_plugin_package(file: UploadFile = File(...), force: bool = Form(False), auto_start: bool = Form(True)):
#     """上传插件包安装"""
#     try:
#         if not file.filename.endswith(".zip"):
#             raise HTTPException(status_code=400, detail="只支持ZIP格式的插件文件")

#         # 创建安装任务
#         task_manager = get_install_task_manager()
#         task_id = await task_manager.create_install_task(
#             identifiers=[file.filename],
#             task_type=TaskType.INSTALL,
#             metadata={"upload_file": file.filename, "force": force, "auto_start": auto_start},
#         )

#         # 自动启动任务
#         await task_manager.start_task(task_id)

#         return {"success": True, "message": "插件包上传并开始安装", "task_id": task_id}

#     except Exception as e:
#         logger.error(f"上传插件包失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/upgrade")
# async def upgrade_plugin(request: UpgradePluginRequest):
#     """升级插件"""
#     try:
#         identifier = f"{request.plugin_name}:{request.version}" if request.version else request.plugin_name

#         task_manager = get_install_task_manager()
#         task_id = await task_manager.create_install_task(
#             identifiers=[identifier],
#             task_type=TaskType.UPGRADE,
#             metadata={"plugin_name": request.plugin_name, "target_version": request.version, "force": request.force},
#         )

#         # 自动启动任务
#         await task_manager.start_task(task_id)

#         return {"success": True, "message": f"创建升级任务: {request.plugin_name}", "task_id": task_id}

#     except Exception as e:
#         logger.error(f"升级插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/{task_id}")
# async def update_install_task(task_id: str, status: Optional[str] = None, progress: Optional[int] = None):
#     """更新安装任务状态"""
#     try:
#         task_manager = get_install_task_manager()
#         task = await task_manager.get_task(task_id)

#         if not task:
#             raise HTTPException(status_code=404, detail="任务不存在")

#         # 更新任务状态
#         if status:
#             task.status = TaskStatus(status)

#         if progress is not None:
#             await task_manager.update_task_progress(task_id, progress)

#         return {"success": True, "message": "任务状态已更新", "task_id": task_id}

#     except Exception as e:
#         logger.error(f"更新安装任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/delete-all")
# async def delete_all_install_tasks():
#     """删除所有安装任务"""
#     try:
#         task_manager = get_install_task_manager()
#         deleted_count = await task_manager.delete_all_tasks()

#         return {"success": True, "message": f"删除了 {deleted_count} 个任务"}

#     except Exception as e:
#         logger.error(f"删除所有任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/tasks/{task_id}/delete/{identifier}")
# async def delete_task_item(task_id: str, identifier: str):
#     """从任务中删除指定项目"""
#     try:
#         task_manager = get_install_task_manager()
#         success = await task_manager.delete_task_item(task_id, identifier)

#         if not success:
#             raise HTTPException(status_code=404, detail="任务或项目不存在")

#         return {"success": True, "message": f"从任务 {task_id} 中删除项目: {identifier}"}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"删除任务项目失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/tasks/statistics")
# async def get_task_statistics():
#     """获取任务统计信息"""
#     try:
#         task_manager = get_install_task_manager()
#         stats = await task_manager.get_task_statistics()

#         return {"success": True, "data": stats}

#     except Exception as e:
#         logger.error(f"获取统计信息失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/config")
# async def get_install_task_config():
#     """获取安装任务配置"""
#     try:
#         config = {
#             "max_concurrent_tasks": 5,
#             "task_timeout": 3600,
#             "retry_count": 3,
#             "auto_cleanup": True,
#             "supported_formats": ["zip", "tar.gz", "bundle"],
#             "default_task_type": "install",
#         }

#         return {"success": True, "config": config}

#     except Exception as e:
#         logger.error(f"获取配置失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.put("/config")
# async def update_install_task_config(config: Dict[str, Any]):
#     """更新安装任务配置"""
#     try:
#         # 这里应该保存配置到数据库或配置文件
#         logger.info(f"更新安装任务配置: {config}")

#         return {"success": True, "message": "配置已更新", "config": config}

#     except Exception as e:
#         logger.error(f"更新配置失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/templates")
# async def get_install_task_templates():
#     """获取安装任务模板"""
#     try:
#         templates = [
#             {
#                 "id": "standard_install",
#                 "name": "标准安装模板",
#                 "description": "用于标准插件安装的模板",
#                 "config": {"auto_start": True, "force": False, "timeout": 1800},
#             },
#             {
#                 "id": "batch_install",
#                 "name": "批量安装模板",
#                 "description": "用于批量插件安装的模板",
#                 "config": {"auto_start": True, "force": False, "max_concurrent": 3},
#             },
#         ]

#         return {"success": True, "templates": templates}

#     except Exception as e:
#         logger.error(f"获取模板失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/templates")
# async def create_install_task_template(template_data: Dict[str, Any]):
#     """创建安装任务模板"""
#     try:
#         template_id = f"template_{len(str(template_data))}"

#         return {"success": True, "message": "模板已创建", "template_id": template_id, "template": template_data}

#     except Exception as e:
#         logger.error(f"创建模板失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # ========== 安装任务管理接口 ==========


# @router.get("/{task_id}")
# async def get_installation_task(task_id: str):
#     """获取安装任务详情"""
#     try:
#         task_manager = get_install_task_manager()
#         task = await task_manager.get_task(task_id)

#         if not task:
#             raise HTTPException(status_code=404, detail="任务不存在")

#         return {"success": True, "data": task.to_dict()}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"获取安装任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/")
# async def list_installation_tasks(
#     status: Optional[str] = None, task_type: Optional[str] = None, limit: int = 50, offset: int = 0
# ):
#     """获取安装任务列表"""
#     try:
#         task_manager = get_install_task_manager()

#         # 转换枚举参数
#         status_enum = TaskStatus(status) if status else None
#         type_enum = TaskType(task_type) if task_type else None

#         tasks = await task_manager.list_tasks(status=status_enum, task_type=type_enum)

#         # 分页
#         total = len(tasks)
#         tasks = tasks[offset : offset + limit]

#         return {"tasks": [task.to_dict() for task in tasks], "total": total, "limit": limit, "offset": offset}

#     except Exception as e:
#         logger.error(f"获取安装任务列表失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/delete-all")
# async def delete_all_installation_tasks():
#     """删除所有安装任务"""
#     try:
#         task_manager = get_install_task_manager()
#         count = await task_manager.delete_all_tasks()

#         return {"success": True, "message": f"删除了 {count} 个任务"}

#     except Exception as e:
#         logger.error(f"删除所有任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/{task_id}")
# async def delete_installation_task(task_id: str):
#     """删除指定安装任务"""
#     try:
#         task_manager = get_install_task_manager()
#         success = await task_manager.delete_task(task_id)

#         if not success:
#             raise HTTPException(status_code=404, detail="任务不存在")

#         return {"success": True, "message": f"任务 {task_id} 已删除"}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"删除任务失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/tasks/{task_id}/delete/{identifier:path}")
# async def delete_installation_item_from_task(task_id: str, identifier: str):
#     """从任务中删除指定项目"""
#     try:
#         task_manager = get_install_task_manager()
#         success = await task_manager.delete_task_item(task_id, identifier)

#         if not success:
#             raise HTTPException(status_code=404, detail="任务或项目不存在")

#         return {"success": True, "message": f"从任务 {task_id} 中删除项目: {identifier}"}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"删除任务项目失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # ========== 插件信息获取接口 ==========


# @router.get("/fetch/manifest")
# async def fetch_plugin_manifest(identifier: str, version: Optional[str] = None):
#     """获取插件清单"""
#     try:
#         # 这里应该实现从插件标识符获取清单的逻辑
#         # 目前返回模拟数据
#         manifest = {
#             "identifier": identifier,
#             "name": f"Plugin for {identifier}",
#             "version": version or "1.0.0",
#             "description": f"示例插件: {identifier}",
#             "author": "Unknown",
#             "dependencies": [],
#             "capabilities": ["tool", "llm"],
#             "metadata": {"created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"},
#         }

#         return {"success": True, "data": manifest}

#     except Exception as e:
#         logger.error(f"获取插件清单失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/fetch/identifier")
# async def fetch_plugin_from_identifier(identifier: str, version: Optional[str] = None):
#     """从标识符获取插件信息"""
#     try:
#         # 这里应该实现从插件仓库或注册中心获取插件信息的逻辑
#         plugin_info = {
#             "identifier": identifier,
#             "name": f"Plugin {identifier}",
#             "version": version or "latest",
#             "description": f"从标识符获取的插件: {identifier}",
#             "download_url": f"https://plugins.example.com/{identifier}/download",
#             "manifest_url": f"https://plugins.example.com/{identifier}/manifest.json",
#             "metadata": {
#                 "size": 1024000,  # 1MB
#                 "checksum": "sha256:example123456",
#                 "created_at": "2024-01-01T00:00:00Z",
#             },
#         }

#         return {"success": True, "data": plugin_info}

#     except Exception as e:
#         logger.error(f"从标识符获取插件失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # ========== 批量操作接口 ==========


# class BatchFetchRequest(BaseModel):
#     """批量获取请求"""

#     ids: List[str]


# @router.post("/installation/fetch/batch")
# async def batch_fetch_plugin_installation_by_ids(request: BatchFetchRequest):
#     """批量获取插件安装信息"""
#     try:
#         task_manager = get_install_task_manager()

#         installations = []
#         for task_id in request.ids:
#             task = await task_manager.get_task(task_id)
#             if task:
#                 installations.append(task.to_dict())

#         return {
#             "success": True,
#             "data": {"installations": installations, "found": len(installations), "requested": len(request.ids)},
#         }

#     except Exception as e:
#         logger.error(f"批量获取安装信息失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/installation/missing")
# async def fetch_missing_plugin_installations(request: BatchFetchRequest):
#     """获取缺失的插件安装信息"""
#     try:
#         task_manager = get_install_task_manager()

#         missing_ids = []
#         for task_id in request.ids:
#             task = await task_manager.get_task(task_id)
#             if not task:
#                 missing_ids.append(task_id)

#         return {
#             "success": True,
#             "data": {
#                 "missing_ids": missing_ids,
#                 "missing_count": len(missing_ids),
#                 "total_requested": len(request.ids),
#             },
#         }

#     except Exception as e:
#         logger.error(f"获取缺失安装信息失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # ========== 任务统计接口 ==========


# @router.get("/tasks/statistics")
# async def get_installation_task_statistics():
#     """获取安装任务统计信息"""
#     try:
#         task_manager = get_install_task_manager()
#         stats = await task_manager.get_task_statistics()

#         return {"success": True, "data": stats}

#     except Exception as e:
#         logger.error(f"获取任务统计失败: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
