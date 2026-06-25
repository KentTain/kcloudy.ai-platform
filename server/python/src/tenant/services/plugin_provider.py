"""
插件安装提供者实现

PluginInstallationProvider 协议在 Tenant 模块的具体实现。
AI 模块通过此实现访问 Tenant 侧的安装记录，不直接访问 Tenant Schema。
"""

from collections.abc import Sequence

from loguru import logger

from framework.database.dependencies import get_task_session
from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    PluginInstallationProvider,
)
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)


class PluginInstallationProviderImpl(PluginInstallationProvider):
    """
    插件安装提供者实现

    本地部署时直接访问数据库，提供插件安装记录的 CRUD 操作。
    每个方法使用独立的 Session 管理事务。
    """

    async def get_tenant_installations(
        self, tenant_id: str
    ) -> list[PluginInstallationDTO]:
        """
        获取租户的所有插件安装记录

        Args:
            tenant_id: 租户 ID

        Returns:
            list[PluginInstallationDTO]
        """
        async with get_task_session() as session:
            installations = await TenantPluginInstallation.all_by_field(
                session, "tenant_id", tenant_id
            )
            return self._to_dto_list(installations)

    async def get_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO | None:
        """
        获取指定插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO | None
        """
        async with get_task_session() as session:
            installation = await TenantPluginInstallation.first_by_fields(
                session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
            )
            if not installation:
                return None
            return self._to_dto(installation)

    async def create_installation(
        self, tenant_id: str, data: PluginInstallationDTO
    ) -> PluginInstallationDTO:
        """
        创建插件安装记录

        Args:
            tenant_id: 租户 ID
            data: 安装记录 DTO

        Returns:
            PluginInstallationDTO
        """
        async with get_task_session() as session:
            # 确保插件定义已存在
            await self._ensure_plugin_definition(session, data)

            # 创建安装记录，初始状态 PENDING
            installation = TenantPluginInstallation(
                tenant_id=tenant_id,
                plugin_id=data.plugin_id,
                plugin_unique_identifier=data.plugin_unique_identifier,
                status="PENDING",
                auto_start=data.auto_start,
                freeze_threshold_hours=data.freeze_threshold_hours,
                plugin_type=data.plugin_type,
                runtime_type=data.runtime_type,
            )
            session.add(installation)
            await session.flush()

            return self._to_dto(installation)

    async def update_installation(
        self, tenant_id: str, plugin_id: str, data: dict
    ) -> PluginInstallationDTO:
        """
        更新插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            data: 更新字段字典

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在
        """
        async with get_task_session() as session:
            installation = await TenantPluginInstallation.first_by_fields(
                session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
            )
            if not installation:
                raise ValueError(
                    f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}"
                )

            await installation.update(session, data)
            return self._to_dto(installation)

    async def delete_installation(
        self, tenant_id: str, plugin_id: str
    ) -> None:
        """
        删除插件安装记录

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Raises:
            ValueError: 安装记录不存在
        """
        async with get_task_session() as session:
            installation = await TenantPluginInstallation.first_by_fields(
                session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
            )
            if not installation:
                raise ValueError(
                    f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}"
                )

            await installation.delete(session)

    async def _ensure_plugin_definition(
        self,
        session,
        data: PluginInstallationDTO,
    ) -> TenantPluginDefinition:
        """
        确保插件定义存在

        根据 data.plugin_unique_identifier 查询 TenantPluginDefinition：
        - 如果存在：refers += 1
        - 如果不存在：创建新定义，refers = 1

        Args:
            session: 数据库会话
            data: 安装记录 DTO（包含 declaration）

        Returns:
            TenantPluginDefinition

        Raises:
            ValueError: 插件定义不存在且未提供 declaration
        """
        definition = await TenantPluginDefinition.one_by_field(
            session, "plugin_unique_identifier", data.plugin_unique_identifier
        )

        if definition:
            # 引用计数递增
            definition.refers += 1
            await session.flush()
            _logger.info(
                f"插件定义引用递增: {data.plugin_unique_identifier}, "
                f"当前引用: {definition.refers}"
            )
        else:
            # 使用 DTO 中的 declaration 创建新定义
            if not data.declaration:
                raise ValueError(
                    f"插件定义不存在且未提供 declaration: {data.plugin_unique_identifier}"
                )

            definition = TenantPluginDefinition(
                plugin_id=data.plugin_id,
                plugin_unique_identifier=data.plugin_unique_identifier,
                declaration=data.declaration,  # 从 DTO 获取 declaration
                install_type=data.plugin_type or "local",
                refers=1,
            )
            session.add(definition)
            await session.flush()
            _logger.info(
                f"创建插件定义: {data.plugin_unique_identifier}, "
                f"install_type={data.plugin_type or 'local'}"
            )

        return definition

    def _to_dto(
        self, installation: TenantPluginInstallation
    ) -> PluginInstallationDTO:
        """
        将 ORM 模型转换为 PluginInstallationDTO

        Args:
            installation: 安装记录 ORM 模型

        Returns:
            PluginInstallationDTO

        注意:
            declaration 字段存储在 plugin_definitions 表中，
            不在 plugin_installations 表中。
            如果需要返回 declaration，需要单独查询。
        """
        return PluginInstallationDTO(
            tenant_id=installation.tenant_id,
            plugin_id=installation.plugin_id,
            plugin_unique_identifier=installation.plugin_unique_identifier,
            declaration={},  # 注意：installation 对象不包含 declaration，需要单独查询
            status=installation.status,
            auto_start=installation.auto_start,
            freeze_threshold_hours=installation.freeze_threshold_hours,
            plugin_type=installation.plugin_type,
            runtime_type=installation.runtime_type,
        )

    def _to_dto_list(
        self,
        installations: Sequence[TenantPluginInstallation],
    ) -> list[PluginInstallationDTO]:
        """
        将 ORM 模型列表转换为 PluginInstallationDTO 列表

        Args:
            installations: 安装记录 ORM 模型列表

        Returns:
            list[PluginInstallationDTO]
        """
        return [self._to_dto(inst) for inst in installations]


# 单例实例
plugin_installation_provider_impl = PluginInstallationProviderImpl()
