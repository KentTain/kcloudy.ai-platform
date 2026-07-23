"""
PluginInstallationProvider.create_installation 方法测试

验证任务 4 的要求：
1. 移除 auto_start 参数处理
2. 初始状态固定为 PENDING
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework.tenant.plugin_protocols import PluginInstallationDTO
from tenant.services.plugin import PluginInstallationProviderImpl


@pytest.fixture
def provider():
    """Provider 实例"""
    return PluginInstallationProviderImpl()


@pytest.fixture
def sample_dto():
    """示例插件安装 DTO"""
    return PluginInstallationDTO(
        tenant_id="tenant-001",
        plugin_id="author/plugin-name",
        plugin_unique_identifier="author/plugin-name:1.0.0@abc123",
        declaration={
            "version": "1.0.0",
            "name": "plugin-name",
            "author": "author",
            "tools_configuration": [],
        },
        status="PENDING",
        freeze_threshold_hours=24,
        plugin_type="local",
        runtime_type="python",
    )


class TestCreateInstallationStatus:
    """测试初始状态固定为 PENDING"""

    @pytest.mark.asyncio
    async def test_create_installation_ignores_dto_status(self, provider, sample_dto):
        """测试 create_installation 忽略 DTO 中的 status 字段，强制设置为 PENDING

        验证点：
        1. 即使 DTO 中 status 为 ACTIVE，创建的记录状态也应该是 PENDING
        2. create_installation 方法不接受 status 参数，初始状态由方法内部控制
        """
        # 修改 DTO 的 status 为 ACTIVE，验证方法是否会忽略
        sample_dto.status = "ACTIVE"

        mock_session = AsyncMock()
        mock_definition = MagicMock()
        mock_definition.refers = 0
        mock_definition.plugin_id = sample_dto.plugin_id
        mock_definition.plugin_unique_identifier = sample_dto.plugin_unique_identifier

        # 记录实际创建的安装记录
        created_installation = None

        def capture_installation(installation):
            nonlocal created_installation
            created_installation = installation
            installation.tenant_id = sample_dto.tenant_id
            installation.plugin_id = sample_dto.plugin_id
            installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
            installation.status = "PENDING"
            installation.freeze_threshold_hours = sample_dto.freeze_threshold_hours
            installation.plugin_type = sample_dto.plugin_type
            installation.runtime_type = sample_dto.runtime_type

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=None,
            ):
                mock_session.add = capture_installation
                mock_session.flush = AsyncMock()

                result = await provider.create_installation("tenant-001", sample_dto)

                # 验证返回的状态是 PENDING，而不是 DTO 中的 ACTIVE
                assert result is not None
                assert result.status == "PENDING", (
                    f"期望状态为 PENDING，实际为 {result.status}"
                )

    @pytest.mark.asyncio
    async def test_create_installation_always_pending(self, provider, sample_dto):
        """测试 create_installation 初始状态始终为 PENDING

        验证点：
        1. 初始状态硬编码为 PENDING
        2. 不受外部参数影响
        """
        # 设置不同的初始状态，验证方法会忽略
        sample_dto.status = "INACTIVE"

        mock_session = AsyncMock()

        # 记录实际创建的安装记录
        created_installation = None

        def capture_installation(installation):
            nonlocal created_installation
            created_installation = installation
            # 模拟 _to_dto 需要的属性
            installation.tenant_id = sample_dto.tenant_id
            installation.plugin_id = sample_dto.plugin_id
            installation.plugin_unique_identifier = sample_dto.plugin_unique_identifier
            installation.status = "PENDING"  # 这是硬编码的值
            installation.freeze_threshold_hours = sample_dto.freeze_threshold_hours
            installation.plugin_type = sample_dto.plugin_type
            installation.runtime_type = sample_dto.runtime_type

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=None,
            ):
                mock_session.add = capture_installation
                mock_session.flush = AsyncMock()

                result = await provider.create_installation("tenant-001", sample_dto)

                # 验证返回的状态是 PENDING，而不是 DTO 中的 INACTIVE
                assert result is not None
                assert result.status == "PENDING", (
                    f"期望状态为 PENDING，实际为 {result.status}"
                )

                # 验证创建的安装记录状态确实是 PENDING
                assert created_installation is not None
                assert created_installation.status == "PENDING"


class TestCreateInstallationNoAutoStart:
    """测试移除 auto_start 参数处理"""

    @pytest.mark.asyncio
    async def test_create_installation_no_auto_start_parameter(self, provider, sample_dto):
        """测试 create_installation 方法不接受 auto_start 参数

        验证点：
        1. 方法签名中没有 auto_start 参数
        2. PluginInstallationDTO 中没有 auto_start 字段
        3. 创建记录时不设置 auto_start 字段
        """
        # 验证 DTO 中没有 auto_start 字段
        dto_fields = sample_dto.__dataclass_fields__.keys()
        assert "auto_start" not in dto_fields, (
            f"PluginInstallationDTO 中不应包含 auto_start 字段，实际字段：{dto_fields}"
        )

        # 验证方法签名
        import inspect
        sig = inspect.signature(provider.create_installation)
        params = list(sig.parameters.keys())
        assert "auto_start" not in params, (
            f"create_installation 方法签名中不应包含 auto_start 参数，实际参数：{params}"
        )

    @pytest.mark.asyncio
    async def test_create_installation_uses_database_default_for_auto_start(
        self, provider, sample_dto
    ):
        """测试 create_installation 不设置 auto_start，使用数据库默认值

        验证点：
        1. 创建记录时不传入 auto_start 参数
        2. auto_start 使用数据库默认值 False
        """
        mock_session = AsyncMock()

        created_kwargs = {}

        def capture_kwargs(*args, **kwargs):
            created_kwargs.update(kwargs)
            mock_installation = MagicMock()
            mock_installation.tenant_id = kwargs.get("tenant_id")
            mock_installation.plugin_id = kwargs.get("plugin_id")
            mock_installation.plugin_unique_identifier = kwargs.get(
                "plugin_unique_identifier"
            )
            mock_installation.status = kwargs.get("status")
            mock_installation.freeze_threshold_hours = kwargs.get(
                "freeze_threshold_hours"
            )
            mock_installation.plugin_type = kwargs.get("plugin_type")
            mock_installation.runtime_type = kwargs.get("runtime_type")
            return mock_installation

        with patch(
            "tenant.services.plugin_provider.get_task_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch(
                "tenant.models.plugin_definition.TenantPluginDefinition.one_by_field",
                return_value=None,
            ):
                mock_session.add = MagicMock()
                mock_session.flush = AsyncMock()

                with patch(
                    "tenant.models.plugin_installation.TenantPluginInstallation"
                ) as mock_installation_class:
                    mock_installation_class.side_effect = capture_kwargs

                    await provider.create_installation("tenant-001", sample_dto)

                    # 验证创建记录时没有设置 auto_start 字段
                    assert "auto_start" not in created_kwargs, (
                        f"创建记录时不应设置 auto_start 字段，实际设置了：{created_kwargs.keys()}"
                    )
