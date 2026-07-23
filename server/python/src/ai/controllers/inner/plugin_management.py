"""
AI 模块插件管理 Inner API 控制器

提供插件管理相关的内部接口，供其他模块调用。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginConfig
from ai.models.plugin import PluginRuntimeState
from ai.schemas.plugin_management import (
    BatchInstallRequest,
    BatchInstallResponse,
    InstallFailedItem,
    InstallSkippedItem,
    InstallSuccessItem,
    StartPluginResponse,
    StopPluginResponse,
)
from ai.services import plugin_management_service
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext

router = APIRouter()

_logger = logging.getLogger(__name__)


@router.post("/plugins/install-batch")
async def batch_install_plugins(
    request: BatchInstallRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    批量安装插件到租户

    为多个租户创建插件配置和运行时状态记录。

    Args:
        request: 批量安装请求，包含安装项列表
        session: 数据库会话

    Returns:
        批量安装响应，包含成功/失败/跳过列表
    """
    success = []
    failed = []
    skipped = []

    for item in request.installations:
        try:
            # 设置租户上下文
            TenantContext.set_tenant_id(item.tenant_id)

            # 检查是否已存在 PluginConfig
            stmt = select(PluginConfig).where(
                PluginConfig.tenant_id == item.tenant_id,
                PluginConfig.plugin_id == item.plugin_id,
            )
            result = await session.execute(stmt)
            existing_config = result.scalar_one_or_none()

            if existing_config:
                skipped.append(
                    InstallSkippedItem(
                        tenant_id=item.tenant_id,
                        reason="already_installed",
                    )
                )
                continue

            # 创建 PluginConfig
            config = PluginConfig(
                tenant_id=item.tenant_id,
                plugin_id=item.plugin_id,
                plugin_unique_identifier=item.plugin_unique_identifier,
                plugin_config=item.declaration,
                runtime_config={},
            )
            session.add(config)

            # 创建 PluginRuntimeState
            runtime_state = PluginRuntimeState(
                tenant_id=item.tenant_id,
                plugin_id=item.plugin_id,
                status="inactive",
            )
            session.add(runtime_state)

            success.append(
                InstallSuccessItem(
                    tenant_id=item.tenant_id,
                    plugin_id=item.plugin_id,
                )
            )

        except Exception as e:
            _logger.error(
                f"批量安装失败: tenant_id={item.tenant_id}, "
                f"plugin_id={item.plugin_id}, error={e}",
                exc_info=True,
            )
            failed.append(
                InstallFailedItem(
                    tenant_id=item.tenant_id,
                    message=str(e),
                )
            )

    # 刷新事务，确保数据写入
    await session.flush()

    return ApiResponse.success(
        data=BatchInstallResponse(
            success=success,
            failed=failed,
            skipped=skipped,
        ).model_dump()
    )


@router.post("/plugins/{plugin_id}/start")
async def start_plugin(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    启动插件

    Args:
        plugin_id: 插件ID
        session: 数据库会话

    Returns:
        启动插件响应
    """
    try:
        result = await plugin_management_service.start_plugin_with_response(
            session, plugin_id
        )

        return ApiResponse.success(
            data=StartPluginResponse(
                plugin_id=result.plugin_id,
                message=result.message,
                status=result.status,
                success=result.success,
                process_id=result.process_id,
                port=result.port,
            ).model_dump()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.error(f"启动插件失败: plugin_id={plugin_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动插件失败: {str(e)}")


@router.post("/plugins/{plugin_id}/stop")
async def stop_plugin(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    停止插件

    Args:
        plugin_id: 插件ID
        session: 数据库会话

    Returns:
        停止插件响应
    """
    try:
        result = await plugin_management_service.stop_plugin_with_response(
            session, plugin_id
        )

        return ApiResponse.success(
            data=StopPluginResponse(
                plugin_id=result.plugin_id,
                message=result.message,
                status=result.status,
                success=result.success,
            ).model_dump()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.error(f"停止插件失败: plugin_id={plugin_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止插件失败: {str(e)}")
