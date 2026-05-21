"""
IAM 模块单元测试

测试 IAM 相关功能。
"""

import pytest


class TestIAMImports:
    """IAM 模块导入测试"""

    def test_import_models(self):
        """测试模型导入"""
        from iam.models import (
            User,
            Role,
            Permission,
            UserRole,
            RolePermission,
            Department,
            UserDepartment,
            OAuthConnection,
            Tenant,
            TenantAdmin,
            TenantConfig,
            UserTenant,
        )

        assert User is not None
        assert Role is not None
        assert Permission is not None

    def test_import_schemas(self):
        """测试 Schema 导入"""
        from iam.schemas import (
            LoginRequest,
            LoginResponse,
            UserVo,
            RoleVo,
            PermissionVo,
        )

        assert LoginRequest is not None
        assert UserVo is not None

    def test_import_services(self):
        """测试服务导入"""
        from iam.services import (
            auth_service,
            user_service,
            role_service,
            permission_service,
            department_service,
            oauth_service,
        )

        assert auth_service is not None
        assert user_service is not None

    def test_import_controllers(self):
        """测试控制器导入"""
        from iam.controllers import router

        assert router is not None


class TestPasswordStrength:
    """密码强度校验测试"""

    def test_valid_password(self):
        """有效密码"""
        from framework.utils.crypto import validate_password_strength

        assert validate_password_strength("Password123") is True
        assert validate_password_strength("Abc123xyz") is True

    def test_password_too_short(self):
        """密码太短"""
        from framework.utils.crypto import validate_password_strength
        import pytest

        with pytest.raises(ValueError, match="密码长度需 8-32 位"):
            validate_password_strength("Pass1")

    def test_password_no_letter(self):
        """密码无字母"""
        from framework.utils.crypto import validate_password_strength
        import pytest

        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            validate_password_strength("12345678")

    def test_password_no_digit(self):
        """密码无数字"""
        from framework.utils.crypto import validate_password_strength
        import pytest

        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            validate_password_strength("Password")


class TestJWTToken:
    """JWT Token 测试"""

    def test_generate_access_token(self):
        """生成 Access Token"""
        from framework.utils.jwt import generate_access_token

        payload = {
            "user_id": "user-123",
            "session_id": "session-456",
            "version": 1,
            "roles": ["user"],
            "permissions": ["user:read"],
        }
        token = generate_access_token(payload, "test-secret")

        assert token is not None
        assert token.count(".") == 2

    def test_verify_token(self):
        """验证 Token"""
        from framework.utils.jwt import generate_access_token, verify_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        token = generate_access_token(payload, "test-secret")

        result = verify_token(token, "test-secret")
        assert result is not None
        assert result["user_id"] == "user-123"

    def test_verify_token_invalid_secret(self):
        """验证 Token - 错误密钥"""
        from framework.utils.jwt import generate_access_token, verify_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        token = generate_access_token(payload, "correct-secret")

        result = verify_token(token, "wrong-secret")
        assert result is None

    def test_decode_token(self):
        """解析 Token"""
        from framework.utils.jwt import generate_access_token, decode_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        token = generate_access_token(payload, "test-secret")

        result = decode_token(token)
        assert result is not None
        assert result["user_id"] == "user-123"
