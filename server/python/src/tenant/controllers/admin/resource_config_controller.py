"""
管理后台资源配置控制器

提供数据库、存储、缓存、队列、发布订阅配置的 CRUD 和连通性测试端点。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse

from tenant.middlewares.admin_auth_middleware import get_current_admin
from tenant.schemas.admin.resource_config import (
    # 数据库
    DatabaseConfigCreateRequest,
    DatabaseConfigUpdateRequest,
    DatabaseConfigResponse,
    DatabaseConfigListResponse,
    # 存储
    StorageConfigCreateRequest,
    StorageConfigUpdateRequest,
    StorageConfigResponse,
    StorageConfigListResponse,
    # 缓存
    CacheConfigCreateRequest,
    CacheConfigUpdateRequest,
    CacheConfigResponse,
    CacheConfigListResponse,
    # 队列
    QueueConfigCreateRequest,
    QueueConfigUpdateRequest,
    QueueConfigResponse,
    QueueConfigListResponse,
    # 发布订阅
    PubSubConfigCreateRequest,
    PubSubConfigUpdateRequest,
    PubSubConfigResponse,
    PubSubConfigListResponse,
    # 通用
    ConnectionTestResult,
    ResourceListQuery,
)
from tenant.services.database_config_service import DatabaseConfigService
from tenant.services.storage_config_service import StorageConfigService
from tenant.services.cache_config_service import CacheConfigService
from tenant.services.queue_config_service import QueueConfigService
from tenant.services.pubsub_config_service import PubSubConfigService

router = APIRouter()


def Success(data=None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


# =============================================================================
# 数据库配置端点
# =============================================================================

DB_PREFIX = "/resource-configs/databases"


@router.get(DB_PREFIX)
async def list_database_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    查询数据库配置列表
    """
    items, total = await DatabaseConfigService.list_configs(
        page=page, page_size=page_size, keyword=keyword
    )
    return ORJSONResponse(
        content=Success(
            DatabaseConfigListResponse(
                items=[
                    DatabaseConfigResponse(**DatabaseConfigService.build_response(item))
                    for item in items
                ],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump()
        )
    )


@router.post(DB_PREFIX)
async def create_database_config(
    data: DatabaseConfigCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    创建数据库配置
    """
    config = await DatabaseConfigService.create(**data.model_dump())
    return ORJSONResponse(
        content=Success(
            DatabaseConfigResponse(
                **DatabaseConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.get(f"{DB_PREFIX}/{{config_id}}")
async def get_database_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    获取单个数据库配置
    """
    config = await DatabaseConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return ORJSONResponse(
        content=Success(
            DatabaseConfigResponse(
                **DatabaseConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.put(f"{DB_PREFIX}/{{config_id}}")
async def update_database_config(
    config_id: str,
    data: DatabaseConfigUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    更新数据库配置
    """
    # 只传递非 None 的字段
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await DatabaseConfigService.update(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return ORJSONResponse(
        content=Success(
            DatabaseConfigResponse(
                **DatabaseConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.delete(f"{DB_PREFIX}/{{config_id}}")
async def delete_database_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    删除数据库配置
    """
    success = await DatabaseConfigService.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return ORJSONResponse(content=Success())


@router.post(f"{DB_PREFIX}/{{config_id}}/test-connection")
async def test_database_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """
    测试数据库连通性
    """
    success, message, latency = await DatabaseConfigService.test_connection(config_id)
    return ORJSONResponse(
        content=Success(
            ConnectionTestResult(
                success=success, message=message, latency_ms=latency
            ).model_dump()
        )
    )


# =============================================================================
# 存储配置端点
# =============================================================================

STORAGE_PREFIX = "/resource-configs/storages"


@router.get(STORAGE_PREFIX)
async def list_storage_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """查询存储配置列表"""
    items, total = await StorageConfigService.list_configs(
        page=page, page_size=page_size, keyword=keyword
    )
    return ORJSONResponse(
        content=Success(
            StorageConfigListResponse(
                items=[
                    StorageConfigResponse(**StorageConfigService.build_response(item))
                    for item in items
                ],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump()
        )
    )


@router.post(STORAGE_PREFIX)
async def create_storage_config(
    data: StorageConfigCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """创建存储配置"""
    config = await StorageConfigService.create(**data.model_dump())
    return ORJSONResponse(
        content=Success(
            StorageConfigResponse(
                **StorageConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.get(f"{STORAGE_PREFIX}/{{config_id}}")
async def get_storage_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """获取单个存储配置"""
    config = await StorageConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return ORJSONResponse(
        content=Success(
            StorageConfigResponse(
                **StorageConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.put(f"{STORAGE_PREFIX}/{{config_id}}")
async def update_storage_config(
    config_id: str,
    data: StorageConfigUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """更新存储配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await StorageConfigService.update(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return ORJSONResponse(
        content=Success(
            StorageConfigResponse(
                **StorageConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.delete(f"{STORAGE_PREFIX}/{{config_id}}")
async def delete_storage_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """删除存储配置"""
    success = await StorageConfigService.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return ORJSONResponse(content=Success())


@router.post(f"{STORAGE_PREFIX}/{{config_id}}/test-connection")
async def test_storage_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """测试存储连通性"""
    success, message, latency = await StorageConfigService.test_connection(config_id)
    return ORJSONResponse(
        content=Success(
            ConnectionTestResult(
                success=success, message=message, latency_ms=latency
            ).model_dump()
        )
    )


# =============================================================================
# 缓存配置端点
# =============================================================================

CACHE_PREFIX = "/resource-configs/caches"


@router.get(CACHE_PREFIX)
async def list_cache_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """查询缓存配置列表"""
    items, total = await CacheConfigService.list_configs(
        page=page, page_size=page_size, keyword=keyword
    )
    return ORJSONResponse(
        content=Success(
            CacheConfigListResponse(
                items=[
                    CacheConfigResponse(**CacheConfigService.build_response(item))
                    for item in items
                ],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump()
        )
    )


@router.post(CACHE_PREFIX)
async def create_cache_config(
    data: CacheConfigCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """创建缓存配置"""
    config = await CacheConfigService.create(**data.model_dump())
    return ORJSONResponse(
        content=Success(
            CacheConfigResponse(**CacheConfigService.build_response(config)).model_dump()
        )
    )


@router.get(f"{CACHE_PREFIX}/{{config_id}}")
async def get_cache_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """获取单个缓存配置"""
    config = await CacheConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return ORJSONResponse(
        content=Success(
            CacheConfigResponse(**CacheConfigService.build_response(config)).model_dump()
        )
    )


@router.put(f"{CACHE_PREFIX}/{{config_id}}")
async def update_cache_config(
    config_id: str,
    data: CacheConfigUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """更新缓存配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await CacheConfigService.update(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return ORJSONResponse(
        content=Success(
            CacheConfigResponse(**CacheConfigService.build_response(config)).model_dump()
        )
    )


@router.delete(f"{CACHE_PREFIX}/{{config_id}}")
async def delete_cache_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """删除缓存配置"""
    success = await CacheConfigService.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return ORJSONResponse(content=Success())


@router.post(f"{CACHE_PREFIX}/{{config_id}}/test-connection")
async def test_cache_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """测试缓存连通性"""
    success, message, latency = await CacheConfigService.test_connection(config_id)
    return ORJSONResponse(
        content=Success(
            ConnectionTestResult(
                success=success, message=message, latency_ms=latency
            ).model_dump()
        )
    )


# =============================================================================
# 队列配置端点
# =============================================================================

QUEUE_PREFIX = "/resource-configs/queues"


@router.get(QUEUE_PREFIX)
async def list_queue_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """查询队列配置列表"""
    items, total = await QueueConfigService.list_configs(
        page=page, page_size=page_size, keyword=keyword
    )
    return ORJSONResponse(
        content=Success(
            QueueConfigListResponse(
                items=[
                    QueueConfigResponse(**QueueConfigService.build_response(item))
                    for item in items
                ],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump()
        )
    )


@router.post(QUEUE_PREFIX)
async def create_queue_config(
    data: QueueConfigCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """创建队列配置"""
    config = await QueueConfigService.create(**data.model_dump())
    return ORJSONResponse(
        content=Success(
            QueueConfigResponse(**QueueConfigService.build_response(config)).model_dump()
        )
    )


@router.get(f"{QUEUE_PREFIX}/{{config_id}}")
async def get_queue_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """获取单个队列配置"""
    config = await QueueConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return ORJSONResponse(
        content=Success(
            QueueConfigResponse(**QueueConfigService.build_response(config)).model_dump()
        )
    )


@router.put(f"{QUEUE_PREFIX}/{{config_id}}")
async def update_queue_config(
    config_id: str,
    data: QueueConfigUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """更新队列配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await QueueConfigService.update(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return ORJSONResponse(
        content=Success(
            QueueConfigResponse(**QueueConfigService.build_response(config)).model_dump()
        )
    )


@router.delete(f"{QUEUE_PREFIX}/{{config_id}}")
async def delete_queue_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """删除队列配置"""
    success = await QueueConfigService.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return ORJSONResponse(content=Success())


@router.post(f"{QUEUE_PREFIX}/{{config_id}}/test-connection")
async def test_queue_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """测试队列连通性"""
    success, message, latency = await QueueConfigService.test_connection(config_id)
    return ORJSONResponse(
        content=Success(
            ConnectionTestResult(
                success=success, message=message, latency_ms=latency
            ).model_dump()
        )
    )


# =============================================================================
# 发布订阅配置端点
# =============================================================================

PUBSUB_PREFIX = "/resource-configs/pubsubs"


@router.get(PUBSUB_PREFIX)
async def list_pubsub_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """查询发布订阅配置列表"""
    items, total = await PubSubConfigService.list_configs(
        page=page, page_size=page_size, keyword=keyword
    )
    return ORJSONResponse(
        content=Success(
            PubSubConfigListResponse(
                items=[
                    PubSubConfigResponse(**PubSubConfigService.build_response(item))
                    for item in items
                ],
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump()
        )
    )


@router.post(PUBSUB_PREFIX)
async def create_pubsub_config(
    data: PubSubConfigCreateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """创建发布订阅配置"""
    config = await PubSubConfigService.create(**data.model_dump())
    return ORJSONResponse(
        content=Success(
            PubSubConfigResponse(
                **PubSubConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.get(f"{PUBSUB_PREFIX}/{{config_id}}")
async def get_pubsub_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """获取单个发布订阅配置"""
    config = await PubSubConfigService.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return ORJSONResponse(
        content=Success(
            PubSubConfigResponse(
                **PubSubConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.put(f"{PUBSUB_PREFIX}/{{config_id}}")
async def update_pubsub_config(
    config_id: str,
    data: PubSubConfigUpdateRequest,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """更新发布订阅配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await PubSubConfigService.update(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return ORJSONResponse(
        content=Success(
            PubSubConfigResponse(
                **PubSubConfigService.build_response(config)
            ).model_dump()
        )
    )


@router.delete(f"{PUBSUB_PREFIX}/{{config_id}}")
async def delete_pubsub_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """删除发布订阅配置"""
    success = await PubSubConfigService.delete(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return ORJSONResponse(content=Success())


@router.post(f"{PUBSUB_PREFIX}/{{config_id}}/test-connection")
async def test_pubsub_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
) -> ORJSONResponse:
    """测试发布订阅连通性"""
    success, message, latency = await PubSubConfigService.test_connection(config_id)
    return ORJSONResponse(
        content=Success(
            ConnectionTestResult(
                success=success, message=message, latency_ms=latency
            ).model_dump()
        )
    )
