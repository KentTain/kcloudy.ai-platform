"""Encryption 组件测试"""

import pytest

from ai.components.encryption import (
    BaseEncryption,
    DecryptionError,
    EncryptionAlgorithmError,
    EncryptionConfigError,
    EncryptionError,
    EncryptionKeyError,
)
from ai.components.encryption.helpers import (
    generate_aes_key,
    generate_encryption_config_template,
    generate_rsa_key_pair,
)
from ai.components.encryption.impl.aes import AESEncryption, RSAEncryption


class TestAESEncryption:
    """测试 AES 加密"""

    def test_aes_encrypt_decrypt_string(self):
        """测试 AES 字符串加密解密"""
        key = "test-key-12345678"
        aes = AESEncryption(key)

        original_data = "Hello, World!"
        encrypted = aes.encrypt(original_data)
        decrypted = aes.decrypt(encrypted)

        assert decrypted == original_data
        assert encrypted != original_data
        assert isinstance(encrypted, str)

    def test_aes_encrypt_decrypt_bytes(self):
        """测试 AES 字节数据加密解密"""
        key = "test-key-12345678"
        aes = AESEncryption(key)

        original_data = b"Binary data test"
        encrypted = aes.encrypt(original_data)
        decrypted = aes.decrypt(encrypted)

        assert decrypted == original_data.decode("utf-8")

    def test_aes_encrypt_empty_string(self):
        """测试 AES 空字符串加密"""
        key = "test-key-12345678"
        aes = AESEncryption(key)

        original_data = ""
        encrypted = aes.encrypt(original_data)
        decrypted = aes.decrypt(encrypted)

        assert decrypted == original_data

    def test_aes_encrypt_chinese(self):
        """测试 AES 中文加密"""
        key = "test-key-中文密钥"
        aes = AESEncryption(key)

        original_data = "你好，世界！这是一段中文测试。"
        encrypted = aes.encrypt(original_data)
        decrypted = aes.decrypt(encrypted)

        assert decrypted == original_data

    def test_aes_different_keys_produce_different_results(self):
        """测试不同密钥产生不同加密结果"""
        aes1 = AESEncryption("key1-1234567890")
        aes2 = AESEncryption("key2-1234567890")

        data = "Same data"
        encrypted1 = aes1.encrypt(data)
        encrypted2 = aes2.encrypt(data)

        assert encrypted1 != encrypted2

    def test_aes_same_key_same_data_different_encryption(self):
        """测试相同密钥和数据的每次加密结果不同（因为随机IV）"""
        aes = AESEncryption("same-key-123456")
        data = "Same data"

        encrypted1 = aes.encrypt(data)
        encrypted2 = aes.encrypt(data)

        # 由于随机 IV，相同数据和密钥的加密结果应该不同
        assert encrypted1 != encrypted2
        # 但两者都应该能正确解密
        assert aes.decrypt(encrypted1) == data
        assert aes.decrypt(encrypted2) == data

    def test_aes_invalid_key_empty(self):
        """测试 AES 空密钥抛出异常"""
        with pytest.raises(EncryptionKeyError):
            AESEncryption("")

    def test_aes_decrypt_invalid_data(self):
        """测试 AES 解密无效数据"""
        aes = AESEncryption("valid-key-123456")

        with pytest.raises(DecryptionError):
            aes.decrypt("invalid-base64-encrypted-data")

    def test_aes_decrypt_wrong_key(self):
        """测试 AES 使用错误密钥解密"""
        aes1 = AESEncryption("correct-key-12345")
        aes2 = AESEncryption("wrong-key-123456")

        data = "Secret message"
        encrypted = aes1.encrypt(data)

        with pytest.raises(DecryptionError):
            aes2.decrypt(encrypted)


