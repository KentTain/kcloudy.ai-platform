"""
部门控制器

提供部门管理接口。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from iam.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    UserDepartmentRequest,
)
from iam.services import department_service
from framework.tenant.context import get_tenant_id

router = APIRouter()


@router.get("/departments")
async def list_departments() -> ORJSONResponse:
    """获取部门列表"""
    tenant_id = get_tenant_id()
    departments = await department_service.list_by_tenant(tenant_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "id": d.id,
                    "name": d.name,
                    "code": d.code,
                    "parent_id": d.parent_id,
                    "sort_order": d.sort_order,
                    "leader_id": d.leader_id,
                    "status": d.status,
                }
                for d in departments
            ],
        }
    )


@router.get("/departments/tree")
async def get_department_tree() -> ORJSONResponse:
    """获取部门树形结构"""
    tenant_id = get_tenant_id()
    tree = await department_service.get_tree(tenant_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": tree,
        }
    )


@router.post("/departments")
async def create_department(data: DepartmentCreate) -> ORJSONResponse:
    """创建部门"""
    tenant_id = get_tenant_id()
    dept = await department_service.create(
        tenant_id=tenant_id,
        name=data.name,
        parent_id=data.parent_id,
        code=data.code,
        sort_order=data.sort_order or 0,
        leader_id=data.leader_id,
    )
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "创建成功",
            "data": {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
            },
        }
    )


@router.put("/departments/{department_id}")
async def update_department(department_id: str, data: DepartmentUpdate) -> ORJSONResponse:
    """更新部门"""
    try:
        dept = await department_service.update(
            department_id=department_id,
            name=data.name,
            code=data.code,
            sort_order=data.sort_order,
            leader_id=data.leader_id,
            status=data.status,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "更新成功",
                "data": {
                    "id": dept.id,
                    "name": dept.name,
                },
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/departments/{department_id}")
async def delete_department(department_id: str) -> ORJSONResponse:
    """删除部门"""
    try:
        await department_service.delete(department_id)
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "删除成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/users")
async def get_department_users(department_id: str) -> ORJSONResponse:
    """获取部门用户列表"""
    users = await department_service.get_department_users(department_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": users,
        }
    )


@router.post("/departments/{department_id}/users")
async def add_user_to_department(department_id: str, data: UserDepartmentRequest) -> ORJSONResponse:
    """添加用户到部门"""
    try:
        await department_service.add_user(
            department_id=department_id,
            user_id=data.user_id,
            is_leader=data.is_leader,
        )
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "添加成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/departments/{department_id}/users/{user_id}")
async def remove_user_from_department(
    department_id: str,
    user_id: str,
) -> ORJSONResponse:
    """从部门移除用户"""
    try:
        removed = await department_service.remove_user(
            department_id=department_id,
            user_id=user_id,
        )
        if not removed:
            raise HTTPException(status_code=404, detail="用户不在该部门中")
        return ORJSONResponse(
            content={
                "code": 200,
                "msg": "移除成功",
                "data": None,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
