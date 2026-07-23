"""document 模块声明"""

from collections.abc import Callable

from document.models import Base
from framework.module.definition import MenuDef, ModuleDefinition, PermissionDef


class DocumentModule:
    """document 模块描述符"""

    @property
    def name(self) -> str:
        return "document"

    @property
    def schema(self) -> str:
        return "document"

    @property
    def dependencies(self) -> list[str]:
        # document 依赖 tenant 和 iam（通过 inner 接口获取用户/组织信息）
        return ["tenant", "iam"]

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        from document.controllers.admin.library_controller import router as admin_library_router
        from document.controllers.admin.persona_controller import router as admin_persona_router
        from document.controllers.admin.tag_controller import router as admin_tag_router
        from document.controllers.console.document_controller import router as console_document_router
        from document.controllers.console.folder_controller import router as console_folder_router
        from document.controllers.console.library_controller import router as console_library_router
        from document.controllers.console.member_controller import router as console_member_router
        from document.controllers.console.metadata_controller import router as console_metadata_router
        from document.controllers.console.permission_controller import router as console_permission_router
        from document.controllers.console.recycle_controller import router as console_recycle_router
        from document.controllers.inner.permission_controller import router as inner_permission_router
        from document.controllers.inner.permission_request_controller import (
            router as inner_permission_request_router,
        )

        return [
            (admin_library_router, "/document/admin/v1", ["Admin - Library"]),
            (admin_tag_router, "/document/admin/v1", ["Admin - Tag"]),
            (admin_persona_router, "/document/admin/v1", ["Admin - Persona"]),
            (console_library_router, "/document/console/v1", ["Console - Library"]),
            (console_folder_router, "/document/console/v1", ["Console - Folder"]),
            (console_document_router, "/document/console/v1", ["Console - Document"]),
            (console_member_router, "/document/console/v1", ["Console - Member"]),
            (console_permission_router, "/document/console/v1", ["Console - Permission"]),
            (console_recycle_router, "/document/console/v1", ["Console - Recycle"]),
            (console_metadata_router, "/document/console/v1", ["Console - Metadata"]),
            (inner_permission_router, "/document/inner/v1", ["Inner - Permission"]),
            (inner_permission_request_router, "/document/inner/v1", ["Inner - PermissionRequest"]),
        ]

    def get_middlewares(self) -> list[type]:
        return []

    def get_lifespan_hooks(self) -> list[Callable]:
        return []

    def get_seeds(self) -> dict[str, Callable]:
        from document.migrations.seeds.library_seed import run as library_seed_run
        return {"document_library": library_seed_run}

    def get_task_setup(self) -> tuple | None:
        from document.tasks.setup import cleanup_tasks, setup_tasks
        return (setup_tasks, cleanup_tasks)

    def get_listener_setup(self) -> tuple | None:
        from document.listeners.setup import cleanup_listeners, setup_listeners
        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition:
        return ModuleDefinition(
            code="document",
            name="文档库",
            description="文档库、文件管理、资源权限、标签、人设",
            icon="BookOpen",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="document.libraries",
                    name="文档库",
                    path="/document/libraries",
                    icon="FolderOpen",
                    sort_order=1,
                    permission_codes=["document:library:read"],
                ),
                MenuDef(
                    code="document.libraries.detail",
                    name="文档库详情",
                    path="/document/libraries/{id}",
                    parent_code="document.libraries",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["document:library:read"],
                ),
                MenuDef(
                    code="document.tags",
                    name="标签管理",
                    path="/document/tags",
                    icon="Tag",
                    sort_order=2,
                    permission_codes=["document:tag:read"],
                ),
                MenuDef(
                    code="document.personas",
                    name="人设管理",
                    path="/document/personas",
                    icon="UserCircle",
                    sort_order=3,
                    permission_codes=["document:persona:read"],
                ),
            ],
            permissions=[
                PermissionDef(code="document:library:read", name="查看文档库", resource="library", action="read"),
                PermissionDef(code="document:library:write", name="编辑文档库", resource="library", action="write"),
                PermissionDef(code="document:library:delete", name="删除文档库", resource="library", action="delete"),
                PermissionDef(code="document:folder:write", name="文件夹操作", resource="folder", action="write"),
                PermissionDef(code="document:file:upload", name="文件上传", resource="file", action="upload"),
                PermissionDef(code="document:file:download", name="文件下载", resource="file", action="download"),
                PermissionDef(code="document:tag:read", name="查看标签", resource="tag", action="read"),
                PermissionDef(code="document:tag:write", name="编辑标签", resource="tag", action="write"),
                PermissionDef(code="document:persona:read", name="查看人设", resource="persona", action="read"),
                PermissionDef(code="document:persona:write", name="编辑人设", resource="persona", action="write"),
                PermissionDef(code="document:permission:write", name="配置权限", resource="permission", action="write"),
                PermissionDef(code="document:recycle:purge", name="清空回收站", resource="recycle", action="purge"),
            ],
        )
