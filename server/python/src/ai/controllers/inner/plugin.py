"""
AI 模块内部接口控制器

提供模块间内部调用接口，不对外暴露。
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field

from ai.services import plugin_management_service

router = APIRouter()


def Success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


class PluginInfoResponse(BaseModel):
    """插件信息响应"""
    plugin_id: str = Field(..., description="插件ID")
    plugin_name: str = Field(..., description="插件名称")
    version: str = Field(..., description="版本号")
    author: str = Field(..., description="作者")
    status: str = Field(..., description="状态")
    plugin_type: str = Field(..., description="插件类型")
    runtime_type: str = Field(..., description="运行时类型")


class PluginInvokeRequest(BaseModel):
    """插件调用请求"""
    parameters: dict[str, Any] = Field(default_factory=dict, description="调用参数")
    timeout: int = Field(default=120, description="超时时间（秒）")


class PluginInvokeResponse(BaseModel):
    """插件调用响应"""
    plugin_id: str = Field(..., description="插件ID")
    result: dict[str, Any] | None = Field(default=None, description="调用结果")
    success: bool = Field(..., description="是否成功")
    error: str | None = Field(default=None, description="错误信息")


@router.get("/ai/health")
async def health_check() -> ORJSONResponse:
    """
    健康检查端点

    场景：健康检查
    WHEN 请求 GET /inner/v1/ai/health
    THEN 返回 {"status": "healthy"}
    """
    return ORJSONResponse(content={"status": "healthy", "module": "ai"})


@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str) -> ORJSONResponse:
    """
    获取单个插件信息

    场景：获取插件信息
    WHEN 请求 GET /inner/v1/plugins/{plugin_id}
    THEN 返回指定插件的详细信息
    AND 不依赖 Token 认证
    AND plugin_id 由调用方显式传入

    场景：插件不存在
    WHEN 请求 GET /inner/v1/plugins/nonexistent
    THEN 返回 HTTP 404
    """
    try:
        result = await plugin_management_service.get_plugin_info(plugin_id)
        return ORJSONResponse(
            content=Success(result.model_dump())
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/{plugin_id}/invoke")
async def invoke_plugin(
    plugin_id: str,
    request: PluginInvokeRequest,
) -> ORJSONResponse:
    """
    调用插件方法

    场景：内部调用插件
    WHEN 请求 POST /inner/v1/plugins/{plugin_id}/invoke
    THEN 执行插件调用并返回结果

    - **plugin_id**: 插件ID
    - **parameters**: 调用参数
    - **timeout**: 超时时间（秒）
    """
    try:
        # 收集流式结果
        result_chunks = []
        async for chunk in plugin_management_service.invoke_plugin_stream(
            plugin_id=plugin_id,
            parameters=request.parameters,
            timeout=request.timeout,
        ):
            result_chunks.append(chunk)

        # 合并结果
        if len(result_chunks) == 1:
            result = result_chunks[0]
        else:
            result = {"chunks": result_chunks}

        return ORJSONResponse(
            content=Success(
                PluginInvokeResponse(
                    plugin_id=plugin_id,
                    result=result,
                    success=True,
                    error=None,
                ).model_dump()
            )
        )
    except Exception as e:
        return ORJSONResponse(
            content=Success(
                PluginInvokeResponse(
                    plugin_id=plugin_id,
                    result=None,
                    success=False,
                    error=str(e),
                ).model_dump()
            )
        )


@router.get("/plugins/{plugin_id}/credentials")
async def get_plugin_credentials(plugin_id: str) -> ORJSONResponse:
    """
    获取插件凭证列表

    场景：获取插件凭证
    WHEN 请求 GET /inner/v1/plugins/{plugin_id}/credentials
    THEN 返回插件的凭证列表
    """
    try:
        total, items = await plugin_management_service.list_credentials(
            plugin_id=plugin_id,
            page=1,
            page_size=100,  # 内部接口默认返回较多数据
            name=None,
        )
        return ORJSONResponse(
            content=Success(
                {
                    "plugin_id": plugin_id,
                    "credentials": [item.model_dump() for item in items],
                    "total": total,
                }
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/{plugin_id}/credentials-schema")
async def get_plugin_credentials_schema(plugin_id: str) -> ORJSONResponse:
    """
    获取插件凭证架构

    场景：获取凭证架构
    WHEN 请求 GET /inner/v1/plugins/{plugin_id}/credentials-schema
    THEN 返回插件的凭证架构定义
    """
    try:
        schema = await plugin_management_service.get_plugin_credentials_schema(
            plugin_id
        )
        return ORJSONResponse(content=Success(schema))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
