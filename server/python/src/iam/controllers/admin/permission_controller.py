"""
权限控制器

提供权限查询接口。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from iam.services import permission_service

router = APIRouter()


@router.get("/permissions")
async def list_permissions(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取所有权限列表"""
    permissions = await permission_service.get_all_permissions(session)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "id": p.id,
                    "code": p.code,
                    "name": p.name,
                    "resource": p.resource,
                    "action": p.action,
                    "description": p.description,
                }
                for p in permissions
            ],
        }
    )


@router.get("/permissions/grouped")
async def get_permissions_grouped(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取按资源分组的权限"""
    grouped = await permission_service.get_permissions_grouped(session)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": {
                resource: [
                    {
                        "id": p.id,
                        "code": p.code,
                        "name": p.name,
                        "action": p.action,
                    }
                    for p in perms
                ]
                for resource, perms in grouped.items()
            },
        }
    )
