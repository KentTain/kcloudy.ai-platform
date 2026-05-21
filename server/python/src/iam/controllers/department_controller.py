"""
部门控制器

提供部门管理接口。
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import ORJSONResponse

from schemas.iam.department import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    UserDepartmentRequest,
)
from services.iam import department_service

router = APIRouter()


@router.get("")
async def list_departments(tenant_id: str) -> ORJSONResponse:
    """获取部门列表"""
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


@router.get("/tree")
async def get_department_tree(tenant_id: str) -> ORJSONResponse:
    """获取部门树形结构"""
    tree = await department_service.get_tree(tenant_id)
    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": tree,
        }
    )


@router.post("")
async def create_department(data: DepartmentCreateRequest) -> ORJSONResponse:
    """创建部门"""
    # tenant_id 从上下文获取，这里暂时用参数
    dept = await department_service.create(
        tenant_id="default",  # TODO: 从上下文获取
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


@router.put("/{department_id}")
async def update_department(department_id: str, data: DepartmentUpdateRequest) -> ORJSONResponse:
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


@router.delete("/{department_id}")
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


@router.get("/{department_id}/users")
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


@router.post("/{department_id}/users")
async def add_user_to_department(department_id: str, data: UserDepartmentRequest) -> ORJSONResponse:
    """添加用户到部门"""
    try:
        await department_service.add_user(
            department_id=department_id,
            user_id=data.department_id,  # TODO: 从 data 获取 user_id
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
