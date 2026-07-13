"""
AI 模块插件包安装 Inner API
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import TenantContext
from pydantic import BaseModel

router = APIRouter()

_logger = logging.getLogger(__name__)


class InstallPluginRequest(BaseModel):
    """安装插件请求"""
    tenant_id: str
    plugin_id: str
    plugin_package: bytes  # 插件包字节


class InstallPluginResponse(BaseModel):
    """安装插件响应"""
    success: bool
    message: str = ""
    plugin_id: str


@router.post("/plugins/install-package")
async def install_plugin_package(
    tenant_id: str,
    plugin_id: str,
    plugin_package: bytes,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    安装插件包

    Args:
        tenant_id: 租户 ID
        plugin_id: 插件 ID
        plugin_package: 插件包字节
        session: 数据库会话

    Returns:
        安装结果
    """
    try:
        # 设置租户上下文
        TenantContext.set_tenant_id(tenant_id)

        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(tenant_id, session)

        # 调用 PluginManager.install_plugin 安装插件
        await manager.install_plugin(
            session=session,
            plugin_package=plugin_package,
            install_request=None,  # 无需安装请求，插件定义已经存在
        )

        _logger.info(f"插件安装成功: {plugin_id}")

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "success",
                "data": {
                    "success": True,
                    "plugin_id": plugin_id,
                },
            }
        )

    except Exception as e:
        _logger.exception(f"插件安装失败: {plugin_id}")
        return ORJSONResponse(
            content={
                "code": 500,
                "msg": str(e),
                "data": {
                    "success": False,
                    "plugin_id": plugin_id,
                },
            }
        )
