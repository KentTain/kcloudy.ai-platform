"""
管理后台插件定义控制器

提供插件定义管理 API：
- 扫描目录注册
- 上传插件包注册
- 列表查询（分页、筛选）
- 详情查看
- 更新（标记推荐/禁用）
- 删除（检查引用计数）
- 统计数据
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from tenant.middlewares.admin_auth_middleware import require_admin_permission
from tenant.schemas.plugin import (
    PluginDefinitionDetailResponse,
    PluginDefinitionPaginatedResponse,
    PluginDefinitionQuery,
    PluginStatisticsResponse,
    ScanDirectoryRequest,
    ScanDirectoryResponse,
    ScannedPluginResult,
    UpdatePluginDefinitionRequest,
    UploadPluginResponse,
)
from tenant.services.plugin_definition_service import plugin_definition_service
from tenant.services.plugin_package_service import plugin_package_service
from tenant.services.plugin_statistics_service import plugin_statistics_service

router = APIRouter()


@router.post("/plugin-definitions/scan")
async def scan_directory_for_plugins(
    request: ScanDirectoryRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    扫描服务器目录注册插件定义

    场景：平台管理员扫描服务器目录批量注册插件定义
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/scan
    THEN 扫描目录中的所有 .zip 文件，解析 manifest，上传到 MinIO，注册到 plugin_definitions 表

    流程：
    1. 遍历目录中的所有 .zip 文件
    2. 解析每个插件包的 manifest
    3. 上传到 MinIO
    4. 注册到数据库
    5. 返回扫描结果统计
    """
    directory = Path(request.directory)

    if not directory.exists():
        return ApiResponse.fail(message=f"目录不存在: {request.directory}")

    if not directory.is_dir():
        return ApiResponse.fail(message=f"路径不是目录: {request.directory}")

    # 收集所有 .zip 文件
    if request.recursive:
        zip_files = list(directory.rglob("*.zip"))
    else:
        zip_files = list(directory.glob("*.zip"))

    if not zip_files:
        return ApiResponse.success(
            data=ScanDirectoryResponse(
                total_count=0,
                success_count=0,
                skipped_count=0,
                failed_count=0,
                results=[],
            ).model_dump()
        )

    results: list[ScannedPluginResult] = []
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for zip_file in zip_files:
        try:
            # 解析插件包
            package_info = plugin_package_service.parse_package_from_path(zip_file)
            package_data = zip_file.read_bytes()

            # 注册插件定义
            try:
                response = await plugin_definition_service.register_definition(
                    session=session,
                    package_info=package_info,
                    package_data=package_data,
                    overwrite=False,
                )
                results.append(
                    ScannedPluginResult(
                        plugin_id=package_info.plugin_id,
                        version=package_info.version,
                        status="success",
                        message="注册成功",
                    )
                )
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                if "已存在" in error_msg:
                    results.append(
                        ScannedPluginResult(
                            plugin_id=package_info.plugin_id,
                            version=package_info.version,
                            status="skipped",
                            message="插件定义已存在",
                        )
                    )
                    skipped_count += 1
                else:
                    results.append(
                        ScannedPluginResult(
                            plugin_id=package_info.plugin_id,
                            version=package_info.version,
                            status="failed",
                            message=error_msg,
                        )
                    )
                    failed_count += 1

        except Exception as e:
            # 解析失败
            results.append(
                ScannedPluginResult(
                    plugin_id=zip_file.name,
                    version="unknown",
                    status="failed",
                    message=f"解析失败: {str(e)}",
                )
            )
            failed_count += 1

    # 提交事务
    await session.commit()

    return ApiResponse.success(
        data=ScanDirectoryResponse(
            total_count=len(zip_files),
            success_count=success_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results,
        ).model_dump()
    )


