"""
jwt 模块单元测试

测试 JWT Token 生成、验证和解析功能
"""

import time
from datetime import datetime, timedelta, timezone

import pytest


class TestGenerateAccessToken:
    """Access Token 生成测试"""

    def test_generate_access_token_success(self):
        """
        场景：生成 Access Token 成功
        WHEN: 提供有效用户信息和密钥
        THEN: 返回有效的 JWT Token
        """
        from framework.utils.jwt import generate_access_token

        payload = {
            "user_id": "user-123",
            "session_id": "session-456",
            "version": 1,
            "roles": ["user"],
            "permissions": ["user:read", "user:write"],
        }
        secret = "test-secret-key"

        token = generate_access_token(payload, secret)

        # JWT 格式：header.payload.signature
        assert token.count(".") == 2
        assert len(token) > 50

    def test_generate_access_token_contains_required_claims(self):
        """
        场景：Token 包含必要声明
        WHEN: 生成 Token
        THEN: 包含 user_id、session_id、version、roles、permissions、exp
        """
        import jwt

        from framework.utils.jwt import generate_access_token

        payload = {
            "user_id": "user-123",
            "session_id": "session-456",
            "version": 1,
            "roles": ["admin"],
            "permissions": ["*"],
        }
        secret = "test-secret-key"

        token = generate_access_token(payload, secret)
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert decoded["user_id"] == "user-123"
        assert decoded["session_id"] == "session-456"
        assert decoded["version"] == 1
        assert decoded["roles"] == ["admin"]
        assert decoded["permissions"] == ["*"]
        assert "exp" in decoded

    def test_generate_access_token_expiry(self):
        """
        场景：Token 过期时间正确
        WHEN: 生成 Access Token
        THEN: 过期时间为 2 小时后
        """
        import jwt

        from framework.utils.jwt import generate_access_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "test-secret-key"

        before = datetime.now(timezone.utc)
        token = generate_access_token(payload, secret)
        after = datetime.now(timezone.utc)

        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

        # 过期时间应该在约 2 小时后
        expected_min = before + timedelta(hours=1.9)
        expected_max = after + timedelta(hours=2.1)
        assert expected_min < exp < expected_max


class TestGenerateRefreshToken:
    """Refresh Token 生成测试"""

    def test_generate_refresh_token_success(self):
        """
        场景：生成 Refresh Token 成功
        WHEN: 提供有效用户信息和密钥
        THEN: 返回有效的 JWT Token
        """
        from framework.utils.jwt import generate_refresh_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "test-secret-key"

        token = generate_refresh_token(payload, secret)

        assert token.count(".") == 2

    def test_generate_refresh_token_expiry(self):
        """
        场景：Refresh Token 过期时间正确
        WHEN: 生成 Refresh Token
        THEN: 过期时间为 7 天后
        """
        import jwt

        from framework.utils.jwt import generate_refresh_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "test-secret-key"

        before = datetime.now(timezone.utc)
        token = generate_refresh_token(payload, secret)
        after = datetime.now(timezone.utc)

        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

        # 过期时间应该在约 7 天后
        expected_min = before + timedelta(days=6.9)
        expected_max = after + timedelta(days=7.1)
        assert expected_min < exp < expected_max


class TestVerifyToken:
    """Token 验证测试"""

    def test_verify_token_valid(self):
        """
        场景：验证有效 Token
        WHEN: Token 有效且未过期
        THEN: 返回解码后的 payload
        """
        from framework.utils.jwt import generate_access_token, verify_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "test-secret-key"

        token = generate_access_token(payload, secret)
        result = verify_token(token, secret)

        assert result is not None
        assert result["user_id"] == "user-123"
        assert result["session_id"] == "session-456"

    def test_verify_token_expired(self):
        """
        场景：验证过期 Token
        WHEN: Token 已过期
        THEN: 返回 None
        """
        import jwt

        from framework.utils.jwt import verify_token

        secret = "test-secret-key"
        # 创建一个已过期的 Token
        expired_payload = {
            "user_id": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

        result = verify_token(expired_token, secret)
        assert result is None

    def test_verify_token_invalid_signature(self):
        """
        场景：验证签名无效的 Token
        WHEN: 使用错误的密钥签名
        THEN: 返回 None
        """
        from framework.utils.jwt import generate_access_token, verify_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "correct-secret"
        wrong_secret = "wrong-secret"

        token = generate_access_token(payload, secret)
        result = verify_token(token, wrong_secret)

        assert result is None

    def test_verify_token_malformed(self):
        """
        场景：验证格式错误的 Token
        WHEN: Token 格式无效
        THEN: 返回 None
        """
        from framework.utils.jwt import verify_token

        result = verify_token("invalid.token.format", "secret")
        assert result is None

    def test_verify_token_empty(self):
        """
        场景：验证空 Token
        WHEN: Token 为空
        THEN: 返回 None
        """
        from framework.utils.jwt import verify_token

        result = verify_token("", "secret")
        assert result is None


class TestDecodeToken:
    """Token 解析测试"""

    def test_decode_token_success(self):
        """
        场景：解析 Token 成功
        WHEN: Token 有效
        THEN: 返回 payload（不验证过期）
        """
        from framework.utils.jwt import generate_access_token, decode_token

        payload = {"user_id": "user-123", "session_id": "session-456"}
        secret = "test-secret-key"

        token = generate_access_token(payload, secret)
        result = decode_token(token)

        assert result is not None
        assert result["user_id"] == "user-123"

    def test_decode_token_without_verification(self):
        """
        场景：解析过期 Token（不验证过期）
        WHEN: Token 已过期但只解析不验证
        THEN: 仍能返回 payload
        """
        import jwt

        from framework.utils.jwt import decode_token

        secret = "test-secret-key"
        expired_payload = {
            "user_id": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

        result = decode_token(expired_token)
        assert result is not None
        assert result["user_id"] == "user-123"

    def test_decode_token_invalid(self):
        """
        场景：解析无效 Token
        WHEN: Token 格式错误
        THEN: 返回 None
        """
        from framework.utils.jwt import decode_token

        result = decode_token("not-a-valid-jwt")
        assert result is None


class TestTokenType:
    """Token 类型常量测试"""

    def test_token_type_constants(self):
        """
        场景：Token 类型常量存在
        WHEN: 导入 Token 类型
        THEN: 包含 ACCESS 和 REFRESH
        """
        from framework.utils.jwt import TokenType

        assert hasattr(TokenType, "ACCESS")
        assert hasattr(TokenType, "REFRESH")

    def test_access_token_expiry_constant(self):
        """
        场景：Access Token 过期时间常量
        WHEN: 检查过期时间配置
        THEN: 默认为 2 小时
        """
        from framework.utils.jwt import ACCESS_TOKEN_EXPIRY_HOURS

        assert ACCESS_TOKEN_EXPIRY_HOURS == 2

    def test_refresh_token_expiry_constant(self):
        """
        场景：Refresh Token 过期时间常量
        WHEN: 检查过期时间配置
        THEN: 默认为 7 天
        """
        from framework.utils.jwt import REFRESH_TOKEN_EXPIRY_DAYS

        assert REFRESH_TOKEN_EXPIRY_DAYS == 7
