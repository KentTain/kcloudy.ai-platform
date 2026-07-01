"""测试 BaseModel to_dict 方法"""

import enum
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.core.base import BaseModel


class StatusEnum(enum.Enum):
    """状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class SampleModel(BaseModel):
    """测试模型"""
    __tablename__ = "test_model"

    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[StatusEnum] = mapped_column(default=StatusEnum.ACTIVE)


def test_to_dict_basic():
    """测试基本 to_dict 功能"""
    model = SampleModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    result = model.to_dict()

    assert result["name"] == "test"
    assert result["status"] == "active"  # 枚举转为值


def test_to_dict_with_exclude():
    """测试 to_dict 排除字段"""
    model = SampleModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    result = model.to_dict(exclude=["status"])

    assert "name" in result
    assert "status" not in result


def test_to_dict_datetime_conversion():
    """测试 datetime 类型转换"""
    now = datetime.now(timezone.utc)
    model = SampleModel(id=str(uuid4()), name="test", status=StatusEnum.ACTIVE)
    model.created_at = now

    result = model.to_dict()

    assert isinstance(result["created_at"], str)  # ISO 格式字符串


def test_to_dict_uuid_conversion():
    """测试 UUID 类型转换"""
    uuid_str = str(uuid4())
    model = SampleModel(id=uuid_str, name="test", status=StatusEnum.ACTIVE)

    result = model.to_dict()

    assert result["id"] == uuid_str
