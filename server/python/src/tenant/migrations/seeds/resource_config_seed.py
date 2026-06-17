"""
资源配置种子数据初始化

从 application.yml 读取配置并创建默认资源配置。
包括数据库、缓存、存储、队列和发布订阅配置。
敏感字段使用 AES-256-GCM 加密。
"""

from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from framework.utils.crypto import encrypt
from framework.utils.log_util import write_info, write_success, write_warning
from tenant.models import (
    CacheConfig,
    DatabaseConfig,
    PubSubConfig,
    QueueConfig,
    StorageConfig,
)

DEFAULT_CONFIG_NAME = "default"


def _parse_database_url(url: str) -> dict[str, str | int]:
    """解析数据库连接字符串

    将 SQLAlchemy 格式的数据库 URL 解析为各组件。

    Args:
        url: 数据库连接字符串，如
            postgresql+asyncpg://user:password@localhost:5432/ai_platform

    Returns:
        包含 host, port, database, username, password, type 的字典
    """
    parsed = urlparse(url)

    # 从 scheme 中提取数据库类型，如 postgresql+asyncpg -> postgresql
    scheme = parsed.scheme or ""
    db_type = scheme.split("+")[0] if "+" in scheme else scheme

    return {
        "type": db_type,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "",
        "username": parsed.username or "",
        "password": parsed.password or "",
    }


