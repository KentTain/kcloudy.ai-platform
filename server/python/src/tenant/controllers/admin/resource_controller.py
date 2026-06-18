"""
管理后台资源配置控制器

提供数据库、存储、缓存、队列、发布订阅配置的 CRUD 和连通性测试端点。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra
from tenant.middlewares.admin_auth_middleware import get_current_admin
from tenant.schemas.admin.resource_config import (
    # 缓存
    CacheConfigCreate,
    CacheConfigUpdate,
    CachePropertyResponse,
    # 通用
    ConnectionTestResult,
    # 数据库
    DatabaseConfigCreate,
    DatabaseConfigUpdate,
    DatabasePropertyResponse,
    # 发布订阅
    PubSubConfigCreate,
    PubSubConfigUpdate,
    PubSubPropertyResponse,
    # 队列
    QueueConfigCreate,
    QueueConfigUpdate,
    QueuePropertyResponse,
    ResourcePaginatedQuery,
    ResourceQuery,
    # 存储
    StorageConfigCreate,
    StorageConfigUpdate,
    StoragePropertyResponse,
)
from tenant.services.cache_config_service import CacheConfigService
from tenant.services.database_config_service import DatabaseConfigService
from tenant.services.pubsub_config_service import PubSubConfigService
from tenant.services.queue_config_service import QueueConfigService
from tenant.services.storage_config_service import StorageConfigService

router = APIRouter()


# =============================================================================
# 数据库配置端点
# =============================================================================

DB_PREFIX = "/resources/databases"


@router.get(DB_PREFIX)
async def list_database_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    查询数据库配置列表
    """
    items, total = await DatabaseConfigService.list_configs(
        session, page=page, page_size=page_size, keyword=keyword
    )
    return SuccessExtra(
        data=[
            DatabasePropertyResponse(**DatabaseConfigService.build_response(item))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(DB_PREFIX)
async def create_database_config(
    data: DatabaseConfigCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    创建数据库配置
    """
    config = await DatabaseConfigService.create(session, **data.model_dump())
    return Success(
        data=DatabasePropertyResponse(**DatabaseConfigService.build_response(config))
    )


@router.get(f"{DB_PREFIX}/{{config_id}}")
async def get_database_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取单个数据库配置
    """
    config = await DatabaseConfigService.get_by_id(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return Success(
        data=DatabasePropertyResponse(**DatabaseConfigService.build_response(config))
    )


@router.put(f"{DB_PREFIX}/{{config_id}}")
async def update_database_config(
    config_id: str,
    data: DatabaseConfigUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    更新数据库配置
    """
    # 只传递非 None 的字段
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await DatabaseConfigService.update(session, config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return Success(
        data=DatabasePropertyResponse(**DatabaseConfigService.build_response(config))
    )


@router.delete(f"{DB_PREFIX}/{{config_id}}")
async def delete_database_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    删除数据库配置
    """
    success = await DatabaseConfigService.delete(session, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return Success(data=success)


@router.post(f"{DB_PREFIX}/{{config_id}}/test-connection")
async def test_database_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    测试数据库连通性
    """
    success, message, latency = await DatabaseConfigService.test_connection(
        session, config_id
    )
    return Success(
        data=ConnectionTestResult(
            success=success, message=message, latency_ms=latency
        ).model_dump()
    )


# =============================================================================
# 存储配置端点
# =============================================================================

STORAGE_PREFIX = "/resources/storages"


@router.get(STORAGE_PREFIX)
async def list_storage_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询存储配置列表"""
    items, total = await StorageConfigService.list_configs(
        session, page=page, page_size=page_size, keyword=keyword
    )
    return SuccessExtra(
        data=[
            StoragePropertyResponse(**StorageConfigService.build_response(item))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(STORAGE_PREFIX)
async def create_storage_config(
    data: StorageConfigCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建存储配置"""
    config = await StorageConfigService.create(session, **data.model_dump())
    return Success(
        data=StoragePropertyResponse(**StorageConfigService.build_response(config))
    )


@router.get(f"{STORAGE_PREFIX}/{{config_id}}")
async def get_storage_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取单个存储配置"""
    config = await StorageConfigService.get_by_id(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return Success(
        data=StoragePropertyResponse(**StorageConfigService.build_response(config))
    )


@router.put(f"{STORAGE_PREFIX}/{{config_id}}")
async def update_storage_config(
    config_id: str,
    data: StorageConfigUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新存储配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await StorageConfigService.update(session, config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return Success(
        data=StoragePropertyResponse(**StorageConfigService.build_response(config))
    )


@router.delete(f"{STORAGE_PREFIX}/{{config_id}}")
async def delete_storage_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除存储配置"""
    success = await StorageConfigService.delete(session, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="存储配置不存在")
    return Success(data=success)


@router.post(f"{STORAGE_PREFIX}/{{config_id}}/test-connection")
async def test_storage_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """测试存储连通性"""
    success, message, latency = await StorageConfigService.test_connection(
        session, config_id
    )
    return Success(
        data=ConnectionTestResult(
            success=success, message=message, latency_ms=latency
        ).model_dump()
    )


# =============================================================================
# 缓存配置端点
# =============================================================================

CACHE_PREFIX = "/resources/caches"


@router.get(CACHE_PREFIX)
async def list_cache_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询缓存配置列表"""
    items, total = await CacheConfigService.list_configs(
        session, page=page, page_size=page_size, keyword=keyword
    )
    return SuccessExtra(
        data=[
            CachePropertyResponse(**CacheConfigService.build_response(item))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(CACHE_PREFIX)
async def create_cache_config(
    data: CacheConfigCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建缓存配置"""
    config = await CacheConfigService.create(session, **data.model_dump())
    return Success(
        data=CachePropertyResponse(**CacheConfigService.build_response(config))
    )


@router.get(f"{CACHE_PREFIX}/{{config_id}}")
async def get_cache_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取单个缓存配置"""
    config = await CacheConfigService.get_by_id(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return Success(
        data=CachePropertyResponse(**CacheConfigService.build_response(config))
    )


@router.put(f"{CACHE_PREFIX}/{{config_id}}")
async def update_cache_config(
    config_id: str,
    data: CacheConfigUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新缓存配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await CacheConfigService.update(session, config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return Success(
        data=CachePropertyResponse(**CacheConfigService.build_response(config))
    )


@router.delete(f"{CACHE_PREFIX}/{{config_id}}")
async def delete_cache_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除缓存配置"""
    success = await CacheConfigService.delete(session, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="缓存配置不存在")
    return Success(data=success)


@router.post(f"{CACHE_PREFIX}/{{config_id}}/test-connection")
async def test_cache_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """测试缓存连通性"""
    success, message, latency = await CacheConfigService.test_connection(
        session, config_id
    )
    return Success(
        data=ConnectionTestResult(
            success=success, message=message, latency_ms=latency
        ).model_dump()
    )


# =============================================================================
# 队列配置端点
# =============================================================================

QUEUE_PREFIX = "/resources/queues"


@router.get(QUEUE_PREFIX)
async def list_queue_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询队列配置列表"""
    items, total = await QueueConfigService.list_configs(
        session, page=page, page_size=page_size, keyword=keyword
    )
    return SuccessExtra(
        data=[
            QueuePropertyResponse(**QueueConfigService.build_response(item))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(QUEUE_PREFIX)
async def create_queue_config(
    data: QueueConfigCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建队列配置"""
    config = await QueueConfigService.create(session, **data.model_dump())
    return Success(
        data=QueuePropertyResponse(**QueueConfigService.build_response(config))
    )


@router.get(f"{QUEUE_PREFIX}/{{config_id}}")
async def get_queue_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取单个队列配置"""
    config = await QueueConfigService.get_by_id(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return Success(
        data=QueuePropertyResponse(**QueueConfigService.build_response(config))
    )


@router.put(f"{QUEUE_PREFIX}/{{config_id}}")
async def update_queue_config(
    config_id: str,
    data: QueueConfigUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新队列配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await QueueConfigService.update(session, config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return Success(
        data=QueuePropertyResponse(**QueueConfigService.build_response(config))
    )


@router.delete(f"{QUEUE_PREFIX}/{{config_id}}")
async def delete_queue_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除队列配置"""
    success = await QueueConfigService.delete(session, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="队列配置不存在")
    return Success(data=success)


@router.post(f"{QUEUE_PREFIX}/{{config_id}}/test-connection")
async def test_queue_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """测试队列连通性"""
    success, message, latency = await QueueConfigService.test_connection(
        session, config_id
    )
    return Success(
        data=ConnectionTestResult(
            success=success, message=message, latency_ms=latency
        ).model_dump()
    )


# =============================================================================
# 发布订阅配置端点
# =============================================================================

PUBSUB_PREFIX = "/resources/pubsubs"


@router.get(PUBSUB_PREFIX)
async def list_pubsub_configs(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询发布订阅配置列表"""
    items, total = await PubSubConfigService.list_configs(
        session, page=page, page_size=page_size, keyword=keyword
    )
    return SuccessExtra(
        data=[
            PubSubPropertyResponse(**PubSubConfigService.build_response(item))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(PUBSUB_PREFIX)
async def create_pubsub_config(
    data: PubSubConfigCreate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建发布订阅配置"""
    config = await PubSubConfigService.create(session, **data.model_dump())
    return Success(
        data=PubSubPropertyResponse(**PubSubConfigService.build_response(config))
    )


@router.get(f"{PUBSUB_PREFIX}/{{config_id}}")
async def get_pubsub_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取单个发布订阅配置"""
    config = await PubSubConfigService.get_by_id(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return Success(
        data=PubSubPropertyResponse(**PubSubConfigService.build_response(config))
    )


@router.put(f"{PUBSUB_PREFIX}/{{config_id}}")
async def update_pubsub_config(
    config_id: str,
    data: PubSubConfigUpdate,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新发布订阅配置"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await PubSubConfigService.update(session, config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return Success(
        data=PubSubPropertyResponse(**PubSubConfigService.build_response(config))
    )


@router.delete(f"{PUBSUB_PREFIX}/{{config_id}}")
async def delete_pubsub_config(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """删除发布订阅配置"""
    success = await PubSubConfigService.delete(session, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="发布订阅配置不存在")
    return Success(data=success)


@router.post(f"{PUBSUB_PREFIX}/{{config_id}}/test-connection")
async def test_pubsub_connection(
    config_id: str,
    admin: dict = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """测试发布订阅连通性"""
    success, message, latency = await PubSubConfigService.test_connection(
        session, config_id
    )
    return Success(
        data=ConnectionTestResult(
            success=success, message=message, latency_ms=latency
        ).model_dump()
    )
