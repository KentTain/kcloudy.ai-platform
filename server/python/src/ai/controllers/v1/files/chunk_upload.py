# src/ai/controllers/v1/files/chunk_upload.py
"""分片上传控制器

提供文件分片上传和断点续传接口。
"""

import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from loguru import logger

from framework.cache.dependencies import get_redis_client

router = APIRouter()
_logger = logger.bind(name=__name__)


@router.post("/upload-chunk")
async def upload_chunk(
    file: UploadFile = File(...),
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    redis: Redis = Depends(get_redis_client),
) -> ORJSONResponse:
    """上传文件分片"""

    try:
        # 1. 创建临时目录
        temp_dir = f"/tmp/uploads/{file_id}"
        os.makedirs(temp_dir, exist_ok=True)

        # 2. 保存分片
        chunk_path = f"{temp_dir}/chunk_{chunk_index}"
        async with aiofiles.open(chunk_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 3. 记录到 Redis
        redis_key = f"upload:{file_id}"
        await redis.sadd(redis_key, chunk_index)
        await redis.expire(redis_key, 86400)  # 24 小时过期

        _logger.info(f"Uploaded chunk {chunk_index}/{total_chunks} for file {file_id}")

        return ORJSONResponse(content={
            "code": 200,
            "msg": "分片上传成功",
            "data": {
                "chunkIndex": chunk_index,
                "totalChunks": total_chunks,
            }
        })
    except Exception as e:
        _logger.error(f"Failed to upload chunk: {e}")
        return ORJSONResponse(
            content={"code": 500, "msg": "分片上传失败"},
            status_code=500,
        )


@router.get("/upload-state/{file_id}")
async def get_upload_state(
    file_id: str,
    redis: Redis = Depends(get_redis_client),
) -> ORJSONResponse:
    """查询上传状态（断点续传）"""

    redis_key = f"upload:{file_id}"
    uploaded_chunks = await redis.smembers(redis_key)

    return ORJSONResponse(content={
        "code": 200,
        "data": {
            "fileId": file_id,
            "uploadedChunks": [int(c) for c in uploaded_chunks],
        }
    })
