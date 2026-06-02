import json
import time
from decimal import Decimal
from urllib.parse import urljoin

import requests

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import (
    AIModelEntity,
    EmbeddingInputType,
    FetchFrom,
    ModelPropertyKey,
    ModelType,
    PriceConfig,
    PriceType,
)
from ai_plugin.sdk.entities.model.text_embedding import (
    EmbeddingUsage,
    TextEmbeddingResult,
)
from ai_plugin.sdk.errors.model import (
    CredentialsValidateFailedError,
)
from ai_plugin.sdk.interfaces.model.openai_compatible.common import (
    _CommonOaiApiCompat,
)
from ai_plugin.sdk.interfaces.model.text_embedding_model import TextEmbeddingModel


class OAICompatEmbeddingModel(_CommonOaiApiCompat, TextEmbeddingModel):
    """OpenAI API兼容的文本嵌入模型类

    提供与OpenAI API兼容的文本嵌入模型实现。
    """

    def _invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: str | None = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """调用文本嵌入模型

        Args:
            model: 模型名称
            credentials: 模型凭证
            texts: 要嵌入的文本列表
            user: 唯一用户ID
            input_type: 输入类型

        Returns:
            嵌入结果
        """

        # 为请求准备请求头和载荷
        headers = {"Content-Type": "application/json"}

        api_key = credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        endpoint_url = credentials.get("endpoint_url", "")
        if not endpoint_url.endswith("/"):
            endpoint_url += "/"

        endpoint_url = urljoin(endpoint_url, "embeddings")

        extra_model_kwargs = {}
        if user:
            extra_model_kwargs["user"] = user

        extra_model_kwargs["encoding_format"] = "float"

        # 获取模型属性
        context_size = self._get_context_size(model, credentials)
        max_chunks = self._get_max_chunks(model, credentials)

        inputs = []
        indices = []
        used_tokens = 0

        for i, text in enumerate(texts):
            # 这里的token计数只是基于GPT2分词器的近似值
            # 待办：优化token估算和分块
            num_tokens = self._get_num_tokens_by_gpt2(text)

            if num_tokens >= context_size:
                cutoff = int((len(text) * context_size) // num_tokens)
                # 如果token数大于上下文长度，只使用开头部分
                inputs.append(text[0:cutoff])
            else:
                inputs.append(text)
            indices += [i]

        batched_embeddings = []
        _iter = range(0, len(inputs), max_chunks)

        for i in _iter:
            # 为请求准备载荷
            payload = {
                "input": inputs[i : i + max_chunks],
                "model": model,
                **extra_model_kwargs,
            }

            # 向OpenAI API发起请求
            response = requests.post(
                endpoint_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=(10, 300),
            )

            response.raise_for_status()  # 对HTTP错误抛出异常
            response_data = response.json()

            # 从响应中提取嵌入和使用的token
            embeddings_batch = [data["embedding"] for data in response_data["data"]]
            embedding_used_tokens = response_data["usage"]["total_tokens"]

            used_tokens += embedding_used_tokens
            batched_embeddings += embeddings_batch

        # 计算使用量
        usage = self._calc_response_usage(
            model=model, credentials=credentials, tokens=used_tokens
        )

        return TextEmbeddingResult(
            embeddings=batched_embeddings, usage=usage, model=model
        )

    def get_num_tokens(
        self, model: str, credentials: dict, texts: list[str]
    ) -> list[int]:
        """使用GPT2分词器近似计算给定消息的token数量

        Args:
            model: 模型名称
            credentials: 模型凭证
            texts: 要嵌入的文本列表

        Returns:
            每个文本对应的token数量列表
        """
        return [self._get_num_tokens_by_gpt2(text) for text in texts]

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """验证模型凭证

        Args:
            model: 模型名称
            credentials: 模型凭证

        Raises:
            CredentialsValidateFailedError: 当凭证验证失败时抛出异常
        """
        try:
            headers = {"Content-Type": "application/json"}

            api_key = credentials.get("api_key")

            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            endpoint_url = credentials.get("endpoint_url", "")
            if not endpoint_url.endswith("/"):
                endpoint_url += "/"

            endpoint_url = urljoin(endpoint_url, "embeddings")

            payload = {"input": "ping", "model": model}

            response = requests.post(
                url=endpoint_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=(10, 300),
            )

            if response.status_code != 200:
                raise CredentialsValidateFailedError(
                    f"Credentials validation failed with status code {response.status_code}",
                )

            try:
                json_result = response.json()
            except json.JSONDecodeError as e:
                raise CredentialsValidateFailedError(
                    "Credentials validation failed: JSON decode error"
                ) from e

            if "model" not in json_result:
                raise CredentialsValidateFailedError(
                    "Credentials validation failed: invalid response"
                )
        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex

    def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> AIModelEntity:
        """从凭证生成自定义模型实体

        Args:
            model: 模型名称
            credentials: 模型凭证

        Returns:
            AI模型实体
        """
        entity = AIModelEntity(
            model=model,
            label=I18nObject(en_US=model),
            model_type=ModelType.TEXT_EMBEDDING,
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={
                ModelPropertyKey.CONTEXT_SIZE: int(
                    credentials.get("context_size", 512)
                ),
                ModelPropertyKey.MAX_CHUNKS: 1,
            },
            parameter_rules=[],
            pricing=PriceConfig(
                input=Decimal(credentials.get("input_price", 0)),
                unit=Decimal(credentials.get("unit", 0)),
                currency=credentials.get("currency", "USD"),
            ),
        )

        return entity

    def _calc_response_usage(
        self, model: str, credentials: dict, tokens: int
    ) -> EmbeddingUsage:
        """
        计算响应使用量

        :param model: 模型
        :param credentials: 模型凭证
        :param tokens: 输入token
        :return: 使用量
        """
        # 获取输入价格信息
        input_price_info = self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.INPUT,
            tokens=tokens,
        )

        # 转换使用量
        usage = EmbeddingUsage(
            tokens=tokens,
            total_tokens=tokens,
            unit_price=input_price_info.unit_price,
            price_unit=input_price_info.unit,
            total_price=input_price_info.total_amount,
            currency=input_price_info.currency,
            latency=time.perf_counter() - self.started_at,
        )

        return usage
