"""
E2E 测试模块

端到端测试用于验证完整的用户场景，包括真实的数据库、Redis、MinIO 等基础设施。

运行方式：
    # 运行所有 E2E 测试
    uv run pytest -m e2e tests/ai/e2e/

    # 运行特定 E2E 测试
    uv run pytest -m e2e tests/ai/e2e/test_plugin_lifecycle.py

注意：
    - E2E 测试默认跳过，需显式指定 -m e2e 才运行
    - E2E 测试需要完整的测试环境（数据库、Redis、MinIO）
    - 测试会创建隔离的测试租户和资源
"""
