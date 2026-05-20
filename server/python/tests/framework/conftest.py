"""
Framework 模块测试 Fixtures

整合单元测试和集成测试的 fixtures。
"""

# 导入集成测试 fixtures
from tests.framework.conftest_integration import *

__all__ = [
    # 配置
    "integration_settings",
    # 服务可用性检测
    "redis_available",
    "postgres_available",
    "minio_available",
    # Redis fixtures
    "redis_client",
    "redis_key_prefix",
    "redis_cleanup",
    # PostgreSQL fixtures
    "postgres_engine",
    "postgres_session",
    # MinIO fixtures
    "minio_client",
    "minio_test_bucket",
    "minio_cleanup",
    # 工具函数
    "unique_id",
    "wait_for_condition",
]
