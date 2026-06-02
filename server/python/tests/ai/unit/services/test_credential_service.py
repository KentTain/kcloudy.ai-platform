# CredentialService 单元测试

import pytest
from unittest.mock import patch

from ai.services.credential_service import CredentialService


class TestCredentialServiceEncrypt:
    """凭证加密测试"""

    def test_encrypt_sensitive_fields(self, credential_schema, sample_credentials):
        """测试敏感字段被加密"""
        service = CredentialService()
        
        with patch("ai.services.credential_service.encrypt") as mock_encrypt:
            mock_encrypt.return_value = "encrypted_value"
            
            result = service.encrypt_credentials(sample_credentials, credential_schema)
            
            # api_key 和 api_secret 是敏感字段，应该被加密
            assert mock_encrypt.call_count == 2
            assert result["api_key"] == "encrypted_value"
            assert result["api_secret"] == "encrypted_value"

    def test_encrypt_preserves_non_sensitive_fields(self, credential_schema, sample_credentials):
        """测试非敏感字段保持原值"""
        service = CredentialService()
        
        with patch("ai.services.credential_service.encrypt") as mock_encrypt:
            mock_encrypt.return_value = "encrypted_value"
            
            result = service.encrypt_credentials(sample_credentials, credential_schema)
            
            # endpoint 和 model_type 非敏感，保持原值
            assert result["endpoint"] == "https://api.example.com"
            assert result["model_type"] == "gpt-4"

    def test_encrypt_empty_credentials(self, credential_schema):
        """测试空凭证返回空字典"""
        service = CredentialService()
        
        result = service.encrypt_credentials({}, credential_schema)
        
        assert result == {}

    def test_encrypt_none_credentials(self, credential_schema):
        """测试 None 凭证返回空字典"""
        service = CredentialService()
        
        result = service.encrypt_credentials(None, credential_schema)
        
        assert result == {}

    def test_encrypt_preserves_none_values(self, credential_schema):
        """测试 None 值字段保持 None"""
        service = CredentialService()
        credentials = {"api_key": None, "endpoint": "https://api.example.com"}
        
        with patch("ai.services.credential_service.encrypt") as mock_encrypt:
            mock_encrypt.return_value = "encrypted_value"
            
            result = service.encrypt_credentials(credentials, credential_schema)
            
            assert result["api_key"] is None
            assert mock_encrypt.call_count == 0

    def test_encrypt_failure_falls_back_to_original(self, credential_schema):
        """测试加密失败时降级保留原值"""
        service = CredentialService()
        credentials = {"api_key": "test-key"}
        
        with patch("ai.services.credential_service.encrypt") as mock_encrypt:
            mock_encrypt.side_effect = Exception("Encryption failed")
            
            result = service.encrypt_credentials(credentials, credential_schema)
            
            # 加密失败时保留原值
            assert result["api_key"] == "test-key"


class TestCredentialServiceDecrypt:
    """凭证解密测试"""

    def test_decrypt_sensitive_fields(self, credential_schema):
        """测试敏感字段被解密"""
        service = CredentialService()
        encrypted = {
            "api_key": "encrypted_key",
            "api_secret": "encrypted_secret",
            "endpoint": "https://api.example.com",
        }
        
        with patch("ai.services.credential_service.decrypt") as mock_decrypt:
            mock_decrypt.side_effect = lambda x: f"decrypted_{x}"
            
            result = service.decrypt_credentials(encrypted, credential_schema)
            
            assert mock_decrypt.call_count == 2
            assert result["api_key"] == "decrypted_encrypted_key"
            assert result["api_secret"] == "decrypted_encrypted_secret"

    def test_decrypt_preserves_non_sensitive_fields(self, credential_schema):
        """测试非敏感字段保持原值"""
        service = CredentialService()
        encrypted = {
            "api_key": "encrypted_key",
            "endpoint": "https://api.example.com",
            "model_type": "gpt-4",
        }
        
        with patch("ai.services.credential_service.decrypt") as mock_decrypt:
            mock_decrypt.return_value = "decrypted_value"
            
            result = service.decrypt_credentials(encrypted, credential_schema)
            
            assert result["endpoint"] == "https://api.example.com"
            assert result["model_type"] == "gpt-4"

    def test_decrypt_empty_credentials(self, credential_schema):
        """测试空凭证返回空字典"""
        service = CredentialService()
        
        result = service.decrypt_credentials({}, credential_schema)
        
        assert result == {}

    def test_decrypt_failure_falls_back_to_original(self, credential_schema):
        """测试解密失败时降级保留原值"""
        service = CredentialService()
        encrypted = {"api_key": "encrypted_key"}
        
        with patch("ai.services.credential_service.decrypt") as mock_decrypt:
            mock_decrypt.side_effect = Exception("Decryption failed")
            
            result = service.decrypt_credentials(encrypted, credential_schema)
            
            assert result["api_key"] == "encrypted_key"


