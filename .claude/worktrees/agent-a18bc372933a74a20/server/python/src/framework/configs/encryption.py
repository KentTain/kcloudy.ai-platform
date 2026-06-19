"""
加密配置模块

提供加密相关的配置模型，包括加密实例、落库加密、前端输入加密和前端输出解密配置。
配置模型基于 Pydantic Settings，支持 YAML 配置文件和环境变量覆盖。

示例 YAML 配置：

```yaml
encryption:
  enabled: true
  instance:
    - name: "default"
      algorithm: "aes"
      key: "${ENCRYPTION_KEY}"
  db_in:
    enabled: true
    use: "default"
  web_in:
    enabled: true
    use: "default"
  web_out:
    temp_key_ttl: 300
```
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class EncryptionInstanceSettings(BaseSettings):
    """加密实例配置

    定义单个加密实例的配置，支持 AES 对称加密和 RSA 非对称加密。

    Attributes:
        name: 加密实例名称，用于在配置中引用
        algorithm: 加密算法，可选值：aes（对称加密）、rsa（非对称加密）
        key: 对称加密密钥（AES 算法使用）
        pri_key: 私钥（RSA 算法使用）
        pub_key: 公钥（RSA 算法使用）
    """

    name: str = Field(description="加密实例名称")
    algorithm: str = Field(description="加密算法：aes或rsa")
    key: str | None = Field(default=None, description="对称加密密钥")
    pri_key: str | None = Field(default=None, description="私钥")
    pub_key: str | None = Field(default=None, description="公钥")


class EncryptionDbInSettings(BaseSettings):
    """落库加密配置

    控制数据落库时的加密行为，确保敏感数据在数据库中加密存储。

    Attributes:
        enabled: 是否启用落库加密
        use: 使用的加密实例名称，对应 EncryptionInstanceSettings.name
    """

    enabled: bool = Field(default=True, description="是否启用落库加密")
    use: str = Field(default="", description="使用的加密实例名称")


class EncryptionWebInSettings(BaseSettings):
    """前端输入加密配置

    控制前端传输数据的加密行为，保护数据传输安全。

    Attributes:
        enabled: 是否启用前端输入加密
        use: 使用的加密实例名称，对应 EncryptionInstanceSettings.name
    """

    enabled: bool = Field(default=True, description="是否启用前端输入加密")
    use: str = Field(default="", description="使用的加密实例名称")


class EncryptionWebOutSettings(BaseSettings):
    """前端输出解密配置

    控制数据返回前端时的解密行为，配合前端加密使用。

    Attributes:
        temp_key_ttl: 临时密钥生存时间（秒），用于前端加密密钥的有效期控制
    """

    temp_key_ttl: int = Field(default=300, description="临时密钥生存时间（秒）")


class EncryptionSettings(BaseSettings):
    """加密配置

    加密功能的顶层配置，管理加密实例和各类加密场景的配置。

    Attributes:
        enabled: 是否启用加密功能
        instance: 加密实例列表，定义可用的加密配置
        db_in: 落库加密配置
        web_in: 前端输入加密配置
        web_out: 前端输出解密配置
    """

    enabled: bool = Field(default=True, description="是否启用加密功能")
    instance: list[EncryptionInstanceSettings] = Field(
        default_factory=list, description="加密实例列表"
    )
    db_in: EncryptionDbInSettings = Field(
        default_factory=EncryptionDbInSettings, description="落库加密配置"
    )
    web_in: EncryptionWebInSettings = Field(
        default_factory=EncryptionWebInSettings, description="前端输入加密配置"
    )
    web_out: EncryptionWebOutSettings = Field(
        default_factory=EncryptionWebOutSettings, description="前端输出解密配置"
    )
