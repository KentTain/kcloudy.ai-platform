"""文件管理路由

提供文件上传、下载等接口。
"""

from fastapi import APIRouter

from ai.controllers.v1.files.upload import router as upload_router
from ai.controllers.v1.files.chunk_upload import router as chunk_upload_router

router = APIRouter(prefix="/files", tags=["文件管理"])
router.include_router(upload_router)
router.include_router(chunk_upload_router)
