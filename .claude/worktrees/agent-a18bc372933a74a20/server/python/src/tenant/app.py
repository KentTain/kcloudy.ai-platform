"""
Tenant 模块独立应用工厂

支持 Tenant 模块独立部署。
"""

from fastapi import FastAPI

from framework.configs import get_settings
from framework.tenant.protocols import TenantProvider, register_tenant_provider
from tenant.module import TenantModule
from tenant.services.tenant_provider_impl import TenantProviderImpl


def create_app() -> FastAPI:
    """
    创建 Tenant 模块独立应用

    Returns:
        FastAPI 应用实例
    """
    settings = get_settings()
    app = FastAPI(
        title="Tenant Service",
        description="租户管理服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 注册模块路由
    tenant_module = TenantModule()
    for router, prefix, tags in tenant_module.get_routers():
        app.include_router(router, prefix=prefix, tags=tags)

    # 注册 TenantProvider
    register_tenant_provider(TenantProviderImpl())

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "tenant"}

    return app
