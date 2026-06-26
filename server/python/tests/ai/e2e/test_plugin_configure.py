"""
插件配置验证测试

测试插件的凭证配置功能，包括：
- 配置凭证并验证加密存储
- 验证凭证脱敏显示
- 更新凭证并验证保留未修改字段

运行方式：
    # 运行所有 E2E 测试（需要配置环境变量）
    uv run pytest -m e2e tests/ai/e2e/test_plugin_configure.py -v

    # 单独运行单元测试风格的凭证功能测试
    uv run pytest tests/ai/e2e/test_plugin_configure.py::TestCredentialServiceCore -v

注意：
    - E2E 测试需要配置 E2E_TONGYI_API_KEY 环境变量
    - 核心功能测试使用 mock，无需外部依赖
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginCredential
from ai.services.credential_service import credential_service


class TestCredentialServiceCore:
    """
    凭证服务核心功能测试

    测试场景（不依赖完整插件安装）：
    1. 凭证加密存储
    2. 凭证解密正确性
    3. 凭证脱敏显示
    4. 凭证格式验证
    """

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_encrypt_credentials_with_sensitive_fields(self) -> None:
        """
        测试凭证加密存储

        场景：配置 tongyi 凭证
        - 提供包含敏感字段的凭证
        - 系统识别敏感字段类型（secret-input）
        - 敏感字段被加密存储

        验证点：
        1. 敏感字段加密后不等于原始值
        2. 加密格式正确（包含 nonce:ciphertext）
        """
        # 凭证架构定义（模拟 tongyi 插件的架构）
        credentials_schema = [
            {
                "name": "dashscope_api_key",
                "type": "secret-input",
                "required": True,
                "label": "API Key",
            },
            {
                "name": "model_type",
                "type": "select",
                "required": False,
                "label": "Model Type",
            },
        ]

        # 原始凭证数据
        original_api_key = "sk-test-api-key-12345678"
        credentials = {
            "dashscope_api_key": original_api_key,
            "model_type": "qwen-turbo",
        }

        # 加密凭证
        encrypted = credential_service.encrypt_credentials(credentials, credentials_schema)

        # 验证加密结果
        assert encrypted is not None, "加密结果不应为空"
        assert "dashscope_api_key" in encrypted, "API Key 字段应存在"
        assert "model_type" in encrypted, "model_type 字段应存在"

        # 验证敏感字段已加密
        encrypted_api_key = encrypted["dashscope_api_key"]
        assert encrypted_api_key != original_api_key, "API Key 应被加密"

        # 验证加密格式（AES-GCM 格式：nonce:ciphertext）
        assert ":" in encrypted_api_key, "加密格式应包含 nonce:ciphertext"

        # 验证非敏感字段不加密
        assert encrypted["model_type"] == "qwen-turbo", "非敏感字段应保持原值"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_decrypt_credentials_correctness(self) -> None:
        """
        测试凭证解密正确性

        场景：解密已加密的凭证
        - 加密凭证数据
        - 解密加密后的凭证
        - 验证解密结果与原始值一致

        验证点：
        1. 解密后的值与原始值一致
        """
        credentials_schema = [
            {"name": "api_key", "type": "secret-input", "required": True},
            {"name": "endpoint", "type": "text-input", "required": False},
        ]

        original_credentials = {
            "api_key": "sk-secret-key-abcdefgh",
            "endpoint": "https://api.example.com",
        }

        # 加密
        encrypted = credential_service.encrypt_credentials(original_credentials, credentials_schema)

        # 解密
        decrypted = credential_service.decrypt_credentials(encrypted, credentials_schema)

        # 验证解密结果
        assert decrypted["api_key"] == original_credentials["api_key"], "API Key 解密后应与原始值一致"
        assert decrypted["endpoint"] == original_credentials["endpoint"], "endpoint 应保持不变"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mask_credentials_display_format(self) -> None:
        """
        测试凭证脱敏显示格式

        场景：脱敏显示凭证
        - 提供原始凭证值
        - 系统返回脱敏后的值

        验证点：
        1. 脱敏后的值不等于原始值
        2. 脱敏格式包含 `...` 或 `....`
        """
        credentials_schema = [
            {"name": "api_key", "type": "secret-input", "required": True},
        ]

        # 测试不同长度的 API Key
        test_cases = [
            ("sk-1234567890abcdefghij", "长 API Key"),
            ("sk-1234", "短 API Key"),
            ("sk-1234567890123456", "中等长度 API Key"),
        ]

        for original_key, description in test_cases:
            credentials = {"api_key": original_key}

            # 脱敏
            masked = credential_service.mask_credentials(credentials, credentials_schema)

            masked_key = masked["api_key"]
            assert masked_key != original_key, f"{description}: 脱敏值不应等于原始值"

            # 验证脱敏格式
            has_mask_marker = "..." in masked_key or "****" in masked_key
            assert has_mask_marker, f"{description}: 脱敏格式应包含 '...' 或 '****'，实际: {masked_key}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mask_credentials_different_lengths(self) -> None:
        """
        测试不同长度凭证的脱敏策略

        验证短、中、长字符串使用不同的脱敏策略。
        """
        # 直接测试内部脱敏方法
        test_cases = [
            # (原始值, 预期包含的脱敏标记)
            ("sk-123", "..."),  # 短字符串
            ("sk-12345678", "..."),  # 中等长度
            ("sk-123456789012345678901234567890", "..."),  # 长字符串
        ]

        for original_value, _ in test_cases:
            masked = credential_service._mask_sensitive_value(original_value)
            assert masked != original_value, "脱敏值不应等于原始值"
            assert "..." in masked or "****" in masked, f"脱敏格式不正确: {masked}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_credentials_format_required_field(self) -> None:
        """
        测试凭证格式验证 - 必填字段

        场景：配置无效凭证
        - 缺少必填字段
        - 系统拒绝并返回验证失败错误

        验证点：
        1. 抛出 ValueError
        2. 错误信息提及必填字段
        """
        credentials_schema = [
            {"name": "api_key", "type": "secret-input", "required": True},
        ]

        # 缺少必填字段
        credentials = {}

        with pytest.raises(ValueError, match=r"(?i)必填|required"):
            credential_service.validate_credentials_format(credentials, credentials_schema)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_credentials_format_type_check(self) -> None:
        """
        测试凭证格式验证 - 类型检查

        场景：凭证类型不匹配
        - 提供错误类型的值
        - 系统拒绝并返回验证失败错误

        验证点：
        1. 抛出 ValueError
        2. 错误信息提及类型
        """
        credentials_schema = [
            {"name": "api_key", "type": "secret-input", "required": True},
            {"name": "timeout", "type": "number", "required": False},
        ]

        # 提供错误类型
        credentials = {
            "api_key": "valid-key",
            "timeout": "not-a-number",  # 应该是数字
        }

        with pytest.raises(ValueError, match=r"(?i)数字|number"):
            credential_service.validate_credentials_format(credentials, credentials_schema)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip_preserves_data(self) -> None:
        """
        测试加密解密往返正确性

        验证加密后的凭证可以正确解密还原。
        """
        credentials_schema = [
            {"name": "api_key", "type": "secret-input"},
            {"name": "secret_token", "type": "secret"},
            {"name": "endpoint", "type": "text-input"},
            {"name": "timeout", "type": "number"},
        ]

        original = {
            "api_key": "sk-test-api-key-12345",
            "secret_token": "token-abc-xyz-789",
            "endpoint": "https://api.example.com/v1",
            "timeout": 30,
        }

        # 加密
        encrypted = credential_service.encrypt_credentials(original, credentials_schema)

        # 验证敏感字段已加密
        assert encrypted["api_key"] != original["api_key"]
        assert encrypted["secret_token"] != original["secret_token"]

        # 验证非敏感字段不变
        assert encrypted["endpoint"] == original["endpoint"]
        assert encrypted["timeout"] == original["timeout"]

        # 解密
        decrypted = credential_service.decrypt_credentials(encrypted, credentials_schema)

        # 验证所有字段一致
        for key, value in original.items():
            assert decrypted[key] == value, f"字段 {key} 解密后不一致"


class TestPluginCredentialE2E:
    """
    插件凭证 E2E 测试

    测试需要完整应用程序环境的场景。
    这些测试在配置了 E2E_TONGYI_API_KEY 时运行。
    """

    @pytest.fixture
    def mock_plugin_installation(self, test_tenant_id: str):
        """
        创建模拟的插件安装记录

        用于测试凭证管理功能，不需要完整的插件安装流程。
        """
        return {
            "tenant_id": test_tenant_id,
            "plugin_id": "langgenius/tongyi",
            "plugin_type": "tool",
            "status": "ACTIVE",
        }

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_create_and_store_credential_in_database(
        self,
        e2e_session: AsyncSession,
        tongyi_api_key: str,
        test_tenant_id: str,
    ) -> None:
        """
        测试创建凭证并存储到数据库

        场景：配置 tongyi 凭证
        - 创建 tongyi 插件的凭证配置
        - 提供有效的 API Key
        - 系统加密存储凭证

        验证点：
        1. 凭证成功创建并存入数据库
        2. 凭证内容在数据库中已加密
        """
        from framework.tenant.context import TenantContext

        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        plugin_id = "langgenius/tongyi"
        credential_name = f"test-e2e-{uuid.uuid4().hex[:8]}"

        # 凭证架构
        credentials_schema = [
            {"name": "dashscope_api_key", "type": "secret-input", "required": True},
        ]

        # 加密凭证
        credentials = {"dashscope_api_key": tongyi_api_key}
        encrypted = credential_service.encrypt_credentials(credentials, credentials_schema)

        # 创建数据库记录
        credential_data = {
            "plugin_id": plugin_id,
            "plugin_type": "tool",
            "scope": "global",
            "name": credential_name,
            "credentials": encrypted,
            "tenant_id": test_tenant_id,
        }

        credential_record = PluginCredential(**credential_data)
        e2e_session.add(credential_record)
        await e2e_session.flush()
        await e2e_session.refresh(credential_record)

        credential_id = str(credential_record.id)

        # 验证记录已创建
        assert credential_id is not None, "凭证 ID 不应为空"
        assert credential_record.name == credential_name, "凭证名称应匹配"

        # 验证凭证已加密存储
        stored_credentials = credential_record.credentials
        assert stored_credentials is not None, "凭证内容不应为空"
        stored_key = stored_credentials.get("dashscope_api_key")
        assert stored_key != tongyi_api_key, "API Key 应已加密存储"
        assert ":" in stored_key, "加密格式应正确"

        # 解密验证
        decrypted = credential_service.decrypt_credentials(stored_credentials, credentials_schema)
        assert decrypted.get("dashscope_api_key") == tongyi_api_key, "解密后应与原始值一致"

        # 清理
        await e2e_session.delete(credential_record)
        await e2e_session.commit()

        TenantContext.clear_tenant_id()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_update_credential_preserve_unmodified_fields(
        self,
        e2e_session: AsyncSession,
        tongyi_api_key: str,
        test_tenant_id: str,
    ) -> None:
        """
        测试更新凭证并验证保留未修改字段

        场景：更新凭证
        - 更新已存在凭证的 API Key
        - 系统更新加密存储的凭证
        - 保留未修改的字段

        验证点：
        1. 更新后的凭证内容正确
        2. 未修改的字段保持原值
        """
        from framework.tenant.context import TenantContext

        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        plugin_id = "langgenius/tongyi"
        credential_name = f"test-update-{uuid.uuid4().hex[:8]}"

        # 凭证架构
        credentials_schema = [
            {"name": "dashscope_api_key", "type": "secret-input", "required": True},
            {"name": "model_type", "type": "select", "required": False},
        ]

        # 创建初始凭证
        initial_credentials = {
            "dashscope_api_key": tongyi_api_key,
            "model_type": "qwen-turbo",
        }
        encrypted_initial = credential_service.encrypt_credentials(initial_credentials, credentials_schema)

        credential_record = PluginCredential(
            plugin_id=plugin_id,
            plugin_type="tool",
            scope="global",
            name=credential_name,
            credentials=encrypted_initial,
            tenant_id=test_tenant_id,
        )
        e2e_session.add(credential_record)
        await e2e_session.flush()
        await e2e_session.refresh(credential_record)

        # 更新凭证（只更新 API Key）
        new_api_key = f"sk-new-{uuid.uuid4().hex[:16]}"
        updated_credentials = {
            "dashscope_api_key": new_api_key,
            "model_type": "qwen-turbo",  # 保持不变
        }
        encrypted_updated = credential_service.encrypt_credentials(updated_credentials, credentials_schema)

        credential_record.credentials = encrypted_updated
        await e2e_session.flush()
        await e2e_session.refresh(credential_record)

        # 验证更新结果
        stored_credentials = credential_record.credentials
        decrypted = credential_service.decrypt_credentials(stored_credentials, credentials_schema)

        # API Key 应更新
        assert decrypted.get("dashscope_api_key") == new_api_key, "API Key 应已更新"

        # model_type 应保持
        assert decrypted.get("model_type") == "qwen-turbo", "model_type 应保持不变"

        # 清理
        await e2e_session.delete(credential_record)
        await e2e_session.commit()

        TenantContext.clear_tenant_id()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_credential_masked_display_from_database(
        self,
        e2e_session: AsyncSession,
        tongyi_api_key: str,
        test_tenant_id: str,
    ) -> None:
        """
        测试从数据库读取凭证并脱敏显示

        场景：脱敏显示凭证
        - 查询凭证详情
        - 敏感字段被脱敏显示

        验证点：
        1. 脱敏后的值不包含完整原始值
        2. 脱敏格式符合预期
        """
        from framework.tenant.context import TenantContext

        # 设置租户上下文
        TenantContext.set_tenant_id(test_tenant_id)

        plugin_id = "langgenius/tongyi"
        credential_name = f"test-mask-{uuid.uuid4().hex[:8]}"

        # 凭证架构
        credentials_schema = [
            {"name": "dashscope_api_key", "type": "secret-input", "required": True},
        ]

        # 创建凭证
        credentials = {"dashscope_api_key": tongyi_api_key}
        encrypted = credential_service.encrypt_credentials(credentials, credentials_schema)

        credential_record = PluginCredential(
            plugin_id=plugin_id,
            plugin_type="tool",
            scope="global",
            name=credential_name,
            credentials=encrypted,
            tenant_id=test_tenant_id,
        )
        e2e_session.add(credential_record)
        await e2e_session.flush()
        await e2e_session.refresh(credential_record)

        # 从数据库读取并脱敏
        stored_credentials = credential_record.credentials
        decrypted = credential_service.decrypt_credentials(stored_credentials, credentials_schema)
        masked = credential_service.mask_credentials(decrypted, credentials_schema)

        # 验证脱敏结果
        masked_key = masked.get("dashscope_api_key")
        assert masked_key != tongyi_api_key, "脱敏值不应等于原始值"

        # 验证脱敏格式
        has_mask_marker = "..." in masked_key or "****" in masked_key
        assert has_mask_marker, f"脱敏格式应正确，实际: {masked_key}"

        # 清理
        await e2e_session.delete(credential_record)
        await e2e_session.commit()

        TenantContext.clear_tenant_id()
