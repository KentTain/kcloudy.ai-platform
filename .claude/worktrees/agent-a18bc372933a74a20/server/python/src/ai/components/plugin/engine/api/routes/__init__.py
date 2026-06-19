# """
# 路由模块
# 定义API路由和处理器
# """

# from fastapi import APIRouter

# from .plugin import router as plugin_router
# from .health import router as health_router
# from .websocket import router as websocket_router

# # 创建主路由
# router = APIRouter()

# # 注册子路由
# router.include_router(health_router, tags=["健康检查"])
# router.include_router(plugin_router, prefix="/plugins", tags=["插件管理"])
# router.include_router(websocket_router, tags=["WebSocket通信"])

# __all__ = ["router"]
