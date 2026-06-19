"""消息模型单元测试"""


from ai.models.message import Message


class TestMessageModel:
    def test_tablename(self):
        assert Message.__tablename__ == "messages"

    def test_schema(self):
        args = Message.__table_args__
        if isinstance(args, tuple):
            assert args[0]["schema"] == "ai"
        else:
            assert args["schema"] == "ai"

    def test_has_required_fields(self):
        columns = {c.name for c in Message.__table__.columns}
        assert "id" in columns
        assert "tenant_id" in columns
        assert "app_id" in columns
        assert "conversation_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "status" in columns
        assert "query" in columns
        assert "answer" in columns
        assert "message_metadata" in columns
        assert "token_count" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_status_default(self):
        status_col = Message.__table__.columns["status"]
        assert status_col.default is not None

    def test_has_foreign_key_to_conversation(self):
        fk_cols = Message.__table__.columns["conversation_id"]
        fks = list(fk_cols.foreign_keys)
        assert len(fks) == 1
        assert str(fks[0].target_fullname) == "ai.conversations.id"

    def test_inherits_active_record(self):
        from framework.database.mixins.active_record import ActiveRecordMixin
        assert issubclass(Message, ActiveRecordMixin)

    def test_inherits_tenant_mixin(self):
        from framework.database.mixins.tenant import TenantMixin
        assert issubclass(Message, TenantMixin)
