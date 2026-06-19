"""
部门控制器

提供部门管理接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.schemas.base import Success, SuccessExtra
from framework.tenant.context import get_tenant_id
from iam.schemas.department import (
    DepartmentCreate,
    DepartmentDetailResponse,
    DepartmentUpdate,
    DepartmentUserBatchRequest,
    MemberInfo,
    UserDepartmentRequest,
)
from iam.services import department_service

router = APIRouter()


@router.get("/departments")
async def list_departments(
    session: AsyncSession = Depends(get_db_session),
):
    """获取部门列表"""
    from iam.schemas.department import DepartmentListItem

    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    departments = await department_service.list_by_tenant(session, tenant_id)
    # 使用 Schema 转换方法，但保持原始数组格式
    items = [DepartmentListItem.from_department(d).model_dump() for d in departments]
    return Success(data=items)


@router.get("/departments/tree")
async def get_department_tree(
    session: AsyncSession = Depends(get_db_session),
):
    """获取部门树形结构"""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    tree = await department_service.get_tree(session, tenant_id)
    return Success(data=tree)


@router.post("/departments")
async def create_department(
    data: DepartmentCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """创建部门"""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="缺少租户上下文")
    dept = await department_service.create(
        session,
        tenant_id=tenant_id,
        name=data.name,
        parent_id=data.parent_id,
        code=data.code,
        sort_order=data.sort_order or 0,
        leader_id=data.leader_id,
    )
    return Success(
        data={
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
        }
    )


@router.put("/departments/{department_id}")
async def update_department(
    department_id: str,
    data: DepartmentUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新部门"""
    try:
        dept = await department_service.update(
            session,
            department_id=department_id,
            name=data.name,
            code=data.code,
            sort_order=data.sort_order,
            leader_id=data.leader_id,
            status=data.status,
        )
        return Success(
            data={
                "id": dept.id,
                "name": dept.name,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """删除部门"""
    try:
        await department_service.delete(session, department_id)
        return Success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/users")
async def get_department_users(
    department_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取部门用户列表"""
    users = await department_service.get_department_users(session, department_id)
    return Success(data=users)


@router.post("/departments/{department_id}/users")
async def add_user_to_department(
    department_id: str,
    data: UserDepartmentRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """添加用户到部门"""
    try:
        await department_service.add_user(
            session,
            department_id=department_id,
            user_id=data.user_id,
            is_leader=data.is_leader,
        )
        return Success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/departments/{department_id}/users/{user_id}")
async def remove_user_from_department(
    department_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """从部门移除用户"""
    try:
        removed = await department_service.remove_user(
            session,
            department_id=department_id,
            user_id=user_id,
        )
        if not removed:
            raise HTTPException(status_code=404, detail="用户不在该部门中")
        return Success(data=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/detail")
async def get_department_detail(
    department_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取部门详情（含统计信息）

    返回部门基本信息 + 直属成员数 + 累计成员数 + 组织路径
    """
    dept = await department_service.get_by_id(session, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    stats = await department_service.get_department_stats(session, department_id)

    return Success(
        data=DepartmentDetailResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            sort_order=dept.sort_order,
            leader_id=dept.leader_id,
            status=dept.status,
            created_at=dept.created_at,
            path=stats.get("path", ""),
            direct_member_count=stats.get("direct_member_count", 0),
            total_member_count=stats.get("total_member_count", 0),
            children_count=stats.get("children_count", 0),
        ).model_dump()
    )


@router.post("/departments/{department_id}/users/batch")
async def batch_add_users_to_department(
    department_id: str,
    data: DepartmentUserBatchRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """批量添加用户到部门"""
    try:
        added = await department_service.batch_add_users(
            session,
            department_id=department_id,
            user_ids=data.user_ids,
        )
        return Success(data={"added": added})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/departments/{department_id}/users/{user_id}/enable")
async def enable_department_user(
    department_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """启用部门成员"""
    from iam.services.user_service import UserService

    try:
        user = await UserService.set_status(session, user_id, "active")
        return Success(data={"user_id": user.id, "status": user.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/departments/{department_id}/users/{user_id}/disable")
async def disable_department_user(
    department_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """停用部门成员"""
    from iam.services.user_service import UserService

    try:
        user = await UserService.set_status(session, user_id, "inactive")
        return Success(data={"user_id": user.id, "status": user.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/members")
async def get_department_members(
    department_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取部门成员列表（详细版）"""
    users = await department_service.get_department_users(session, department_id)
    return Success(data=users)
