"""文本嵌入模型基类

迁移自 Alon: src/alon/components/model/model_providers/__base__/text_embedding_model.py
"""

from pydantic import ConfigDict

from ai.components.model.model_providers.__base__.ai_model import AIModelImpl
from ai.components.plugin.client.model_client import ModelClient
from ai_plugin.sdk.entities.model import ModelPropertyKey, ModelType
from ai_plugin.sdk.entities.model.text_embedding import TextEmbeddingResult


class TextEmbeddingModelImpl(AIModelImpl):
    """文本嵌入模型基础类"""

    model_type: ModelType = ModelType.TEXT_EMBEDDING

    # pydantic 配置
    model_config = ConfigDict(protected_namespaces=())

    async def invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: str | None = None,
    ) -> TextEmbeddingResult:
        """调用文本嵌入模型"""
        try:
            model_client = ModelClient()

            return await model_client.invoke_text_embedding(
                tenant_id=self.tenant_id,
                user_id=user or "unknown",
                plugin_id=self.plugin_id,
                provider=self.provider_name,
                model=model,
                credentials=credentials,
                texts=texts,
            )
        except Exception as e:
            raise self._transform_invoke_error(e)

    async def get_num_tokens(
        self, model: str, credentials: dict, texts: list[str]
    ) -> list[int]:
        """获取给定文本的 token 数量"""
        model_client = ModelClient()

        return await model_client.get_text_embedding_num_tokens(
            tenant_id=self.tenant_id,
            user_id="unknown",
            plugin_id=self.plugin_id,
            provider=self.provider_name,
            model=model,
            credentials=credentials,
            texts=texts,
        )

    async def _get_context_size(self, model: str, credentials: dict) -> int:
        """获取给定嵌入模型的上下文大小"""
        model_schema = await self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.CONTEXT_SIZE in model_schema.model_properties
        ):
            content_size: int = model_schema.model_properties[
                ModelPropertyKey.CONTEXT_SIZE
            ]
            return content_size

        return 1000

    async def _get_max_chunks(self, model: str, credentials: dict) -> int:
        """获取给定嵌入模型的最大块数"""
        model_schema = await self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.MAX_CHUNKS in model_schema.model_properties
        ):
            max_chunks: int = model_schema.model_properties[ModelPropertyKey.MAX_CHUNKS]
            return max_chunks

        return 1
