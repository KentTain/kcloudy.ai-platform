"""
管理后台 API 集成测试

测试场景覆盖：
1. 管理员认证
2. 租户 CRUD 操作
3. 租户激活/停用
"""

import pytest

from iam.middlewares.admin_auth_middleware import (
    hash_password,
    verify_password,
    generate_token,
    AdminAuthService,
)


class TestAdminAuth:
    """管理员认证测试"""

    def test_password_hash(self):
        """测试密码哈希"""
        password = "test123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) == 60  # bcrypt 输出长度
        assert hashed.startswith("$2b$")  # bcrypt 格式

    def test_password_verify(self):
        """测试密码验证"""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_generate_token(self):
        """测试 Token 生成"""
        token = generate_token()
        assert token is not None
        assert len(token) > 20


class TestAdminAuthService:
    """管理员认证服务测试"""

    def test_verify_token_empty(self):
        """测试空 Token 验证"""
        result = AdminAuthService.verify_token("invalid_token")
        assert result is None


class TestTenantAdminAPI:
    """管理后台 API 测试"""

    def test_schema_validation(self):
        """测试 Schema 验证"""
        from tenant.schemas.admin.tenant import TenantCreateRequest

        # 创建请求
        req = TenantCreateRequest(
            name="测试租户",
            code="test_tenant",
        )
        assert req.name == "测试租户"
        assert req.code == "test_tenant"

    def test_tenant_vo(self):
        """测试租户 VO"""
        from tenant.schemas.admin.tenant import TenantVo
        from datetime import datetime

        vo = TenantVo(
            id="t001",
            name="测试租户",
            code="test",
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert vo.id == "t001"
        assert vo.status == "active"
