"""
Tenant 模块管理后台控制器
"""

from tenant.controllers.admin.marketplace_controller import router as marketplace_router

__all__ = ["marketplace_router"]
