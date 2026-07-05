"""文件上传控制器

提供文件上传到对象存储的接口。
"""

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import ORJSONResponse
from loguru import logger

from ai.schemas.file import FileUploadResponse
from framework.common.ctx import get_tenant_id, get_user_id
from framework.configs.settings import get_settings
from framework.storage import get_storage_provider

router = APIRouter()
_logger = logger.bind(name=__name__)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
) -> ORJSONResponse:
    """上传文件到对象存储

    将文件上传到 MinIO 对象存储，路径格式为：
    ai/{tenant_id}/{user_id}/{filename}

    Returns:
        ORJSONResponse: 包含文件 URL、MIME 类型、文件名和大小
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 获取租户和用户信息
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        if not tenant_id:
            return ORJSONResponse(
                content={
                    "code": 401,
                    "msg": "未找到租户信息",
                },
                status_code=401,
            )

        # 构造文件路径
        filename = file.filename or "unknown"
        file_path = f"ai/{tenant_id}/{user_id}/{filename}" if user_id else f"ai/{tenant_id}/{filename}"

        # 获取存储提供者和 bucket 名称
        settings = get_settings()
        storage = get_storage_provider(settings.oss)
        bucket = settings.oss.bucket

        # 上传文件
        url = await storage.upload(
            bucket=bucket,
            name=file_path,
            data=content,
            content_type=file.content_type,
        )

        # 构造响应
        response = FileUploadResponse(
            url=url,
            media_type=file.content_type or "application/octet-stream",
            filename=filename,
            size=len(content),
        )

        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "上传成功",
                "data": response.model_dump(),
            }
        )

    except Exception as e:
        _logger.error(f"Failed to upload file: {e}")
        return ORJSONResponse(
            content={
                "code": 500,
                "msg": "文件上传失败",
            },
            status_code=500,
        )
