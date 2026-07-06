# src/ai/controllers/v1/files/merge_chunks.py
"""合并分片控制器

提供文件分片合并接口。
"""

import os
import shutil
import aiofiles
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from loguru import logger

from framework.cache.dependencies import get_redis_client

router = APIRouter()
_logger = logger.bind(name=__name__)


class MergeChunksRequest(BaseModel):
    """合并分片请求"""
    file_id: str
    filename: str
    total_chunks: int


@router.post("/merge-chunks")
async def merge_chunks(
    request: MergeChunksRequest,
    redis: Redis = Depends(get_redis_client),
) -> ORJSONResponse:
    """合并文件分片"""

    try:
        file_id = request.file_id
        temp_dir = f"/tmp/uploads/{file_id}"

        # 1. 检查所有分片是否已上传
        redis_key = f"upload:{file_id}"
        uploaded_chunks = await redis.smembers(redis_key)

        if len(uploaded_chunks) != request.total_chunks:
            _logger.warning(f"Incomplete chunks: {len(uploaded_chunks)}/{request.total_chunks}")
            return ORJSONResponse(
                content={"code": 400, "msg": "分片不完整"},
                status_code=400,
            )

        # 2. 合并分片
        output_path = f"{temp_dir}/{request.filename}"
        async with aiofiles.open(output_path, 'wb') as outfile:
            for i in range(request.total_chunks):
                chunk_path = f"{temp_dir}/chunk_{i}"
                async with aiofiles.open(chunk_path, 'rb') as infile:
                    content = await infile.read()
                    await outfile.write(content)

        # 3. 上传到 MinIO（简化实现：返回本地路径）
        # 实际项目中应该使用 MinIO 存储
        url = f"file://{output_path}"

        # 4. 清理临时文件
        shutil.rmtree(temp_dir)
        await redis.delete(redis_key)

        _logger.info(f"Merged {request.total_chunks} chunks for file {file_id}")

        return ORJSONResponse(content={
            "code": 200,
            "msg": "文件上传成功",
            "data": {"url": url}
        })
    except Exception as e:
        _logger.error(f"Failed to merge chunks: {e}")
        return ORJSONResponse(
            content={"code": 500, "msg": "合并分片失败"},
            status_code=500,
        )
