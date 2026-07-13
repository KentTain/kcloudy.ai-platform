"""会话模型单元测试"""


from ai.models.conversation import Conversation


class TestConversationModel:
    def test_tablename(self):
        assert Conversation.__tablename__ == "conversations"

    def test_schema(self):
        args = Conversation.__table_args__
        if isinstance(args, tuple):
            assert args[0]["schema"] == "ai"
        else:
            assert args["schema"] == "ai"

    def test_has_required_fields(self):
        columns = {c.name for c in Conversation.__table__.columns}
        assert "id" in columns
        assert "tenant_id" in columns
        assert "app_id" in columns
        assert "name" in columns
        assert "status" in columns
        assert "mode" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_status_default(self):
        status_col = Conversation.__table__.columns["status"]
        assert status_col.default is not None

    def test_mode_default(self):
        mode_col = Conversation.__table__.columns["mode"]
        assert mode_col.default is not None

    def test_inherits_active_record(self):
        from framework.database.mixins.active_record import ActiveRecordMixin
        assert issubclass(Conversation, ActiveRecordMixin)

    def test_inherits_tenant_mixin(self):
        from framework.database.mixins.tenant import TenantMixin
        assert issubclass(Conversation, TenantMixin)