class TestCredentialServiceMask:
    """凭证脱敏测试"""

    def test_mask_short_value(self, credential_schema):
        """测试短字符串脱敏（<=8字符）"""
        service = CredentialService()
        credentials = {"api_key": "abc123"}  # 6 characters
        
        result = service.mask_credentials(credentials, credential_schema)
        
        # 短字符串显示首尾各2个字符
        assert result["api_key"] == "ab...23"

    def test_mask_medium_value(self, credential_schema):
        """测试中等长度字符串脱敏（9-16字符）"""
        service = CredentialService()
        credentials = {"api_key": "abcdefghijk"}  # 11 characters
        
        result = service.mask_credentials(credentials, credential_schema)
        
        # 中等长度显示首尾各4个字符
        assert result["api_key"] == "abcd....hijk"

    def test_mask_long_value(self, credential_schema):
        """测试长字符串脱敏（>16字符）"""
        service = CredentialService()
        credentials = {"api_key": "sk-test-api-key-12345678"}  # 23 characters
        
        result = service.mask_credentials(credentials, credential_schema)
        
        # 长字符串显示首尾各5个字符
        assert result["api_key"] == "sk-te....45678"

    def test_mask_very_short_value(self, credential_schema):
        """测试非常短的字符串脱敏（<=4字符）"""
        service = CredentialService()
        credentials = {"api_key": "abc"}  # 3 characters
        
        result = service.mask_credentials(credentials, credential_schema)
        
        # 非常短的字符串显示 ****
        assert result["api_key"] == "****"

    def test_mask_preserves_non_sensitive_fields(self, credential_schema):
        """测试非敏感字段不脱敏"""
        service = CredentialService()
        credentials = {
            "api_key": "secret-key",
            "endpoint": "https://api.example.com",
        }
        
        result = service.mask_credentials(credentials, credential_schema)
        
        assert result["endpoint"] == "https://api.example.com"

    def test_mask_empty_value(self, credential_schema):
        """测试空字符串脱敏"""
        service = CredentialService()
        credentials = {"api_key": ""}
        
        result = service.mask_credentials(credentials, credential_schema)
        
        assert result["api_key"] == ""

    def test_mask_none_value(self, credential_schema):
        """测试 None 值脱敏"""
        service = CredentialService()
        credentials = {"api_key": None}
        
        result = service.mask_credentials(credentials, credential_schema)
        
        assert result["api_key"] is None


class TestCredentialServiceValidate:
    """凭证格式校验测试"""

    def test_validate_required_field_missing(self, credential_schema):
        """测试必填字段缺失"""
        service = CredentialService()
        credentials = {"endpoint": "https://api.example.com"}  # 缺少 api_key
        
        with pytest.raises(ValueError, match="api_key.*必填"):
            service.validate_credentials_format(credentials, credential_schema)

    def test_validate_string_type(self, credential_schema):
        """测试字符串类型校验"""
        service = CredentialService()
        credentials = {
            "api_key": "test-key",
            "api_secret": "test-secret",
            "endpoint": 123,  # 应该是字符串
            "model_type": "gpt-4",
        }
        
        with pytest.raises(ValueError, match="endpoint.*字符串类型"):
            service.validate_credentials_format(credentials, credential_schema)

    def test_validate_select_option_valid(self, credential_schema):
        """测试 select 类型选项值有效"""
        service = CredentialService()
        credentials = {
            "api_key": "test-key",
            "api_secret": "test-secret",
            "model_type": "gpt-4",  # 有效选项
        }
        
        # 不应抛出异常
        service.validate_credentials_format(credentials, credential_schema)

    def test_validate_select_option_invalid(self, credential_schema):
        """测试 select 类型选项值无效"""
        service = CredentialService()
        credentials = {
            "api_key": "test-key",
            "api_secret": "test-secret",
            "model_type": "invalid-model",  # 无效选项
        }
        
        with pytest.raises(ValueError, match="model_type.*以下之一"):
            service.validate_credentials_format(credentials, credential_schema)

    def test_validate_empty_schema(self):
        """测试空 schema 不校验"""
        service = CredentialService()
        credentials = {"any_field": "any_value"}
        
        # 不应抛出异常
        service.validate_credentials_format(credentials, [])

    def test_validate_optional_field_can_be_none(self, credential_schema):
        """测试可选字段可以为 None"""
        service = CredentialService()
        credentials = {
            "api_key": "test-key",
            "api_secret": "test-secret",
            "model_type": "gpt-4",
            "endpoint": None,  # 可选字段，可以为 None
        }
        
        # 不应抛出异常
        service.validate_credentials_format(credentials, credential_schema)


class TestCredentialServiceExtract:
    """凭证架构提取测试"""

    def test_extract_from_plugin_config(self, sample_plugin_config):
        """测试从插件配置提取凭证架构"""
        service = CredentialService()
        
        result = service.extract_credentials_schema(sample_plugin_config)
        
        assert len(result) == 1
        assert result[0]["name"] == "api_key"

    def test_extract_from_empty_plugin_config(self):
        """测试从空插件配置提取"""
        service = CredentialService()
        
        result = service.extract_credentials_schema({})
        
        assert result == []

    def test_extract_from_none_plugin_config(self):
        """测试从 None 插件配置提取"""
        service = CredentialService()
        
        result = service.extract_credentials_schema(None)
        
        assert result == []

    def test_extract_from_config_without_tools(self):
        """测试从无工具配置的插件配置提取"""
        service = CredentialService()
        config = {"version": "1.0.0", "name": "test"}
        
        result = service.extract_credentials_schema(config)
        
        assert result == []

    def test_extract_from_config_with_empty_tools(self):
        """测试从空工具配置的插件配置提取"""
        service = CredentialService()
        config = {"version": "1.0.0", "tools_configuration": []}
        
        result = service.extract_credentials_schema(config)
        
        assert result == []
