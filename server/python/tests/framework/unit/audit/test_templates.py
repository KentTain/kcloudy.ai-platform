"""测试审计日志模板"""

import pytest
from framework.audit.templates import AuditTemplateBuilder


def test_build_template_key():
    """测试构建模板 Key"""
    builder = AuditTemplateBuilder()

    template_key = builder.build_template_key(
        module="iam",
        resource="user",
        action="create"
    )

    assert template_key == "audit.iam.user.create"


def test_build_detail_full():
    """测试构建完整 detail"""
    builder = AuditTemplateBuilder()

    detail = builder.build_detail(
        module="iam",
        resource="user",
        action="create",
        operator_name="张三",
        operated_at="2026-07-01 10:30:00",
        resource_name="李四",
        extra={"role": "管理员"}
    )

    assert detail["text"] == "张三在2026-07-01 10:30:00对用户\"李四\"进行了创建操作"
    assert detail["template_key"] == "audit.iam.user.create"
    assert detail["params"]["operator_name"] == "张三"
    assert detail["params"]["resource_name"] == "李四"
    assert detail["params"]["operation_type"] == "创建"
    assert detail["extra"]["role"] == "管理员"


def test_build_detail_without_extra():
    """测试构建不带 extra 的 detail"""
    builder = AuditTemplateBuilder()

    detail = builder.build_detail(
        module="iam",
        resource="user",
        action="update",
        operator_name="张三",
        operated_at="2026-07-01 10:30:00",
        resource_name="李四"
    )

    assert detail["text"] == "张三在2026-07-01 10:30:00对用户\"李四\"进行了更新操作"
    assert "extra" not in detail or detail["extra"] is None
