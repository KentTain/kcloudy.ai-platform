"""
IAM 模块内部接口控制器 - 部门

提供模块间内部调用接口，不对外暴露。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from iam.models import Department
from iam.services.department_service import DepartmentService

router = APIRouter()


def Success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "msg": msg, "data": data}


class DepartmentInfoResponse(BaseModel):
    """部门信息响应"""
    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parent_id: str | None = Field(None, description="父部门ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")


class DepartmentTreeResponse(BaseModel):
    """部门树响应"""
    id: str = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    parent_id: str | None = Field(None, description="父部门ID")
    tree_level: int = Field(..., description="树层级")
    tree_path: str = Field(..., description="树路径")
    children: list["DepartmentTreeResponse"] = Field(default_factory=list, description="子部门")


def build_department_info(dept: Department) -> DepartmentInfoResponse:
    """构建部门信息响应"""
    return DepartmentInfoResponse(
        id=dept.id,
        name=dept.name,
        parent_id=dept.parent_id,
        tree_level=dept.tree_level,
        tree_path=dept.tree_path,
    )


def build_department_tree(departments: list[Department]) -> list[DepartmentTreeResponse]:
    """构建部门树"""
    # 按父ID分组
    children_map: dict[str | None, list[Department]] = {}
    for dept in departments:
        parent_id = dept.parent_id or None
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(dept)

    def build_node(dept: Department) -> DepartmentTreeResponse:
        children = children_map.get(dept.id, [])
        return DepartmentTreeResponse(
            id=dept.id,
            name=dept.name,
            parent_id=dept.parent_id,
            tree_level=dept.tree_level,
            tree_path=dept.tree_path,
            children=[build_node(c) for c in children],
        )

    # 找到根节点
    roots = children_map.get(None, [])
    return [build_node(r) for r in roots]


@router.get("/departments/tree")
async def get_department_tree(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取部门树

    场景：获取部门树
    WHEN 请求 GET /inner/v1/departments/tree
    THEN 返回完整的部门树结构
    """
    stmt = select(Department).order_by(Department.tree_sort)
    result = await session.execute(stmt)
    departments = list(result.scalars().all())

    tree = build_department_tree(departments)

    return ORJSONResponse(content=Success([t.model_dump() for t in tree]))


@router.get("/departments/{department_id}")
async def get_department(
    department_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    获取单个部门

    场景：获取单个部门
    WHEN 请求 GET /inner/v1/departments/{department_id}
    THEN 返回指定部门的详细信息

    场景：部门不存在
    WHEN 请求 GET /inner/v1/departments/nonexistent
    THEN 返回 HTTP 404
    """
    dept = await DepartmentService.get_by_id(session, department_id)

    if not dept:
        raise HTTPException(status_code=404, detail=f"部门 {department_id} 不存在")

    return ORJSONResponse(
        content=Success(build_department_info(dept).model_dump())
    )