@router.post("/plugin-definitions/upload")
async def upload_plugin_package(
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
    file: UploadFile = File(..., description="插件包文件（.zip）"),
    overwrite: bool = Form(default=False, description="是否覆盖已存在的插件定义"),
) -> ApiResponse:
    """
    上传插件包注册插件定义

    场景：平台管理员上传插件包文件注册插件定义
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/upload
    THEN 解析 manifest，上传到 MinIO，注册到 plugin_definitions 表

    流程：
    1. 验证文件格式
    2. 解析插件包的 manifest
    3. 上传到 MinIO
    4. 注册到数据库
    5. 返回插件定义详情
    """
    # 验证文件格式
    if not file.filename or not file.filename.endswith(".zip"):
        return ApiResponse.fail(message="请上传 .zip 格式的插件包")

    # 读取文件内容
    package_data = await file.read()

    # 解析插件包
    try:
        package_info = plugin_package_service.parse_package_from_bytes(package_data)
    except Exception as e:
        return ApiResponse.fail(message=f"插件包解析失败: {str(e)}")

    # 注册插件定义
    try:
        response = await plugin_definition_service.register_definition(
            session=session,
            package_info=package_info,
            package_data=package_data,
            overwrite=overwrite,
        )

        # 提交事务
        await session.commit()

        return ApiResponse.success(
            data=UploadPluginResponse(
                plugin_id=response.plugin_id,
                version=package_info.version,
                plugin_unique_identifier=response.plugin_unique_identifier,
                status="updated" if overwrite else "created",
                message="插件定义注册成功",
            ).model_dump()
        )
    except Exception as e:
        error_msg = str(e)
        if "已存在" in error_msg:
            return ApiResponse.fail(message=f"插件定义已存在: {package_info.plugin_id}，如需覆盖请设置 overwrite=true")
        return ApiResponse.fail(message=f"注册失败: {error_msg}")


@router.get("/plugin-definitions")
async def list_plugin_definitions(
    _perm: None = Depends(require_admin_permission("tenant:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    type: str | None = None,
    is_recommended: bool | None = None,
    is_enabled: bool | None = None,
) -> ApiResponse:
    """
    获取插件定义列表（分页）

    场景：平台管理员查询插件定义列表
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions
    THEN 返回插件定义分页列表，支持关键词搜索、类型筛选、推荐/启用状态筛选
    """
    query = PluginDefinitionQuery(
        page=page,
        page_size=page_size,
        keyword=keyword,
        type=type,
        is_recommended=is_recommended,
        is_enabled=is_enabled,
    )
    result = await plugin_definition_service.list_definitions(session, query)
    return ApiResponse.paginated(
        data=result.items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/plugin-definitions/statistics")
async def get_plugin_statistics(
    _perm: None = Depends(require_admin_permission("tenant:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取插件统计数据

    场景：平台管理员查看插件定义统计数据
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions/statistics
    THEN 返回统计数据，包含 definition_stats（总数、按类型分布、推荐数、启用数）
         和 installation_stats（总安装数、活跃安装数、本周新增安装数）
    """
    statistics = await plugin_statistics_service.get_statistics(session)
    return ApiResponse.success(data=statistics.model_dump())


@router.get("/plugin-definitions/{plugin_id}")
async def get_plugin_definition_detail(
    plugin_id: str,
    _perm: None = Depends(require_admin_permission("tenant:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    获取插件定义详情

    场景：平台管理员查看插件定义详情
    WHEN 管理员请求 GET /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 返回插件定义详情，包含完整的 declaration 内容
    """
    result = await plugin_definition_service.get_definition_detail(session, plugin_id)
    return ApiResponse.success(data=result.model_dump())


@router.patch("/plugin-definitions/{plugin_id}")
async def update_plugin_definition(
    plugin_id: str,
    request: UpdatePluginDefinitionRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    更新插件定义（标记推荐/禁用）

    场景：平台管理员标记插件定义为推荐或禁用
    WHEN 管理员请求 PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 更新插件定义的 is_recommended 或 is_enabled 字段
    """
    result = await plugin_definition_service.update_definition(
        session, plugin_id, request
    )
    return ApiResponse.success(data=result.model_dump())


@router.delete("/plugin-definitions/{plugin_id}")
async def delete_plugin_definition(
    plugin_id: str,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    删除插件定义

    场景：平台管理员删除插件定义
    WHEN 管理员请求 DELETE /tenant/admin/v1/plugin-definitions/{plugin_id}
    THEN 检查 refers > 0 时禁止删除，否则删除定义

    Raises:
        ConflictError: 插件定义仍被租户引用（refers > 0）
    """
    await plugin_definition_service.delete_definition(session, plugin_id)
    return ApiResponse.success(message="插件定义已删除")
