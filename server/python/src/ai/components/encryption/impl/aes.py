"""加密算法实现"""

import base64
import hashlib

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from ai.components.encryption.exceptions import (
    DecryptionError,
    EncryptionAlgorithmError,
    EncryptionKeyError,
)
from ai.components.encryption.interfaces import BaseEncryption


class AESEncryption(BaseEncryption):
    """AES加密算法实现"""

    def __init__(self, key: str):
        """
        初始化AES加密

        Args:
            key: 加密密钥，长度必须是16、24或32字节
        """
        if not key:
            raise EncryptionKeyError("AES密钥不能为空")

        # 确保密钥长度为32字节（256位）
        self.key = self._normalize_key(key)

    def _normalize_key(self, key: str) -> bytes:
        """标准化密钥长度"""
        key_bytes = key.encode("utf-8")

        # 使用SHA256哈希确保密钥长度为32字节
        return hashlib.sha256(key_bytes).digest()

    def encrypt(self, data: str | bytes) -> str:
        """
        AES加密

        Args:
            data: 要加密的数据

        Returns:
            Base64编码的加密数据
        """
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            # 生成随机IV
            iv = get_random_bytes(AES.block_size)

            # 创建AES加密器
            cipher = AES.new(self.key, AES.MODE_CBC, iv)

            # 填充数据并加密
            padded_data = pad(data, AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)

            # 将IV和加密数据组合并进行Base64编码
            result = base64.b64encode(iv + encrypted_data).decode("utf-8")
            return result

        except Exception as e:
            raise EncryptionAlgorithmError(f"AES加密失败: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        AES解密

        Args:
            encrypted_data: Base64编码的加密数据

        Returns:
            解密后的原始数据
        """
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

            # 提取IV和加密数据
            iv = encrypted_bytes[: AES.block_size]
            encrypted_content = encrypted_bytes[AES.block_size :]

            # 创建AES解密器
            cipher = AES.new(self.key, AES.MODE_CBC, iv)

            # 解密并去除填充
            decrypted_data = cipher.decrypt(encrypted_content)
            unpadded_data = unpad(decrypted_data, AES.block_size)

            return unpadded_data.decode("utf-8")

        except Exception as e:
            raise DecryptionError(f"AES解密失败: {str(e)}")


class RSAEncryption(BaseEncryption):
    """RSA加密算法实现"""

    def __init__(self, private_key: str | None = None, public_key: str | None = None):
        """
        初始化RSA加密

        Args:
            private_key: 私钥（用于解密）
            public_key: 公钥（用于加密）
        """
        self.private_key = None
        self.public_key = None

        if private_key:
            try:
                self.private_key = RSA.import_key(private_key)
            except Exception as e:
                raise EncryptionKeyError(f"无效的RSA私钥: {str(e)}")

        if public_key:
            try:
                self.public_key = RSA.import_key(public_key)
            except Exception as e:
                raise EncryptionKeyError(f"无效的RSA公钥: {str(e)}")

    def encrypt(self, data: str | bytes) -> str:
        """
        RSA加密（使用公钥）

        Args:
            data: 要加密的数据

        Returns:
            Base64编码的加密数据
        """
        if not self.public_key:
            raise EncryptionKeyError("RSA加密需要公钥")

        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            # 创建RSA加密器
            cipher = PKCS1_v1_5.new(self.public_key)

            # RSA加密有长度限制，需要分块处理
            max_length = self.public_key.size_in_bytes() - 11  # PKCS1填充需要11字节
            encrypted_chunks = []

            for i in range(0, len(data), max_length):
                chunk = data[i : i + max_length]
                encrypted_chunk = cipher.encrypt(chunk)
                encrypted_chunks.append(encrypted_chunk)

            # 合并所有加密块并进行Base64编码
            encrypted_data = b"".join(encrypted_chunks)
            return base64.b64encode(encrypted_data).decode("utf-8")

        except Exception as e:
            raise EncryptionAlgorithmError(f"RSA加密失败: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        RSA解密（使用私钥）

        Args:
            encrypted_data: Base64编码的加密数据

        Returns:
            解密后的原始数据
        """
        if not self.private_key:
            raise EncryptionKeyError("RSA解密需要私钥")

        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

            # 创建RSA解密器
            cipher = PKCS1_v1_5.new(self.private_key)

            # 分块解密
            block_size = self.private_key.size_in_bytes()
            decrypted_chunks = []

            for i in range(0, len(encrypted_bytes), block_size):
                chunk = encrypted_bytes[i : i + block_size]
                decrypted_chunk = cipher.decrypt(chunk, None)
                if decrypted_chunk is None:
                    raise DecryptionError("RSA解密失败：无效的加密数据")
                decrypted_chunks.append(decrypted_chunk)

            # 合并所有解密块
            decrypted_data = b"".join(decrypted_chunks)
            return decrypted_data.decode("utf-8")

        except Exception as e:
            raise DecryptionError(f"RSA解密失败: {str(e)}")

    @classmethod
    def generate_key_pair(cls, key_size: int = 2048) -> tuple[str, str]:
        """
        生成RSA密钥对

        Args:
            key_size: 密钥长度，默认2048位

        Returns:
            (私钥, 公钥) 元组
        """
        try:
            key = RSA.generate(key_size)
            private_key = key.export_key().decode("utf-8")
            public_key = key.publickey().export_key().decode("utf-8")
            return private_key, public_key
        except Exception as e:
            raise EncryptionKeyError(f"生成RSA密钥对失败: {str(e)}")
