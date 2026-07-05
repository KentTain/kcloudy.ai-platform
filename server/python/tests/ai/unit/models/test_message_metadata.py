"""MessageMetadata 模型测试"""

import pytest

from ai.models.message_metadata import MessageMetadata


class TestMessageMetadata:
    """MessageMetadata 测试类"""

    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = MessageMetadata(
            message_id="msg-123",
            tenant_id="tenant-001",
            user_id="user-001",
            rating=2,
            feedback="很有帮助",
        )

        assert metadata.message_id == "msg-123"
        assert metadata.tenant_id == "tenant-001"
        assert metadata.user_id == "user-001"
        assert metadata.rating == 2
        assert metadata.feedback == "很有帮助"

    def test_metadata_default_values(self):
        """测试默认值"""
        metadata = MessageMetadata(
            message_id="msg-456",
            tenant_id="tenant-001",
            user_id="user-001",
        )

        assert metadata.rating is None
        assert metadata.feedback is None
        assert metadata.prompt_tokens is None

    def test_model_class_exists(self):
        """测试模型类存在"""
        assert hasattr(MessageMetadata, "__tablename__")
        assert MessageMetadata.__tablename__ == "message_metadata"

    def test_model_has_required_fields(self):
        """测试模型包含必需字段"""
        assert hasattr(MessageMetadata, "message_id")
        assert hasattr(MessageMetadata, "tenant_id")
        assert hasattr(MessageMetadata, "user_id")
        assert hasattr(MessageMetadata, "rating")
        assert hasattr(MessageMetadata, "feedback")
        assert hasattr(MessageMetadata, "prompt_tokens")
        assert hasattr(MessageMetadata, "completion_tokens")
        assert hasattr(MessageMetadata, "total_tokens")
        assert hasattr(MessageMetadata, "model_name")
        assert hasattr(MessageMetadata, "provider")
        assert hasattr(MessageMetadata, "response_time_ms")

    def test_model_inherits_base_model(self):
        """测试模型继承 BaseModel"""
        from ai.models import BaseModel

        assert issubclass(MessageMetadata, BaseModel)

    def test_mixin_fields_exist(self):
        """验证 TimestampMixin 字段存在"""
        assert hasattr(MessageMetadata, "id")
        assert hasattr(MessageMetadata, "created_at")
        assert hasattr(MessageMetadata, "updated_at")