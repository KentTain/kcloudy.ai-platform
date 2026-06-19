"""模型列表 Schema 测试"""

from ai.schemas.model import ModelItem, ModelListResponse, ProviderItem


class TestModelItem:
    """模型项 Schema 测试"""

    def test_model_item_creation(self):
        """测试创建模型项"""
        item = ModelItem(id="openai/gpt-4o-mini", name="gpt-4o-mini", description="GPT-4o Mini")
        assert item.id == "openai/gpt-4o-mini"
        assert item.name == "gpt-4o-mini"
        assert item.description == "GPT-4o Mini"

    def test_model_item_optional_description(self):
        """测试描述字段可选"""
        item = ModelItem(id="openai/gpt-4o", name="gpt-4o")
        assert item.id == "openai/gpt-4o"
        assert item.name == "gpt-4o"
        assert item.description is None


class TestProviderItem:
    """提供商项 Schema 测试"""

    def test_provider_item_creation(self):
        """测试创建提供商项"""
        models = [
            ModelItem(id="openai/gpt-4o-mini", name="gpt-4o-mini"),
            ModelItem(id="openai/gpt-4o", name="gpt-4o"),
        ]
        provider = ProviderItem(id="openai", name="OpenAI", models=models)
        assert provider.id == "openai"
        assert provider.name == "OpenAI"
        assert len(provider.models) == 2

    def test_provider_item_empty_models(self):
        """测试空模型列表"""
        provider = ProviderItem(id="openai", name="OpenAI")
        assert provider.models == []


class TestModelListResponse:
    """模型列表响应 Schema 测试"""

    def test_response_creation(self):
        """测试创建响应"""
        models = [ModelItem(id="openai/gpt-4o-mini", name="gpt-4o-mini")]
        provider = ProviderItem(id="openai", name="OpenAI", models=models)
        response = ModelListResponse(providers=[provider])
        assert len(response.providers) == 1
        assert response.providers[0].id == "openai"

    def test_response_empty_providers(self):
        """测试空提供商列表"""
        response = ModelListResponse()
        assert response.providers == []

    def test_response_serialization(self):
        """测试序列化"""
        models = [ModelItem(id="openai/gpt-4o-mini", name="gpt-4o-mini", description="GPT-4o Mini")]
        provider = ProviderItem(id="openai", name="OpenAI", models=models)
        response = ModelListResponse(providers=[provider])

        data = response.model_dump()
        assert "providers" in data
        assert len(data["providers"]) == 1
        assert data["providers"][0]["id"] == "openai"
        assert data["providers"][0]["models"][0]["id"] == "openai/gpt-4o-mini"
