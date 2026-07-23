"""
插件定义服务

提供插件定义的管理功能：注册、查询、更新、删除。
"""

from typing import Any

from loguru import logger
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.exceptions import ConflictError, NotFoundError
from tenant.models.plugin import TenantPluginDefinition
from tenant.schemas.plugin import (
    InstallToTenantsRequest,
    InstallToTenantsResponse,
    PluginDefinitionDetailResponse,
    PluginDefinitionPaginatedResponse,
    PluginDefinitionQuery,
    PluginDefinitionResponse,
    UpdatePluginDefinitionRequest,
)
from tenant.services.plugin.plugin_package_service import PluginPackageInfo
from tenant.services.plugin.plugin_storage_service import plugin_storage_service

_logger = logger.bind(name=__name__)


class PluginDefinitionService:
    """插件定义服务"""

    @staticmethod
    async def register_definition(
        session: AsyncSession,
        package_info: PluginPackageInfo,
        package_data: bytes,
        overwrite: bool = False,
    ) -> PluginDefinitionResponse:
        """
        注册插件定义

        流程：
        1. 检查插件定义是否已存在
        2. 上传插件包到 MinIO
        3. 创建插件定义记录

        Args:
            session: 数据库会话
            package_info: 插件包解析结果
            package_data: 插件包二进制数据
            overwrite: 是否覆盖已存在的定义

        Returns:
            PluginDefinitionResponse: 注册结果

        Raises:
            ConflictError: 插件定义已存在且 overwrite=False
        """
        # 构建插件唯一标识符
        plugin_unique_identifier = f"{package_info.plugin_id}:{package_info.version}@{package_info.package_hash}"

        # 检查是否已存在（取最新的启用版本）
        existing_stmt = (
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == package_info.plugin_id,
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        existing_result = await session.execute(existing_stmt)
        existing_definition = existing_result.scalar_one_or_none()

        if existing_definition:
            if not overwrite:
                raise ConflictError(message=f"插件定义已存在: {package_info.plugin_id}")
            # 覆盖模式：更新现有记录
            return await PluginDefinitionService._update_existing_definition(
                session, existing_definition, package_info, package_data
            )

        # 上传插件包到 MinIO
        await plugin_storage_service.upload_plugin_package(
            plugin_id=package_info.plugin_id,
            version=package_info.version,
            package_data=package_data,
        )

        # 创建插件定义记录
        definition = TenantPluginDefinition(
            plugin_id=package_info.plugin_id,
            plugin_unique_identifier=plugin_unique_identifier,
            declaration=package_info.declaration,
            refers=0,
            install_type="local",
            manifest_type=package_info.manifest_type,
            is_recommended=False,
            is_enabled=True,
        )
        session.add(definition)
        await session.flush()
        await session.refresh(definition)

        _logger.info(
            f"注册插件定义成功: {package_info.plugin_id}:{package_info.version}"
        )

        return PluginDefinitionService._to_response(definition)

    @staticmethod
    async def _update_existing_definition(
        session: AsyncSession,
        existing: TenantPluginDefinition,
        package_info: PluginPackageInfo,
        package_data: bytes,
    ) -> PluginDefinitionResponse:
        """
        更新已存在的插件定义

        Args:
            session: 数据库会话
            existing: 现有插件定义
            package_info: 新的插件包解析结果
            package_data: 插件包二进制数据

        Returns:
            PluginDefinitionResponse: 更新后的响应
        """
        # 上传新版本的插件包
        await plugin_storage_service.upload_plugin_package(
            plugin_id=package_info.plugin_id,
            version=package_info.version,
            package_data=package_data,
        )

        # 更新插件定义
        plugin_unique_identifier = f"{package_info.plugin_id}:{package_info.version}@{package_info.package_hash}"

        existing.plugin_unique_identifier = plugin_unique_identifier
        existing.declaration = package_info.declaration
        existing.manifest_type = package_info.manifest_type

        await session.flush()
        await session.refresh(existing)

        _logger.info(
            f"更新插件定义成功: {package_info.plugin_id}:{package_info.version}"
        )

        return PluginDefinitionService._to_response(existing)

    @staticmethod
    async def list_definitions(
        session: AsyncSession,
        query: PluginDefinitionQuery,
    ) -> PluginDefinitionPaginatedResponse:
        """
        分页查询插件定义列表

        Args:
            session: 数据库会话
            query: 查询参数

        Returns:
            PluginDefinitionPaginatedResponse: 分页响应
        """
        conditions = []

        # 关键词搜索（匹配 plugin_id）
        if query.keyword:
            conditions.append(
                TenantPluginDefinition.plugin_id.ilike(f"%{query.keyword}%")
            )

        # 安装类型筛选
        if query.type:
            conditions.append(TenantPluginDefinition.install_type == query.type)

        # 推荐状态筛选
        if query.is_recommended is not None:
            conditions.append(
                TenantPluginDefinition.is_recommended == query.is_recommended
            )

        # 启用状态筛选
        if query.is_enabled is not None:
            conditions.append(TenantPluginDefinition.is_enabled == query.is_enabled)

        # 查询总数
        count_stmt = select(func.count(TenantPluginDefinition.id))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询列表
        offset = (query.page - 1) * query.page_size
        stmt = select(TenantPluginDefinition)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = (
            stmt.order_by(TenantPluginDefinition.refers.desc())
            .offset(offset)
            .limit(query.page_size)
        )

        result = await session.execute(stmt)
        definitions = list(result.scalars().all())

        # 转换为响应对象
        items = [PluginDefinitionService._to_response(d) for d in definitions]

        return PluginDefinitionPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    @staticmethod
    async def get_definition_detail(
        session: AsyncSession,
        plugin_id: str,
    ) -> PluginDefinitionDetailResponse:
        """
        获取插件定义详情

        Args:
            session: 数据库会话
            plugin_id: 插件ID

        Returns:
            PluginDefinitionDetailResponse: 详情响应

        Raises:
            NotFoundError: 插件定义不存在
        """
        stmt = (
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == plugin_id,
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        return PluginDefinitionDetailResponse(
            id=str(definition.id),
            plugin_id=definition.plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            declaration=definition.declaration or {},
            refers=definition.refers,
            install_type=definition.install_type,
            manifest_type=definition.manifest_type,
            is_recommended=definition.is_recommended,
            is_enabled=definition.is_enabled,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

    @staticmethod
    async def update_definition(
        session: AsyncSession,
        plugin_id: str,
        request: UpdatePluginDefinitionRequest,
    ) -> PluginDefinitionResponse:
        """
        更新插件定义（标记推荐/禁用）

        Args:
            session: 数据库会话
            plugin_id: 插件ID
            request: 更新请求

        Returns:
            PluginDefinitionResponse: 更新后的响应

        Raises:
            NotFoundError: 插件定义不存在
        """
        # 查询现有定义（取最新的启用版本）
        stmt = (
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == plugin_id,
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        # 更新字段
        update_data: dict[str, Any] = {}
        if request.is_recommended is not None:
            update_data["is_recommended"] = request.is_recommended
        if request.is_enabled is not None:
            update_data["is_enabled"] = request.is_enabled

        if update_data:
            update_stmt = (
                update(TenantPluginDefinition)
                .where(TenantPluginDefinition.id == definition.id)
                .values(**update_data)
            )
            await session.execute(update_stmt)
            await session.refresh(definition)

        return PluginDefinitionService._to_response(definition)

    @staticmethod
    async def delete_definition(
        session: AsyncSession,
        plugin_id: str,
    ) -> None:
        """
        删除插件定义

        同时删除 MinIO 上的插件包文件。

        Args:
            session: 数据库会话
            plugin_id: 插件ID

        Raises:
            NotFoundError: 插件定义不存在
            ConflictError: 插件定义仍被租户引用
        """
        # 查询现有定义（取最新的启用版本）
        stmt = (
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == plugin_id,
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        # 检查引用计数
        if definition.refers > 0:
            raise ConflictError(
                message=f"无法删除，有 {definition.refers} 个租户正在使用此插件"
            )

        # 删除 MinIO 上的插件包
        deleted_count = await plugin_storage_service.delete_all_versions(plugin_id)
        _logger.info(f"删除 MinIO 插件包: {plugin_id}, 共 {deleted_count} 个文件")

        # 删除定义
        delete_stmt = delete(TenantPluginDefinition).where(
            TenantPluginDefinition.id == definition.id
        )
        await session.execute(delete_stmt)

        _logger.info(f"已删除插件定义: {plugin_id}")

    @staticmethod
    def _to_response(definition: TenantPluginDefinition) -> PluginDefinitionResponse:
        """转换模型为响应对象"""
        return PluginDefinitionResponse(
            id=str(definition.id),
            plugin_id=definition.plugin_id,
            plugin_unique_identifier=definition.plugin_unique_identifier,
            refers=definition.refers,
            install_type=definition.install_type,
            manifest_type=definition.manifest_type,
            is_recommended=definition.is_recommended,
            is_enabled=definition.is_enabled,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

    @staticmethod
    async def preview_scan_directory(
        session: AsyncSession,
        directory: str,
        recursive: bool = False,
    ) -> list[dict[str, Any]]:
        """
        预览扫描目录中的插件

        Args:
            session: 数据库会话
            directory: 服务器目录路径
            recursive: 是否递归扫描子目录

        Returns:
            list[dict]: 预览结果列表
        """
        from pathlib import Path

        from tenant.services.plugin import plugin_package_service

        dir_path = Path(directory)

        if not dir_path.exists():
            raise ValueError(f"目录不存在: {directory}")

        if not dir_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

        # 收集所有 .zip 文件
        if recursive:
            zip_files = list(dir_path.rglob("*.zip"))
        else:
            zip_files = list(dir_path.glob("*.zip"))

        if not zip_files:
            return []

        results: list[dict[str, Any]] = []

        # 查询已存在的插件ID
        existing_stmt = select(TenantPluginDefinition.plugin_id)
        existing_result = await session.execute(existing_stmt)
        existing_ids = {row[0] for row in existing_result.fetchall()}

        for zip_file in zip_files:
            try:
                # 解析插件包
                package_info = plugin_package_service.parse_package_from_path(zip_file)

                # 从 declaration 中获取名称和描述
                manifest = package_info.declaration.get("_manifest", {})
                name = manifest.get("name", package_info.name)
                description = manifest.get("description", "")

                results.append(
                    {
                        "plugin_id": package_info.plugin_id,
                        "version": package_info.version,
                        "name": name,
                        "description": description,
                        "exists": package_info.plugin_id in existing_ids,
                        "status": "ready",
                        "error_message": None,
                    }
                )
            except Exception as e:
                # 解析失败
                results.append(
                    {
                        "plugin_id": zip_file.name,
                        "version": "unknown",
                        "name": zip_file.stem,
                        "description": "",
                        "exists": False,
                        "status": "invalid",
                        "error_message": str(e),
                    }
                )

        return results

    @staticmethod
    async def preview_parse_package(
        session: AsyncSession,
        package_data: bytes,
    ) -> dict[str, Any]:
        """
        预览解析插件包

        Args:
            session: 数据库会话
            package_data: 插件包二进制数据

        Returns:
            dict: 解析结果

        Raises:
            ValueError: 插件包解析失败
        """
        from tenant.services.plugin import plugin_package_service

        # 解析插件包
        package_info = plugin_package_service.parse_package_from_bytes(package_data)

        # 检查是否已存在
        existing_stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == package_info.plugin_id
        )
        existing_result = await session.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        # 从 declaration 中获取名称和描述
        manifest = package_info.declaration.get("_manifest", {})
        name = manifest.get("name", package_info.name)
        description = manifest.get("description", "")

        return {
            "plugin_id": package_info.plugin_id,
            "version": package_info.version,
            "name": name,
            "description": description,
            "manifest_type": package_info.manifest_type,
            "declaration": package_info.declaration,
            "exists": existing is not None,
        }

    @staticmethod
    async def install_to_tenants(
        session: AsyncSession,
        plugin_id: str,
        request: InstallToTenantsRequest,
    ) -> InstallToTenantsResponse:
        """
        安装插件到指定租户

        流程：
        1. 查询插件定义，校验存在且启用
        2. 遍历租户列表，校验租户存在性和安装状态
        3. 通过 Inner API 批量创建 AI 侧数据
        4. 根据 AI 侧结果创建 Tenant 侧安装记录

        Args:
            session: 数据库会话
            plugin_id: 插件ID
            request: 安装请求

        Returns:
            InstallToTenantsResponse: 批量安装结果
        """
        from framework.clients.ai_client import InstallationItem, get_ai_client
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            get_plugin_installation_provider,
        )
        from tenant.models.plugin import TenantPluginInstallation
        from tenant.models.tenant import Tenant
        from tenant.schemas.plugin import (
            InstallFailedItem,
            InstallSkippedItem,
            InstallSuccessItem,
        )

        # 1. 查询插件定义（取最新的启用版本）
        stmt = (
            select(TenantPluginDefinition)
            .where(
                TenantPluginDefinition.plugin_id == plugin_id,
                TenantPluginDefinition.is_enabled == True,
            )
            .order_by(TenantPluginDefinition.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        if not definition.is_enabled:
            raise ValueError(f"插件定义已禁用: {plugin_id}")

        success: list[InstallSuccessItem] = []
        failed: list[InstallFailedItem] = []
        skipped: list[InstallSkippedItem] = []

        # 2. 准备批量安装数据
        installation_items = []
        valid_tenant_ids = []

        for tenant_id in request.tenant_ids:
            try:
                # 校验租户存在
                tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
                tenant_result = await session.execute(tenant_stmt)
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    failed.append(
                        InstallFailedItem(
                            tenant_id=tenant_id,
                            message="租户不存在",
                        )
                    )
                    continue

                # 检查是否已安装
                existing_stmt = select(TenantPluginInstallation).where(
                    TenantPluginInstallation.tenant_id == tenant_id,
                    TenantPluginInstallation.plugin_id == plugin_id,
                )
                existing_result = await session.execute(existing_stmt)
                existing_installation = existing_result.scalar_one_or_none()
                if existing_installation:
                    skipped.append(
                        InstallSkippedItem(
                            tenant_id=tenant_id,
                            reason="already_installed",
                        )
                    )
                    continue

                # 准备安装项
                installation_items.append(
                    InstallationItem(
                        tenant_id=tenant_id,
                        plugin_id=definition.plugin_id,
                        plugin_unique_identifier=definition.plugin_unique_identifier,
                        declaration=definition.declaration or {},
                        auto_start=request.auto_start,
                    )
                )
                valid_tenant_ids.append(tenant_id)

            except Exception as e:
                _logger.error(f"准备安装数据失败: tenant_id={tenant_id}, error={e}")
                failed.append(
                    InstallFailedItem(
                        tenant_id=tenant_id,
                        message=str(e),
                    )
                )

        # 3. 通过 Inner API 批量创建 AI 侧数据
        if installation_items:
            ai_client = get_ai_client()
            ai_result = await ai_client.batch_install_plugins(
                session, installation_items
            )

            # 4. 根据 AI 侧结果创建 Tenant 侧记录
            provider = get_plugin_installation_provider()

            for item in ai_result.success:
                try:
                    # 创建 Tenant 侧安装记录
                    dto = PluginInstallationDTO(
                        tenant_id=item.tenant_id,
                        plugin_id=definition.plugin_id,
                        plugin_unique_identifier=definition.plugin_unique_identifier,
                        declaration=definition.declaration or {},
                        status="INACTIVE",  # AI 侧已创建，状态为 INACTIVE
                        auto_start=request.auto_start,
                        plugin_type=definition.install_type,
                    )
                    await provider.create_installation(item.tenant_id, dto)
                    success.append(
                        InstallSuccessItem(
                            tenant_id=item.tenant_id,
                            plugin_id=plugin_id,
                        )
                    )
                except Exception as e:
                    _logger.error(
                        f"创建租户安装记录失败: tenant_id={item.tenant_id}, error={e}"
                    )
                    failed.append(
                        InstallFailedItem(
                            tenant_id=item.tenant_id,
                            message=f"创建安装记录失败: {str(e)}",
                        )
                    )

            # 添加 AI 侧失败和跳过的记录
            for item in ai_result.failed:
                failed.append(
                    InstallFailedItem(
                        tenant_id=item.tenant_id,
                        message=item.message,
                    )
                )

            for item in ai_result.skipped:
                skipped.append(
                    InstallSkippedItem(
                        tenant_id=item.tenant_id,
                        reason=item.reason,
                    )
                )

        _logger.info(
            f"安装插件到租户完成: plugin_id={plugin_id}, "
            f"success={len(success)}, failed={len(failed)}, skipped={len(skipped)}"
        )

        return InstallToTenantsResponse(
            success=success,
            failed=failed,
            skipped=skipped,
        )


# 单例实例
plugin_definition_service = PluginDefinitionService()
