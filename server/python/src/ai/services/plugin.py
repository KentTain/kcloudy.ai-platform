"""
插件管理服务层

负责封装 plugin_manager 的调用逻辑，提供高级业务接口。
适配 framework 基础设施：crypto, storage, ctx。
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import (
    CredentialScope,
    PluginCredential,
    PluginStatus,
    PluginType,
)
from ai.models.plugin_config import PluginConfig as AIPluginConfig
from ai.models.plugin_runtime_state import PluginRuntimeState
from ai.schemas.plugin import (
    CreatePluginCredential,
    PluginCredentialVo,
    PluginInfoVo,
    PluginInstallResponseVo,
    PluginOperationResponseVo,
    PluginPaginatedListResponseVo,
    UpdatePluginCredential,
)
from ai.services.credential_service import credential_service
from framework.common.ctx import get_tenant_id, get_user_id
from framework.common.exceptions import BadRequestError
from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    get_plugin_installation_provider,
)

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
        limit: int = 50,
        offset: int = 0,
    ) -> PluginPaginatedListResponseVo:
        """获取插件列表"""
        tenant_id = get_tenant_id()
        if not tenant_id:
            raise ValueError("租户ID不能为空")

        _logger.info(
            f"获取插件列表: tenant_id={tenant_id}, status={status}, "
            f"plugin_id={plugin_id}, plugin_type={plugin_type}, limit={limit}, offset={offset}"
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
        paged_data = combined_data[offset : offset + limit]

        # 6. 转换为 VO
        plugin_vos = []
        for inst, ai_config, runtime_state in paged_data:
            plugin_vo = await self._convert_combined_data_to_vo(
                inst, ai_config, runtime_state
            )
            plugin_vos.append(plugin_vo)

        return PluginPaginatedListResponseVo(plugins=plugin_vos, total=total)

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


# 全局服务实例
plugin_management_service = PluginManagementService()
