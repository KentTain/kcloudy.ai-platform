"""
AI 模块控制台控制器 - 批量运行时状态

提供批量查看运行时状态的接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas import GetRuntimeStateListSuccessRespModel
from ai.services import plugin_management_service
from framework.common.exceptions import BadRequestError
from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse

_logger = logger.bind(name=__name__)

router = APIRouter(tags=["控制台-运行时状态"])


@router.get(
    "",
    summary="批量获取运行时状态",
    response_class=ORJSONResponse,
    responses={
        200: {
            "description": "获取成功",
            "model": GetRuntimeStateListSuccessRespModel,
        },
    },
)
async def get_runtime_states(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    批量获取运行时状态

    场景：用户查看所有已安装插件的运行时状态摘要
    WHEN 请求 GET /console/v1/plugins/runtime-states
    THEN 返回所有插件的运行时状态列表，包含汇总统计
    """
    try:
        result = await plugin_management_service.get_runtime_states(session)
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        raise BadRequestError(f"获取运行时状态列表失败: {str(e)}")
    except Exception as e:
        _logger.exception("获取运行时状态列表失败")
        raise BadRequestError(f"获取运行时状态列表失败: {str(e)}")
