"""
AI 模块管理后台控制器

提供插件的安装、卸载、启动、停止、升级等管理接口。
"""

from typing import Any

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import ORJSONResponse, StreamingResponse
from loguru import logger

from ai.schemas import (
    GetPluginInfoSuccessRespModel,
    GetPluginListSuccessRespModel,
    InstallPluginSuccessRespModel,
    PluginInvokeRequest,
    StartPluginSuccessRespModel,
    StopPluginSuccessRespModel,
    UninstallPluginSuccessRespModel,
)
from ai.services import plugin_management_service

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["管理端-插件管理"])


def Success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


@router.get(
    "",
    summary="获取插件列表",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件列表获取成功",
            "model": GetPluginListSuccessRespModel,
        },
    },
)
async def get_plugin_list(
    status: str | None = Query(None, description="插件状态过滤"),
    plugin_id: str | None = Query(None, description="插件id模糊查询"),
    plugin_type: str | None = Query(None, description="插件类型过滤"),
    limit: int = Query(50, ge=1, le=2000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> ORJSONResponse:
    """
    获取插件列表

    场景：管理员查询插件列表
    WHEN 请求 GET /admin/v1/plugins
    THEN 返回当前租户的所有插件列表
    """
    try:
        result = await plugin_management_service.get_plugin_list(
            status=status,
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            limit=limit,
            offset=offset,
        )
        return ORJSONResponse(content=Success(data=result.model_dump()))
    except Exception as e:
        _logger.exception("获取插件列表失败")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upload",
    summary="上传安装插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件安装成功",
            "model": InstallPluginSuccessRespModel,
        },
    },
)
async def upload_plugin(
    plugin_file: UploadFile = File(..., description="插件包文件(.zip格式)"),
    auto_start: bool = Form(True, description="是否自动启动插件"),
    install_config: str | None = Form(default="{}", description="安装配置(JSON字符串)"),
) -> ORJSONResponse:
    """
    上传安装插件

    场景：管理员上传插件包
    WHEN 请求 POST /admin/v1/plugins/upload
    THEN 安装插件并返回安装结果

    - **plugin_file**: 插件包文件，必须是.zip格式
    - **auto_start**: 是否在安装后自动启动插件
    - **install_config**: 安装配置，JSON格式的字符串
    """
    try:
        # 验证文件格式
        if not plugin_file.filename or not plugin_file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="插件文件必须是.zip格式")

        # 读取插件包内容
        plugin_package = await plugin_file.read()

        # 解析安装配置
        config = {}
        if install_config:
            import json

            try:
                config = json.loads(install_config)
            except json.JSONDecodeError:
                _logger.exception(
                    f"upload_plugin-> install_config:{install_config} 安装配置格式错误"
                )
                raise HTTPException(status_code=400, detail="安装配置格式错误")

        # 执行安装
        result = await plugin_management_service.install_plugin(
            plugin_package=plugin_package,
            auto_start=auto_start,
            install_config=config,
        )

        return ORJSONResponse(content=Success(data=result.model_dump()))

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("插件安装失败")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{plugin_id:path}/start",
    summary="启动插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件启动成功",
            "model": StartPluginSuccessRespModel,
        },
    },
)
async def start_plugin(
    plugin_id: str = Path(..., description="插件ID"),
) -> ORJSONResponse:
    """
    启动插件

    场景：管理员启动插件
    WHEN 请求 POST /admin/v1/plugins/{plugin_id}/start
    THEN 启动指定插件并返回结果
    """
    try:
        result = await plugin_management_service.start_plugin(plugin_id)
        return ORJSONResponse(content=Success(data=result.model_dump()))
    except Exception as e:
        _logger.exception(f"插件启动失败: {plugin_id}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{plugin_id:path}/stop",
    summary="停止插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件停止成功",
            "model": StopPluginSuccessRespModel,
        },
    },
)
async def stop_plugin(
    plugin_id: str = Path(..., description="插件ID"),
) -> ORJSONResponse:
    """
    停止插件

    场景：管理员停止插件
    WHEN 请求 POST /admin/v1/plugins/{plugin_id}/stop
    THEN 停止指定插件并返回结果
    """
    try:
        result = await plugin_management_service.stop_plugin(plugin_id)
        return ORJSONResponse(content=Success(data=result.model_dump()))
    except Exception as e:
        _logger.exception(f"插件停止失败: {plugin_id}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{plugin_id:path}/upgrade",
    summary="升级插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件升级成功",
            "model": InstallPluginSuccessRespModel,
        },
    },
)
async def upgrade_plugin(
    plugin_id: str = Path(..., description="插件ID"),
    plugin_file: UploadFile = File(..., description="插件包文件(.zip格式)"),
    auto_start: bool | None = Form(
        None, description="是否自动启动插件（默认沿用原设置）"
    ),
    install_config: str = Form(default="{}", description="安装配置(JSON字符串)"),
) -> ORJSONResponse:
    """
    升级插件

    场景：管理员升级插件
    WHEN 请求 POST /admin/v1/plugins/{plugin_id}/upgrade
    THEN 升级指定插件并返回结果

    注意：仅校验包内ID与路径ID一致，版本可升可降。
    """
    try:
        if not plugin_file.filename or not plugin_file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="插件文件必须是.zip格式")

        plugin_package = await plugin_file.read()

        # 解析安装配置
        config = {}
        if install_config:
            import json

            try:
                config = json.loads(install_config)
            except json.JSONDecodeError:
                _logger.exception(
                    f"upgrade_plugin-> install_config:{install_config} 安装配置格式错误"
                )
                raise HTTPException(status_code=400, detail="安装配置格式错误")

        # 执行升级
        result = await plugin_management_service.install_plugin(
            plugin_package=plugin_package,
            auto_start=auto_start if auto_start is not None else True,
            install_config=config,
        )
        return ORJSONResponse(content=Success(data=result.model_dump()))

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception(f"插件升级失败: {plugin_id}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{plugin_id:path}",
    summary="卸载插件",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件卸载成功",
            "model": UninstallPluginSuccessRespModel,
        },
    },
)
async def uninstall_plugin(
    plugin_id: str = Path(..., description="插件ID"),
) -> ORJSONResponse:
    """
    卸载插件

    场景：管理员卸载插件
    WHEN 请求 DELETE /admin/v1/plugins/{plugin_id}
    THEN 卸载指定插件并返回结果

    注意：此操作将完全移除插件，包括其所有数据和配置
    """
    try:
        result = await plugin_management_service.uninstall_plugin(plugin_id)
        return ORJSONResponse(content=Success(data=result.model_dump()))
    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("卸载插件失败")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{plugin_id:path}/invoke",
    summary="调用插件方法",
    responses={
        200: {
            "description": "插件流式调用成功",
            "content": {"text/event-stream": {}},
        },
    },
)
async def invoke_plugin(
    request: PluginInvokeRequest,
    plugin_id: str = Path(..., description="插件ID"),
):
    """
    调用插件方法

    场景：管理员调用插件
    WHEN 请求 POST /admin/v1/plugins/{plugin_id}/invoke
    THEN 流式返回调用结果

    - **plugin_id**: 插件ID
    - **parameters**: 调用参数
    - **timeout**: 超时时间（秒）
    """

    async def generate():
        try:
            result = plugin_management_service.invoke_plugin_stream(
                plugin_id=plugin_id,
                parameters=request.parameters,
                timeout=request.timeout,
            )

            async for chunk in result:
                # 将每个chunk转换为JSON字符串并加上换行符，用于流式传输
                import orjson

                yield orjson.dumps(chunk).decode("utf-8") + "\n"

        except Exception as e:
            # 在流式响应中发送错误信息
            import orjson

            error_chunk = {"error": True, "message": str(e), "plugin_id": plugin_id}
            yield orjson.dumps(error_chunk).decode("utf-8") + "\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/assets/{plugin_id}/{asset_path:path}",
    summary="获取插件资源文件内容",
    responses={
        200: {
            "description": "插件资源文件内容",
            "content": {"*/*": {}},
        },
    },
)
async def get_plugin_asset(
    plugin_id: str = Path(..., description="插件ID"),
    asset_path: str = Path(..., description="资源文件相对路径"),
) -> Response:
    """
    获取插件资源文件内容

    场景：获取插件资源
    WHEN 请求 GET /admin/v1/plugins/assets/{plugin_id}/{asset_path}
    THEN 返回资源文件内容

    支持图片、JSON、YAML等各种类型的资源文件
    """
    _logger.info(
        f"get_plugin_asset-> plugin_id:{plugin_id}, asset_path:{asset_path}"
    )

    try:
        # 通过service层获取插件资源文件内容
        content = await plugin_management_service.get_plugin_asset(
            plugin_id, asset_path
        )

        if content is None:
            raise HTTPException(status_code=404, detail=f"资源文件不存在: {asset_path}")

        # 根据文件扩展名确定Content-Type
        file_extension = asset_path.split(".")[-1].lower() if "." in asset_path else ""
        content_type_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "json": "application/json",
            "yaml": "application/x-yaml",
            "yml": "application/x-yaml",
            "txt": "text/plain",
            "md": "text/markdown",
            "css": "text/css",
            "js": "application/javascript",
            "html": "text/html",
        }
        content_type = content_type_map.get(file_extension, "application/octet-stream")

        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={asset_path.split('/')[-1]}",
                "Cache-Control": "public, max-age=36000",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception(f"获取插件资源文件内容失败: {plugin_id}/{asset_path}")
        raise HTTPException(status_code=500, detail=str(e))


# 注意：这个通用路径需要放到后面
# FastAPI 按照路由注册的顺序进行匹配，先注册的路由优先匹配
@router.get(
    "/{plugin_id:path}",
    summary="获取插件详细信息",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "插件详细信息获取成功",
            "model": GetPluginInfoSuccessRespModel,
        },
    },
)
async def get_plugin_info(
    plugin_id: str = Path(..., description="插件ID"),
) -> ORJSONResponse:
    """
    获取插件详细信息

    场景：管理员查询插件详情
    WHEN 请求 GET /admin/v1/plugins/{plugin_id}
    THEN 返回插件详细信息
    """
    try:
        result = await plugin_management_service.get_plugin_info(plugin_id)
        return ORJSONResponse(content=Success(data=result.model_dump()))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
