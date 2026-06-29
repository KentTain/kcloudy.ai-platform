"""
插件管理服务层

负责封装 plugin_manager 的调用逻辑，提供高级业务接口。
适配 framework 基础设施：crypto, storage, ctx。
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ai.models.plugin import (
    CredentialScope,
    PluginCredential,
    PluginStatus,
    PluginType,
)
from ai.models.plugin_config import PluginConfig as AIPluginConfig
from ai.models.plugin_runtime_state import PluginRuntimeState
from ai.schemas.plugin import (
    AvailablePluginListResponse,
    AvailablePluginVo,
    CreatePluginCredential,
    PluginConfigResponse,
    PluginCredentialVo,
    PluginInfoVo,
    PluginInstallResponseVo,
    PluginOperationResponseVo,
    PluginPaginatedListResponseVo,
    PluginRuntimeStats,
    PluginStatusStats,
    PluginUsageStatisticsResponse,
    PluginUsageStats,
    RuntimeStateItem,
    RuntimeStateListResponse,
    RuntimeStateResponse,
    StartPluginResponse,
    StopPluginResponse,
    UpdatePluginConfigRequest,
    UpdatePluginCredential,
)
from ai.services.credential_service import credential_service
from framework.common.ctx import get_tenant_id, get_user_id
from framework.common.exceptions import BadRequestError
from framework.database.dependencies import get_task_session
from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    get_plugin_installation_provider,
)
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation

_logger = logger.bind(name=__name__)


class PluginManagementService:
    """插件管理服务

    提供插件生命周期管理、凭证管理等功能。
    """

    # ==================== 插件列表与详情 ====================

    async def get_plugin_list(
        self,
        session: AsyncSession,
        status: str | None = None,
        plugin_id: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PluginPaginatedListResponseVo:
        """获取插件列表"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        _logger.info(
            f"获取插件列表: tenant_id={tenant_id}, status={status}, "
            f"plugin_id={plugin_id}, plugin_type={plugin_type}, page={page}, page_size={page_size}"
        )

        # 1. 从 Provider 获取租户的插件安装记录
        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(tenant_id)

        # 2. 获取 AI 侧配置
        plugin_ids = [inst.plugin_id for inst in installations]
        if not plugin_ids:
            return PluginPaginatedListResponseVo(plugins=[], total=0)

        result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id.in_(plugin_ids),
            )
        )
        ai_configs = {cfg.plugin_id: cfg for cfg in result.scalars().all()}

        # 3. 获取 AI 侧运行时状态
        runtime_result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id.in_(plugin_ids),
            )
        )
        runtime_states = {st.plugin_id: st for st in runtime_result.scalars().all()}

        # 4. 组装数据并过滤
        combined_data = []
        for inst in installations:
            # 过滤条件
            if status and inst.status != status:
                continue
            if plugin_id and plugin_id.lower() not in inst.plugin_id.lower():
                continue
            if plugin_type and inst.plugin_type != plugin_type:
                continue

            ai_config = ai_configs.get(inst.plugin_id)
            runtime_state = runtime_states.get(inst.plugin_id)
            combined_data.append((inst, ai_config, runtime_state))

        # 5. 排序和分页
        total = len(combined_data)
        offset = (page - 1) * page_size
        paged_data = combined_data[offset : offset + page_size]

        # 6. 转换为 VO
        plugin_vos = []
        for inst, ai_config, runtime_state in paged_data:
            plugin_vo = await self._convert_combined_data_to_vo(
                inst, ai_config, runtime_state
            )
            plugin_vos.append(plugin_vo)

        return PluginPaginatedListResponseVo(plugins=plugin_vos, total=total)

    async def get_available_plugins(
        self,
        session: AsyncSession,
        keyword: str | None = None,
        type: str | None = None,
        is_recommended: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AvailablePluginListResponse:
        """
        获取可用插件列表

        从 Tenant 模块获取已注册且启用的插件定义列表，
        并标记每个插件是否已安装。

        Args:
            session: 数据库会话
            keyword: 关键词搜索
            type: 插件类型筛选
            is_recommended: 是否推荐筛选
            page: 页码
            page_size: 每页条数

        Returns:
            AvailablePluginListResponse: 可用插件列表响应
        """
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        _logger.info(
            f"获取可用插件列表: tenant_id={tenant_id}, keyword={keyword}, "
            f"type={type}, is_recommended={is_recommended}"
        )

        # 1. 查询租户已安装的插件
        installed_plugins_stmt = select(TenantPluginInstallation.plugin_id).where(
            TenantPluginInstallation.tenant_id == tenant_id
        )
        installed_result = await session.execute(installed_plugins_stmt)
        installed_plugin_ids = set(row[0] for row in installed_result.fetchall())

        # 2. 查询安装状态
        installation_status_map: dict[str, str] = {}
        if installed_plugin_ids:
            status_stmt = select(
                TenantPluginInstallation.plugin_id,
                TenantPluginInstallation.status,
            ).where(
                TenantPluginInstallation.tenant_id == tenant_id,
                TenantPluginInstallation.plugin_id.in_(installed_plugin_ids),
            )
            status_result = await session.execute(status_stmt)
            for row in status_result.fetchall():
                installation_status_map[row[0]] = row[1]

        # 3. 构建查询条件
        conditions = [TenantPluginDefinition.is_enabled == True]

        if keyword:
            conditions.append(
                TenantPluginDefinition.plugin_id.ilike(f"%{keyword}%")
            )

        # 4. 查询总数
        count_stmt = select(func.count(TenantPluginDefinition.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 5. 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(TenantPluginDefinition)
            .where(*conditions)
            .order_by(TenantPluginDefinition.refers.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        definitions = list(result.scalars().all())

        # 6. 转换为 VO
        items = []
        for definition in definitions:
            # 从 declaration 中提取插件信息
            declaration = definition.declaration or {}
            configuration = declaration.get("configuration", {})

            # 获取插件类型
            plugin_type = self._extract_plugin_type(declaration)

            # 应用类型筛选
            if type and plugin_type != type:
                continue

            # 应用推荐筛选
            if is_recommended is not None and definition.is_recommended != is_recommended:
                continue

            is_installed = definition.plugin_id in installed_plugin_ids
            installation_status = installation_status_map.get(definition.plugin_id)

            items.append(AvailablePluginVo(
                plugin_id=definition.plugin_id,
                plugin_unique_identifier=definition.plugin_unique_identifier,
                name=configuration.get("label", {}).get("zh_Hans")
                or configuration.get("label", {}).get("en_US")
                or definition.plugin_id.split("/")[-1],
                author=configuration.get("author", definition.plugin_id.split("/")[0] if "/" in definition.plugin_id else "unknown"),
                version=configuration.get("version", ""),
                description=configuration.get("description", {}).get("zh_Hans", "")
                or configuration.get("description", {}).get("en_US", ""),
                icon=configuration.get("icon"),
                plugin_type=plugin_type,
                runtime_type="local",  # 默认本地运行
                is_installed=is_installed,
                installation_status=installation_status,
                is_recommended=definition.is_recommended,
                is_enabled=definition.is_enabled,
                created_at=definition.created_at,
                updated_at=definition.updated_at,
            ))

        return AvailablePluginListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def _extract_plugin_type(self, declaration: dict) -> str:
        """从声明中提取插件类型"""
        if declaration.get("tools_configuration"):
            return "tool"
        if declaration.get("models_configuration"):
            return "model"
        if declaration.get("agent_strategies_configuration"):
            return "agent"
        return "unknown"

    async def get_plugin_info(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> PluginInfoVo:
        """获取插件详细信息"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 1. 从 Provider 获取安装记录
        provider = get_plugin_installation_provider()
        installation_dto = await provider.get_installation(tenant_id, plugin_id)

        if not installation_dto:
            raise ValueError(f"插件不存在: {plugin_id}")

        # 2. 查询 AI 侧配置
        result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = result.scalar_one_or_none()

        # 3. 查询 AI 侧运行时状态
        runtime_result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id == plugin_id,
            )
        )
        runtime_state = runtime_result.scalar_one_or_none()

        return await self._convert_combined_data_to_vo(
            installation_dto, ai_config, runtime_state
        )

    # ======================= 凭证管理 =======================

    async def get_plugin_credentials_schema(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> list[dict[str, Any]]:
        """查询插件的凭证架构"""
        # 查询 AI 侧配置
        result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = result.scalar_one_or_none()

        if not ai_config or not ai_config.plugin_config:
            return []

        return credential_service.extract_credentials_schema(ai_config.plugin_config)

    async def list_credentials(
        self,
        session: AsyncSession,
        plugin_id: str,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
    ) -> tuple[int, list[PluginCredentialVo]]:
        """获取凭证列表"""
        fields = {"plugin_id": plugin_id}
        fuzzy = {"name": name} if name else None
        items, pagination = await PluginCredential.paginated_by_query(
            session=session,
            fields=fields,
            fuzzy_fields=fuzzy,
            page=page,
            page_size=page_size,
            order_by=[("created_at", "desc")],
        )

        return pagination.total, [self._to_credential_vo(i) for i in items]

    async def get_credential(
        self,
        session: AsyncSession,
        credential_id: str,
    ) -> PluginCredentialVo:
        """获取凭证详情"""
        tenant_id = get_tenant_id()
        record = await PluginCredential.one_by_id(session, credential_id)
        if not record:
            raise ValueError("凭证不存在")

        # 读取安装记录（通过 Provider）与 schema
        provider = get_plugin_installation_provider()
        installation_dto = await provider.get_installation(tenant_id, record.plugin_id)

        # 提取凭证架构
        credentials_schema = []
        if installation_dto:
            # 获取 AI 侧配置
            ai_config_result = await session.execute(
                select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == tenant_id,
                    AIPluginConfig.plugin_id == record.plugin_id,
                )
            )
            ai_config = ai_config_result.scalar_one_or_none()
            if ai_config and ai_config.plugin_config:
                credentials_schema = credential_service.extract_credentials_schema(
                    ai_config.plugin_config
                )

        # 解密并脱敏
        decrypted = record.credentials or {}
        if credentials_schema:
            decrypted = credential_service.decrypt_credentials(
                record.credentials or {},
                credentials_schema,
            )

        masked = credential_service.mask_credentials(decrypted, credentials_schema)

        vo = self._to_credential_vo(record)
        vo.credentials = masked
        return vo

    async def create_credential(
        self,
        session: AsyncSession,
        plugin_id: str,
        obj_in: CreatePluginCredential,
    ) -> PluginCredentialVo:
        """创建凭证（含格式校验、插件校验、加密入库）"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        name = obj_in.name
        credentials = obj_in.credentials
        if not name or not isinstance(credentials, dict):
            raise ValueError("name 和 credentials 为必填")

        user_id = get_user_id() or ""

        # 使用 Provider 验证插件存在
        provider = get_plugin_installation_provider()
        installation_dto = await provider.get_installation(tenant_id, plugin_id)
        if installation_dto is None:
            raise ValueError(f"插件不存在: {plugin_id}")

        # 获取 AI 侧配置用于凭证架构
        ai_config_result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = ai_config_result.scalar_one_or_none()

        # 检查凭证名称是否已存在
        existing_credential_stmt = select(PluginCredential).where(
            and_(
                PluginCredential.plugin_id == plugin_id,
                PluginCredential.name == name,
            ),
        )
        existing_credential = (
            await session.execute(existing_credential_stmt)
        ).scalar_one_or_none()
        if existing_credential:
            raise BadRequestError(f"凭证名称 '{name}' 已存在，请使用其他名称")

        # 凭证架构
        credentials_schema = []
        plugin_config_dict = None
        if ai_config and ai_config.plugin_config:
            plugin_config_dict = ai_config.plugin_config
            credentials_schema = credential_service.extract_credentials_schema(
                plugin_config_dict
            )

        # 1) 格式校验
        credential_service.validate_credentials_format(credentials, credentials_schema)

        # 2) 加密
        encrypted = credential_service.encrypt_credentials(
            credentials, credentials_schema
        )

        # 默认 provider_name 取第一个 tools_configuration
        provider_name = None
        try:
            if plugin_config_dict and plugin_config_dict.get("tools_configuration"):
                tools_config = plugin_config_dict["tools_configuration"]
                if tools_config and len(tools_config) > 0:
                    first_tool = tools_config[0]
                    identity = first_tool.get("identity", {})
                    provider_name = identity.get("name", "")
                    if provider_name:
                        provider_name = f"{plugin_id}/{provider_name}"
        except Exception:
            pass

        data = {
            "plugin_id": plugin_id,
            "plugin_type": installation_dto.plugin_type,
            "scope": CredentialScope.GLOBAL,
            "name": name,
            "provider_name": provider_name,
            "credentials": encrypted,
            "tenant_id": tenant_id,
            "created_by": user_id,
        }

        record = await PluginCredential.create(session, data)
        await session.flush()
        return self._to_credential_vo(record)

    async def update_credential(
        self,
        session: AsyncSession,
        plugin_id: str,
        credential_id: str,
        obj_in: UpdatePluginCredential,
    ) -> PluginCredentialVo:
        """更新凭证"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        record = await PluginCredential.one_by_id(session, credential_id)
        if not record:
            raise ValueError("凭证不存在")

        # 查询安装记录（通过 Provider）
        provider = get_plugin_installation_provider()
        installation_dto = await provider.get_installation(tenant_id, plugin_id)
        if installation_dto is None:
            raise ValueError(f"插件不存在: {plugin_id}")

        # 获取 AI 侧配置用于凭证架构
        ai_config_result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = ai_config_result.scalar_one_or_none()

        credentials_schema = []
        if ai_config and ai_config.plugin_config:
            credentials_schema = credential_service.extract_credentials_schema(
                ai_config.plugin_config
            )

        update_data: dict[str, Any] = {}
        if obj_in.name is not None:
            # 检查凭证名称是否已存在
            if obj_in.name != record.name:
                existing_credential_stmt = select(PluginCredential).where(
                    and_(
                        PluginCredential.plugin_id == plugin_id,
                        PluginCredential.name == obj_in.name,
                        PluginCredential.id != record.id,
                    ),
                )
                existing_credential = (
                    await session.execute(existing_credential_stmt)
                ).scalar_one_or_none()
                if existing_credential:
                    raise BadRequestError(
                        f"凭证名称 '{obj_in.name}' 已存在，请使用其他名称"
                    )

            update_data["name"] = obj_in.name

        if isinstance(obj_in.credentials, dict):
            new_credentials = dict(obj_in.credentials)

            # 旧值脱敏占位回填
            if record.credentials:
                decrypted_old = credential_service.decrypt_credentials(
                    record.credentials,
                    credentials_schema,
                )
                masked_old = credential_service.mask_credentials(
                    decrypted_old, credentials_schema
                )
                for k, v in new_credentials.items():
                    if isinstance(v, str) and v == masked_old.get(k):
                        new_credentials[k] = decrypted_old.get(k)

            # 1) 格式校验
            credential_service.validate_credentials_format(
                new_credentials, credentials_schema
            )

            # 2) 加密
            encrypted = credential_service.encrypt_credentials(
                new_credentials, credentials_schema
            )
            update_data["credentials"] = encrypted

        await record.update(session, update_data)
        await record.refresh(session)
        return self._to_credential_vo(record)

    async def delete_credential(
        self,
        session: AsyncSession,
        credential_id: str,
    ) -> bool:
        """删除凭证"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        record = await PluginCredential.one_by_id(session, credential_id)
        if not record:
            raise ValueError("凭证不存在")

        await record.delete(session)
        return True

    def _to_credential_vo(self, record: PluginCredential) -> PluginCredentialVo:
        """转换凭证记录为 VO"""
        return PluginCredentialVo(
            id=str(record.id),
            plugin_id=record.plugin_id,
            scope=record.scope.value
            if hasattr(record.scope, "value")
            else str(record.scope),
            name=record.name,
            provider_name=record.provider_name,
            created_at=record.created_at.isoformat() if record.created_at else None,
            updated_at=record.updated_at.isoformat() if record.updated_at else None,
            created_by=getattr(record, "created_by", None),
            updated_by=getattr(record, "updated_by", None),
        )

    # ==================== 插件安装与卸载 ====================

    async def install_plugin(
        self,
        session: AsyncSession,
        plugin_package: bytes,
        auto_start: bool = True,
        install_config: dict[str, Any] = {},
    ) -> PluginInstallResponseVo:
        """安装插件"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            # 获取插件管理器
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            # 创建安装请求
            from ai.components.plugin.engine.models.request import InstallRequest

            install_request = InstallRequest(
                auto_start=auto_start, config_override=install_config
            )

            # 执行安装
            plugin_id = await plugin_manager.install_plugin(
                session, plugin_package, install_request
            )

            _logger.info(f"插件安装成功: {plugin_id}")

            return PluginInstallResponseVo(
                plugin_id=plugin_id,
                message="插件安装成功",
                status="installed" if not auto_start else "running",
            )

        except Exception as e:
            _logger.exception("插件安装失败")
            raise ValueError(f"插件安装失败: {str(e)}")

    async def start_plugin(
        self, session: AsyncSession, plugin_id: str
    ) -> PluginOperationResponseVo:
        """启动插件"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            success = await plugin_manager.start_plugin(plugin_id)

            if success:
                _logger.info(f"插件启动成功: {plugin_id}")
                return PluginOperationResponseVo(
                    plugin_id=plugin_id,
                    message="插件启动成功",
                    status="running",
                    success=True,
                )
            else:
                return PluginOperationResponseVo(
                    plugin_id=plugin_id,
                    message="插件启动失败",
                    status="error",
                    success=False,
                )

        except Exception as e:
            _logger.exception(f"插件启动失败: {plugin_id}")
            return PluginOperationResponseVo(
                plugin_id=plugin_id,
                message=f"插件启动失败: {str(e)}",
                status="error",
                success=False,
            )

    async def stop_plugin(
        self, session: AsyncSession, plugin_id: str
    ) -> PluginOperationResponseVo:
        """停止插件"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            success = await plugin_manager.stop_plugin(plugin_id)

            if success:
                _logger.info(f"插件停止成功: {plugin_id}")
                return PluginOperationResponseVo(
                    plugin_id=plugin_id,
                    message="插件停止成功",
                    status="stopped",
                    success=True,
                )
            else:
                return PluginOperationResponseVo(
                    plugin_id=plugin_id,
                    message="插件停止失败",
                    status="error",
                    success=False,
                )

        except Exception as e:
            _logger.exception(f"插件停止失败: {plugin_id}")
            return PluginOperationResponseVo(
                plugin_id=plugin_id,
                message=f"插件停止失败: {str(e)}",
                status="error",
                success=False,
            )

    async def uninstall_plugin(
        self,
        session: AsyncSession,
        plugin_id: str,
    ) -> PluginOperationResponseVo:
        """卸载插件"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)
            provider = get_plugin_installation_provider()

            # 1. 停止插件
            try:
                await plugin_manager.stop_plugin(plugin_id)
            except Exception:
                _logger.warning(f"卸载前停止插件失败: {plugin_id}")

            # 2. 删除 AI 侧配置
            await session.execute(
                delete(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
            )

            # 3. 删除 AI 侧运行时状态
            await session.execute(
                delete(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
            )

            # 4. 删除 Tenant 侧安装记录
            try:
                await provider.delete_installation(tenant_id, plugin_id)
            except ValueError:
                # 记录不存在，忽略
                pass
            except Exception as e:
                _logger.warning(f"删除 Tenant 侧安装记录失败: {plugin_id}, {e}")

            await session.flush()

            # 5. 删除本地运行目录
            try:
                import shutil

                plugin_dir = plugin_manager.workspace_dir / plugin_id
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)
                    _logger.info(f"已删除本地插件目录: {plugin_dir}")
            except Exception as e:
                _logger.warning(f"删除本地插件目录失败: {plugin_id}, {e}")

            # 6. 清理内存注册
            try:
                if plugin_id in plugin_manager.running_plugins:
                    del plugin_manager.running_plugins[plugin_id]
                if plugin_id in plugin_manager.plugins:
                    del plugin_manager.plugins[plugin_id]
            except Exception:
                pass

            _logger.info(f"插件卸载成功: {plugin_id}")
            return PluginOperationResponseVo(
                plugin_id=plugin_id,
                message="插件卸载成功",
                status="uninstalled",
                success=True,
            )

        except Exception as e:
            _logger.exception("插件卸载失败")
            return PluginOperationResponseVo(
                plugin_id=plugin_id,
                message=f"插件卸载失败: {str(e)}",
                status="error",
                success=False,
            )

    # ==================== 插件调用 ====================

    async def invoke_plugin_stream(
        self,
        session: AsyncSession,
        plugin_id: str,
        parameters: dict[str, Any],
        timeout: int,
    ):
        """流式调用插件方法"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            async for chunk in plugin_manager.invoke_plugin_stream(
                session, plugin_id, parameters, timeout
            ):
                yield chunk

            _logger.info(f"流式插件调用成功: {plugin_id}")

        except Exception as e:
            _logger.error(f"流式插件调用失败: {plugin_id}, error: {e}")
            raise e

    # ==================== 辅助方法 ====================

    async def _convert_combined_data_to_vo(
        self,
        installation_dto: Any,
        ai_config: AIPluginConfig | None,
        runtime_state: PluginRuntimeState | None,
    ) -> PluginInfoVo:
        """将组合数据转换为 VO 对象

        Args:
            installation_dto: PluginInstallationDTO 实例
            ai_config: AIPluginConfig 实例（可选）
            runtime_state: PluginRuntimeState 实例（可选）

        Returns:
            PluginInfoVo
        """
        from framework.tenant.plugin_protocols import PluginInstallationDTO

        # 提取插件配置信息
        plugin_config_dict = {}
        if ai_config and ai_config.plugin_config:
            plugin_config_dict = ai_config.plugin_config.get("configuration", {})

        # 确定状态：优先使用运行时状态，否则使用安装状态
        status = runtime_state.status if runtime_state else installation_dto.status

        return PluginInfoVo(
            plugin_id=installation_dto.plugin_id,
            plugin_name=plugin_config_dict.get("label", {}).get("zh_Hans")
            or installation_dto.plugin_id.split("/")[-1],
            version=plugin_config_dict.get("version", ""),
            author=plugin_config_dict.get("author", "unknown"),
            description=plugin_config_dict.get("description", {}).get("zh_Hans", ""),
            icon=plugin_config_dict.get("icon"),
            status=status,
            plugin_type=installation_dto.plugin_type or "",
            runtime_type=installation_dto.runtime_type or "",
            auto_start=installation_dto.auto_start,
            installed_at=None,  # 新架构中不再追踪安装时间
            last_started_at=runtime_state.last_started_at.isoformat()
            if runtime_state and runtime_state.last_started_at
            else None,
            last_stopped_at=runtime_state.last_stopped_at.isoformat()
            if runtime_state and runtime_state.last_stopped_at
            else None,
            last_accessed_at=runtime_state.last_accessed_at.isoformat()
            if runtime_state and runtime_state.last_accessed_at
            else None,
            process_id=runtime_state.process_id if runtime_state else None,
            port=runtime_state.port if runtime_state else None,
            call_count=runtime_state.call_count if runtime_state else 0,
            error_count=runtime_state.error_count if runtime_state else 0,
            last_error=runtime_state.last_error if runtime_state else None,
        )

    async def _update_last_accessed_time(
        self,
        session: AsyncSession,
        plugin_id: str,
    ):
        """更新插件最后访问时间（更新 AI 侧运行时状态）"""
        tenant_id = get_tenant_id()

        result = await session.execute(
            select(PluginRuntimeState).where(
                and_(
                    PluginRuntimeState.tenant_id == tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                ),
            ),
        )
        runtime_state = result.scalar_one_or_none()

        if runtime_state:
            runtime_state.last_accessed_at = datetime.now()
            runtime_state.call_count = (runtime_state.call_count or 0) + 1
            await session.flush()

    # ==================== 插件资源文件 ====================

    async def get_plugin_asset(
        self, session: AsyncSession, plugin_id: str, asset_path: str
    ) -> bytes:
        """获取插件资源文件内容"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            asset_content = await plugin_manager.get_plugin_asset(plugin_id, asset_path)

            if asset_content is None:
                raise ValueError(f"插件资源文件不存在: {plugin_id}/{asset_path}")

            _logger.info(f"获取插件资源文件成功: {plugin_id}/{asset_path}")

            return asset_content

        except Exception as e:
            _logger.exception(f"获取插件资源文件失败: {plugin_id}/{asset_path}")
            raise ValueError(f"获取插件资源文件失败: {str(e)}")

    # ==================== 运行时管理 ====================

    async def start_plugin_with_response(
        self, session: AsyncSession, plugin_id: str
    ) -> StartPluginResponse:
        """启动插件（带详细响应）"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            # 检查插件是否已安装
            provider = get_plugin_installation_provider()
            installation = await provider.get_installation(tenant_id, plugin_id)
            if not installation:
                raise ValueError(f"插件未安装: {plugin_id}")

            # 检查插件是否已在运行
            if plugin_id in plugin_manager.running_plugins:
                return StartPluginResponse(
                    plugin_id=plugin_id,
                    message="插件已在运行",
                    status="running",
                    success=True,
                    process_id=plugin_manager.running_plugins[plugin_id].process_id,
                    port=plugin_manager.running_plugins[plugin_id].port,
                )

            # 启动插件
            success = await plugin_manager.start_plugin(plugin_id)

            if success:
                # 获取运行时信息
                runtime = plugin_manager.running_plugins.get(plugin_id)
                process_id = runtime.process_id if runtime else None
                port = runtime.port if runtime else None

                # 更新数据库运行时状态
                await self._update_runtime_state_on_start(
                    session, tenant_id, plugin_id, process_id, port
                )

                _logger.info(f"插件启动成功: {plugin_id}")
                return StartPluginResponse(
                    plugin_id=plugin_id,
                    message="插件启动成功",
                    status="running",
                    success=True,
                    process_id=process_id,
                    port=port,
                )
            else:
                return StartPluginResponse(
                    plugin_id=plugin_id,
                    message="插件启动失败",
                    status="error",
                    success=False,
                )

        except Exception as e:
            _logger.exception(f"插件启动失败: {plugin_id}")
            return StartPluginResponse(
                plugin_id=plugin_id,
                message=f"插件启动失败: {str(e)}",
                status="error",
                success=False,
            )

    async def stop_plugin_with_response(
        self, session: AsyncSession, plugin_id: str
    ) -> StopPluginResponse:
        """停止插件（带详细响应）"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        try:
            from ai.components.plugin.engine.core.plugin_manager import (
                PluginManagerFactory,
            )

            plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

            # 检查插件是否在运行
            if plugin_id not in plugin_manager.running_plugins:
                return StopPluginResponse(
                    plugin_id=plugin_id,
                    message="插件未在运行",
                    status="inactive",
                    success=True,
                )

            # 停止插件
            success = await plugin_manager.stop_plugin(plugin_id, session)

            if success:
                # 更新数据库运行时状态
                await self._update_runtime_state_on_stop(session, tenant_id, plugin_id)

                _logger.info(f"插件停止成功: {plugin_id}")
                return StopPluginResponse(
                    plugin_id=plugin_id,
                    message="插件停止成功",
                    status="inactive",
                    success=True,
                )
            else:
                return StopPluginResponse(
                    plugin_id=plugin_id,
                    message="插件停止失败",
                    status="error",
                    success=False,
                )

        except Exception as e:
            _logger.exception(f"插件停止失败: {plugin_id}")
            return StopPluginResponse(
                plugin_id=plugin_id,
                message=f"插件停止失败: {str(e)}",
                status="error",
                success=False,
            )

    async def get_plugin_config(
        self, session: AsyncSession, plugin_id: str
    ) -> PluginConfigResponse:
        """获取插件配置"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 检查插件是否已安装
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(tenant_id, plugin_id)
        if not installation:
            raise ValueError(f"插件未安装: {plugin_id}")

        # 查询 AI 侧配置
        result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = result.scalar_one_or_none()

        return PluginConfigResponse(
            plugin_id=plugin_id,
            plugin_config=ai_config.plugin_config if ai_config else None,
            runtime_config=ai_config.runtime_config if ai_config else None,
        )

    async def update_plugin_config(
        self,
        session: AsyncSession,
        plugin_id: str,
        request: UpdatePluginConfigRequest,
    ) -> PluginConfigResponse:
        """更新插件配置"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 检查插件是否已安装
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(tenant_id, plugin_id)
        if not installation:
            raise ValueError(f"插件未安装: {plugin_id}")

        # 查询 AI 侧配置
        result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id == plugin_id,
            )
        )
        ai_config = result.scalar_one_or_none()

        if not ai_config:
            # 如果配置不存在，创建新配置
            ai_config = AIPluginConfig(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                plugin_unique_identifier=plugin_id,
                plugin_config={},
                runtime_config=request.runtime_config or {},
            )
            session.add(ai_config)
        else:
            # 更新运行时配置
            if request.runtime_config is not None:
                current_runtime = ai_config.runtime_config or {}
                # 创建新字典，确保 SQLAlchemy 检测到变更
                new_runtime = {**current_runtime, **request.runtime_config}
                ai_config.runtime_config = new_runtime
                # 强制标记 JSON 字段已修改
                flag_modified(ai_config, "runtime_config")
                _logger.info(f"更新配置: plugin_id={plugin_id}, old={current_runtime}, new={new_runtime}")

        await session.flush()
        await session.refresh(ai_config)

        _logger.info(f"更新插件配置: {plugin_id}")

        return PluginConfigResponse(
            plugin_id=plugin_id,
            plugin_config=ai_config.plugin_config,
            runtime_config=ai_config.runtime_config,
        )

    async def get_runtime_state(
        self, session: AsyncSession, plugin_id: str
    ) -> RuntimeStateResponse:
        """获取单个插件的运行时状态"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 检查插件是否已安装
        provider = get_plugin_installation_provider()
        installation = await provider.get_installation(tenant_id, plugin_id)
        if not installation:
            raise ValueError(f"插件未安装: {plugin_id}")

        # 查询运行时状态
        result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id == plugin_id,
            )
        )
        runtime_state = result.scalar_one_or_none()

        # 获取工作目录
        from ai.components.plugin.engine.core.plugin_manager import (
            PluginManagerFactory,
        )

        plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)
        work_directory = str(plugin_manager.workspace_dir / plugin_id)

        if not runtime_state:
            return RuntimeStateResponse(
                plugin_id=plugin_id,
                status="inactive",
                work_directory=work_directory,
                health_status="unknown",
            )

        # 计算成功率
        success_rate = None
        if runtime_state.call_count and runtime_state.call_count > 0:
            success_rate = (runtime_state.call_count - (runtime_state.error_count or 0)) / runtime_state.call_count * 100

        return RuntimeStateResponse(
            plugin_id=plugin_id,
            status=runtime_state.status,
            process_id=runtime_state.process_id,
            port=runtime_state.port,
            work_directory=work_directory,
            call_count=runtime_state.call_count or 0,
            error_count=runtime_state.error_count or 0,
            success_rate=success_rate,
            last_started_at=runtime_state.last_started_at.isoformat() if runtime_state.last_started_at else None,
            last_stopped_at=runtime_state.last_stopped_at.isoformat() if runtime_state.last_stopped_at else None,
            last_accessed_at=runtime_state.last_accessed_at.isoformat() if runtime_state.last_accessed_at else None,
            health_status=self._calculate_health_status(runtime_state),
            last_error=runtime_state.last_error,
        )

    async def get_runtime_states(
        self, session: AsyncSession
    ) -> RuntimeStateListResponse:
        """批量获取运行时状态"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 获取所有安装的插件
        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(tenant_id)

        if not installations:
            return RuntimeStateListResponse()

        plugin_ids = [inst.plugin_id for inst in installations]

        # 查询所有运行时状态
        result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id.in_(plugin_ids),
            )
        )
        runtime_states = {st.plugin_id: st for st in result.scalars().all()}

        # 获取 AI 配置用于提取名称
        config_result = await session.execute(
            select(AIPluginConfig).where(
                AIPluginConfig.tenant_id == tenant_id,
                AIPluginConfig.plugin_id.in_(plugin_ids),
            )
        )
        ai_configs = {cfg.plugin_id: cfg for cfg in config_result.scalars().all()}

        # 获取插件管理器
        from ai.components.plugin.engine.core.plugin_manager import (
            PluginManagerFactory,
        )

        plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

        # 构建响应
        items: list[RuntimeStateItem] = []
        running_count = 0
        frozen_count = 0
        total_memory_mb = 0.0
        total_cpu_percent = 0.0

        for inst in installations:
            runtime_state = runtime_states.get(inst.plugin_id)
            ai_config = ai_configs.get(inst.plugin_id)

            # 获取插件名称
            plugin_name = None
            if ai_config and ai_config.plugin_config:
                config_dict = ai_config.plugin_config.get("configuration", {})
                plugin_name = config_dict.get("label", {}).get("zh_Hans")

            # 获取运行时信息
            process_id = None
            port = None
            memory_mb = None
            cpu_percent = None
            status = "inactive"

            if runtime_state:
                status = runtime_state.status
                process_id = runtime_state.process_id
                port = runtime_state.port

            # 从运行中插件获取实时信息
            if inst.plugin_id in plugin_manager.running_plugins:
                runtime = plugin_manager.running_plugins[inst.plugin_id]
                process_id = runtime.process_id
                port = runtime.port

                # 统计
                if status == "active":
                    running_count += 1
                elif status == "frozen":
                    frozen_count += 1

            items.append(RuntimeStateItem(
                plugin_id=inst.plugin_id,
                plugin_name=plugin_name,
                status=status,
                process_id=process_id,
                port=port,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
            ))

        return RuntimeStateListResponse(
            items=items,
            running_count=running_count,
            frozen_count=frozen_count,
            total_memory_mb=total_memory_mb,
            total_cpu_percent=total_cpu_percent,
        )

    async def _update_runtime_state_on_start(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
        process_id: int | None,
        port: int | None,
    ):
        """启动后更新运行时状态"""
        result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id == plugin_id,
            )
        )
        runtime_state = result.scalar_one_or_none()

        if runtime_state:
            runtime_state.status = "active"
            runtime_state.process_id = process_id
            runtime_state.port = port
            runtime_state.last_started_at = datetime.now()
        else:
            # 创建新记录
            runtime_state = PluginRuntimeState(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                status="active",
                process_id=process_id,
                port=port,
                last_started_at=datetime.now(),
                call_count=0,
                error_count=0,
            )
            session.add(runtime_state)

        await session.flush()

    async def _update_runtime_state_on_stop(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ):
        """停止后更新运行时状态"""
        result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id == plugin_id,
            )
        )
        runtime_state = result.scalar_one_or_none()

        if runtime_state:
            runtime_state.status = "inactive"
            runtime_state.process_id = None
            runtime_state.port = None
            runtime_state.last_stopped_at = datetime.now()
            await session.flush()

    def _calculate_health_status(self, runtime_state: PluginRuntimeState) -> str:
        """计算健康状态"""
        if not runtime_state:
            return "unknown"

        if runtime_state.status == "inactive":
            return "unknown"

        # 如果有进程ID但状态为active，检查是否健康
        if runtime_state.status == "active":
            # 简单判断：如果错误率低于50%，认为健康
            if runtime_state.call_count and runtime_state.call_count > 0:
                error_rate = (runtime_state.error_count or 0) / runtime_state.call_count
                return "healthy" if error_rate < 0.5 else "unhealthy"
            return "healthy"

        if runtime_state.status == "frozen":
            return "unknown"

        return "unknown"

    # ==================== 统计仪表板 ====================

    async def get_statistics(self, session: AsyncSession) -> PluginUsageStatisticsResponse:
        """获取插件使用统计"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        # 获取所有安装的插件
        provider = get_plugin_installation_provider()
        installations = await provider.get_tenant_installations(tenant_id)

        if not installations:
            return PluginUsageStatisticsResponse(
                status_stats=PluginStatusStats(),
                usage_stats=PluginUsageStats(),
                runtime_stats=PluginRuntimeStats(),
                cached_at=datetime.now().isoformat(),
            )

        plugin_ids = [inst.plugin_id for inst in installations]

        # 查询所有运行时状态
        result = await session.execute(
            select(PluginRuntimeState).where(
                PluginRuntimeState.tenant_id == tenant_id,
                PluginRuntimeState.plugin_id.in_(plugin_ids),
            )
        )
        runtime_states = list(result.scalars().all())

        # 计算状态统计
        active_count = sum(1 for st in runtime_states if st.status == "active")
        inactive_count = sum(1 for st in runtime_states if st.status == "inactive")
        frozen_count = sum(1 for st in runtime_states if st.status == "frozen")
        error_count = sum(
            1 for st in runtime_states
            if st.status == "active" and st.error_count and st.error_count > 0
        )

        status_stats = PluginStatusStats(
            active_count=active_count,
            inactive_count=inactive_count,
            frozen_count=frozen_count,
            error_count=error_count,
        )

        # 计算使用统计
        total_invocations = sum(st.call_count or 0 for st in runtime_states)
        error_invocations = sum(st.error_count or 0 for st in runtime_states)
        success_rate = 0.0
        if total_invocations > 0:
            success_rate = (total_invocations - error_invocations) / total_invocations * 100

        # 今日调用数（暂时使用总调用数，后续可实现按日期统计）
        today_invocations = total_invocations

        usage_stats = PluginUsageStats(
            today_invocations=today_invocations,
            total_invocations=total_invocations,
            error_invocations=error_invocations,
            success_rate=round(success_rate, 2),
            avg_response_time_ms=None,  # 暂不实现
        )

        # 计算运行时统计
        from ai.components.plugin.engine.core.plugin_manager import (
            PluginManagerFactory,
        )

        plugin_manager = await PluginManagerFactory.get_manager(tenant_id, session)

        running_processes = sum(
            1 for pid in plugin_ids if pid in plugin_manager.running_plugins
        )
        frozen_processes = frozen_count

        runtime_stats = PluginRuntimeStats(
            running_processes=running_processes,
            frozen_processes=frozen_processes,
            total_memory_mb=0.0,  # 暂不实现
            total_cpu_percent=0.0,  # 暂不实现
            active_endpoints=0,  # 暂不实现
        )

        return PluginUsageStatisticsResponse(
            status_stats=status_stats,
            usage_stats=usage_stats,
            runtime_stats=runtime_stats,
            cached_at=datetime.now().isoformat(),
        )


# 全局服务实例
plugin_management_service = PluginManagementService()
