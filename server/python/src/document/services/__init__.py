"""document 模块服务"""

from document.services.document_service import document_service
from document.services.folder_service import folder_service
from document.services.library_service import library_service
from document.services.member_service import member_service
from document.services.metadata_service import metadata_service
from document.services.permission_config_service import permission_config_service
from document.services.permission_service import PermissionService
from document.services.persona_service import persona_service
from document.services.recycle_service import recycle_service
from document.services.tag_service import tag_service

__all__ = [
    "library_service",
    "folder_service",
    "document_service",
    "member_service",
    "PermissionService",
    "permission_config_service",
    "tag_service",
    "persona_service",
    "recycle_service",
    "metadata_service",
]