class TestRSAEncryption:
    """测试 RSA 加密"""

    def test_rsa_encrypt_decrypt(self):
        """测试 RSA 加密解密"""
        private_key, public_key = generate_rsa_key_pair()
        rsa = RSAEncryption(private_key=private_key, public_key=public_key)

        original_data = "Hello, RSA!"
        encrypted = rsa.encrypt(original_data)
        decrypted = rsa.decrypt(encrypted)

        assert decrypted == original_data

    def test_rsa_encrypt_without_public_key(self):
        """测试 RSA 无公钥加密抛出异常"""
        private_key, _ = generate_rsa_key_pair()
        rsa = RSAEncryption(private_key=private_key)

        with pytest.raises(EncryptionKeyError) as exc_info:
            rsa.encrypt("test data")

        assert "需要公钥" in str(exc_info.value)

    def test_rsa_decrypt_without_private_key(self):
        """测试 RSA 无私钥解密抛出异常"""
        _, public_key = generate_rsa_key_pair()
        rsa = RSAEncryption(public_key=public_key)

        with pytest.raises(EncryptionKeyError) as exc_info:
            rsa.decrypt("some-encrypted-data")

        assert "需要私钥" in str(exc_info.value)

    def test_rsa_long_data_encryption(self):
        """测试 RSA 长数据加密（分块处理）"""
        private_key, public_key = generate_rsa_key_pair()
        rsa = RSAEncryption(private_key=private_key, public_key=public_key)

        # 生成超过 RSA 块大小的数据
        original_data = "A" * 500
        encrypted = rsa.encrypt(original_data)
        decrypted = rsa.decrypt(encrypted)

        assert decrypted == original_data

    def test_rsa_generate_key_pair(self):
        """测试 RSA 密钥对生成"""
        private_key, public_key = RSAEncryption.generate_key_pair()

        assert private_key.startswith("-----BEGIN RSA PRIVATE KEY-----")
        assert public_key.startswith("-----BEGIN PUBLIC KEY-----")

    def test_rsa_invalid_private_key(self):
        """测试无效 RSA 私钥"""
        with pytest.raises(EncryptionKeyError):
            RSAEncryption(private_key="invalid-private-key")

    def test_rsa_invalid_public_key(self):
        """测试无效 RSA 公钥"""
        with pytest.raises(EncryptionKeyError):
            RSAEncryption(public_key="invalid-public-key")


class TestHelpers:
    """测试辅助函数"""

    def test_generate_aes_key_default_length(self):
        """测试默认长度 AES 密钥生成"""
        key = generate_aes_key()
        assert len(key) == 32

    def test_generate_aes_key_custom_length(self):
        """测试自定义长度 AES 密钥生成"""
        key = generate_aes_key(16)
        assert len(key) == 16

        key = generate_aes_key(64)
        assert len(key) == 64

    def test_generate_aes_key_randomness(self):
        """测试 AES 密钥随机性"""
        key1 = generate_aes_key()
        key2 = generate_aes_key()

        assert key1 != key2

    def test_generate_rsa_key_pair(self):
        """测试 RSA 密钥对生成"""
        private_key, public_key = generate_rsa_key_pair()

        assert isinstance(private_key, str)
        assert isinstance(public_key, str)
        assert len(private_key) > 0
        assert len(public_key) > 0

    def test_generate_encryption_config_template(self):
        """测试加密配置模板生成"""
        config = generate_encryption_config_template()

        assert "encryption" in config
        assert config["encryption"]["enabled"] is True
        assert "instance" in config["encryption"]
        assert len(config["encryption"]["instance"]) == 2

        # 验证 AES 实例配置
        aes_instance = config["encryption"]["instance"][0]
        assert aes_instance["algorithm"] == "aes"
        assert "key" in aes_instance

        # 验证 RSA 实例配置
        rsa_instance = config["encryption"]["instance"][1]
        assert rsa_instance["algorithm"] == "rsa"
        assert "pri-key" in rsa_instance
        assert "pub-key" in rsa_instance


class TestExceptions:
    """测试异常类"""

    def test_encryption_error(self):
        """测试基础加密异常"""
        with pytest.raises(EncryptionError):
            raise EncryptionError("Test error")

    def test_encryption_key_error(self):
        """测试密钥异常"""
        with pytest.raises(EncryptionKeyError):
            raise EncryptionKeyError("Invalid key")

    def test_encryption_algorithm_error(self):
        """测试算法异常"""
        with pytest.raises(EncryptionAlgorithmError):
            raise EncryptionAlgorithmError("Algorithm failed")

    def test_decryption_error(self):
        """测试解密异常"""
        with pytest.raises(DecryptionError):
            raise DecryptionError("Decryption failed")

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        assert issubclass(EncryptionKeyError, EncryptionError)
        assert issubclass(EncryptionAlgorithmError, EncryptionError)
        assert issubclass(DecryptionError, EncryptionError)
        assert issubclass(EncryptionConfigError, EncryptionError)


class TestBaseEncryption:
    """测试基类"""

    def test_base_encryption_is_abstract(self):
        """测试 BaseEncryption 是抽象类"""
        with pytest.raises(TypeError):
            BaseEncryption()

    def test_base_encryption_methods(self):
        """测试 BaseEncryption 方法定义"""
        assert hasattr(BaseEncryption, "encrypt")
        assert hasattr(BaseEncryption, "decrypt")

    def test_aes_implements_base_encryption(self):
        """测试 AESEncryption 实现了 BaseEncryption"""
        assert issubclass(AESEncryption, BaseEncryption)

    def test_rsa_implements_base_encryption(self):
        """测试 RSAEncryption 实现了 BaseEncryption"""
        assert issubclass(RSAEncryption, BaseEncryption)