async def _create_database_config(session, settings) -> bool:
    """创建默认数据库配置

    从 settings.sqlalchemy.url 读取连接信息并创建 DatabaseConfig。
    密码字段使用 AES-256-GCM 加密。

    Args:
        session: 异步数据库会话
        settings: 全局配置实例

    Returns:
        创建成功返回 True，已存在或失败返回 False
    """
    db_url = settings.sqlalchemy.url
    if not db_url:
        write_warning("数据库连接 URL 未配置，跳过创建数据库配置")
        return False

    # 检查是否已存在
    result = await session.execute(
        select(DatabaseConfig).where(DatabaseConfig.name == DEFAULT_CONFIG_NAME).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        write_info("默认数据库配置已存在，跳过创建")
        return False

    parsed = _parse_database_url(db_url)

    config = DatabaseConfig(
        name=DEFAULT_CONFIG_NAME,
        type=parsed["type"],
        host=parsed["host"],
        port=parsed["port"],
        database=parsed["database"],
        username=parsed["username"],
        password=encrypt(parsed["password"]) if parsed["password"] else "",
        is_default=True,
    )

    session.add(config)
    await session.flush()
    write_success(f"已创建默认数据库配置: {parsed['host']}:{parsed['port']}/{parsed['database']}")
    return True


async def _create_cache_config(session, settings) -> bool:
    """创建默认缓存配置

    从 settings.redis 读取连接信息并创建 CacheConfig。
    密码字段使用 AES-256-GCM 加密。

    Args:
        session: 异步数据库会话
        settings: 全局配置实例

    Returns:
        创建成功返回 True，已存在或失败返回 False
    """
    # 检查是否已存在
    result = await session.execute(
        select(CacheConfig).where(CacheConfig.name == DEFAULT_CONFIG_NAME).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        write_info("默认缓存配置已存在，跳过创建")
        return False

    redis_config = settings.redis
    single = redis_config.single

    config = CacheConfig(
        name=DEFAULT_CONFIG_NAME,
        host=single.host,
        port=single.port,
        password=encrypt(single.password) if single.password else None,
        db=single.db,
        prefix=None,
        is_default=True,
    )

    session.add(config)
    await session.flush()
    write_success(f"已创建默认缓存配置: {single.host}:{single.port}")
    return True


async def _create_storage_config(session, settings) -> bool:
    """创建默认存储配置

    从 settings.oss 读取连接信息并创建 StorageConfig。
    密钥字段使用 AES-256-GCM 加密。

    Args:
        session: 异步数据库会话
        settings: 全局配置实例

    Returns:
        创建成功返回 True，已存在或失败返回 False
    """
    # 检查是否已存在
    result = await session.execute(
        select(StorageConfig).where(StorageConfig.name == DEFAULT_CONFIG_NAME).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        write_info("默认存储配置已存在，跳过创建")
        return False

    oss_config = settings.oss
    minio_config = oss_config.minio

    # 如果未配置存储端点，跳过创建
    if not minio_config.endpoint and not oss_config.bucket:
        write_warning("存储服务未配置（缺少 endpoint 或 bucket），跳过创建存储配置")
        return False

    config = StorageConfig(
        name=DEFAULT_CONFIG_NAME,
        type=oss_config.default_type,
        bucket=oss_config.bucket,
        endpoint=minio_config.endpoint or None,
        access_key=minio_config.access_key or None,
        secret_key=encrypt(minio_config.secret_key) if minio_config.secret_key else None,
        is_default=True,
    )

    session.add(config)
    await session.flush()
    write_success(f"已创建默认存储配置: {oss_config.default_type} ({oss_config.bucket})")
    return True


async def _create_queue_config(session, settings) -> bool:
    """创建默认队列配置

    从 settings.redis 和 settings.messaging.queue 读取连接信息并创建 QueueConfig。
    密码字段使用 AES-256-GCM 加密。

    Args:
        session: 异步数据库会话
        settings: 全局配置实例

    Returns:
        创建成功返回 True，已存在或失败返回 False
    """
    # 检查是否已存在
    result = await session.execute(
        select(QueueConfig).where(QueueConfig.name == DEFAULT_CONFIG_NAME).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        write_info("默认队列配置已存在，跳过创建")
        return False

    redis_config = settings.redis
    single = redis_config.single
    queue_type = settings.messaging.queue.use

    config = QueueConfig(
        name=DEFAULT_CONFIG_NAME,
        type=queue_type,
        host=single.host,
        port=single.port,
        username=None,
        password=encrypt(single.password) if single.password else None,
        vhost=None,
        is_default=True,
    )

    session.add(config)
    await session.flush()
    write_success(f"已创建默认队列配置: {queue_type} ({single.host}:{single.port})")
    return True


async def _create_pubsub_config(session, settings) -> bool:
    """创建默认发布订阅配置

    从 settings.redis 和 settings.messaging.pubsub 读取连接信息并创建 PubSubConfig。
    密码字段使用 AES-256-GCM 加密。

    Args:
        session: 异步数据库会话
        settings: 全局配置实例

    Returns:
        创建成功返回 True，已存在或失败返回 False
    """
    # 检查是否已存在
    result = await session.execute(
        select(PubSubConfig).where(PubSubConfig.name == DEFAULT_CONFIG_NAME).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        write_info("默认发布订阅配置已存在，跳过创建")
        return False

    redis_config = settings.redis
    single = redis_config.single
    pubsub_type = settings.messaging.pubsub.use

    config = PubSubConfig(
        name=DEFAULT_CONFIG_NAME,
        type=pubsub_type,
        host=single.host,
        port=single.port,
        username=None,
        password=encrypt(single.password) if single.password else None,
        is_default=True,
    )

    session.add(config)
    await session.flush()
    write_success(f"已创建默认发布订阅配置: {pubsub_type} ({single.host}:{single.port})")
    return True


async def run(*, dry_run: bool = False) -> int:
    """初始化资源配置数据

    从 application.yml 读取配置并创建默认资源配置。
    如果默认配置已存在则跳过，支持 dry_run 模式预览。
    敏感字段使用 AES-256-GCM 加密，捕获 IntegrityError 处理并发创建。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.configs import get_settings
    from framework.database.core.engine import get_session

    settings = get_settings()
    created_count = 0

    async with get_session() as session:
        try:
            if dry_run:
                write_info("[DRY-RUN] 将创建默认资源配置（数据库、缓存、存储、队列、发布订阅）")
                return 5

            # 按顺序创建各类配置（每个函数内部检查是否已存在）
            if await _create_database_config(session, settings):
                created_count += 1

            if await _create_cache_config(session, settings):
                created_count += 1

            if await _create_storage_config(session, settings):
                created_count += 1

            if await _create_queue_config(session, settings):
                created_count += 1

            if await _create_pubsub_config(session, settings):
                created_count += 1

            await session.commit()

        except IntegrityError:
            # 并发创建时可能触发唯一约束冲突，回滚并跳过
            await session.rollback()
            write_warning("并发创建检测到冲突，跳过（默认资源配置可能已被其他进程创建）")
            return 0

        if created_count:
            write_success(f"已创建 {created_count} 项默认资源配置")
        else:
            write_warning("默认资源配置已初始化，无需变更")

        return created_count
