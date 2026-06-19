"""
文本嵌入服务
提供所有文本嵌入相关功能的统一接口
"""

import hashlib
from collections import OrderedDict
from decimal import Decimal
from threading import RLock

from loguru import logger

from ai.components.model.internal.model_instance_factory import (
    ModelInstance,
    ModelInstanceFactory,
)
from ai.components.model.services.base_model_service import BaseModelService
from ai_plugin.sdk.entities.model import ModelType
from ai_plugin.sdk.entities.model.text_embedding import (
    EmbeddingUsage,
    TextEmbeddingResult,
)


class EmbeddingService(BaseModelService):
    """
    文本嵌入服务类

    封装所有文本嵌入相关的操作，提供简洁易用的接口
    """

    # 全局LRU缓存与锁（跨实例共享）：key -> embedding 向量（类级共享）
    # key 由 (model, provider, text) 计算的哈希组成，避免存储大文本键
    _embedding_cache: OrderedDict[str, list[float]] = OrderedDict()
    _cache_lock: RLock = RLock()

    def __init__(
        self,
        tenant_id: str,
        cache_enabled: bool = True,
        cache_size: int = 2000,
        log_cache_details: bool = False,
    ):
        """

        :param tenant_id: 租户 ID
        :param cache_enabled: 是否启用缓存
        :param cache_size: 最大缓存条目数
        :param log_cache_details: 是否打印缓存命中/未命中详单
        """
        super().__init__(tenant_id)
        self._logger = logger.bind(name=__name__)

        self._cache_enabled: bool = cache_enabled
        # 最大缓存条目数：可按需调整，注意内存占用（每条约几KB~十几KB，取决于维度）
        self._max_cache_size: int = cache_size
        self._log_cache_details_enabled: bool = log_cache_details

    def _make_cache_key(self, text: str, model: str, provider: str) -> str:
        """
        根据文本、模型名和提供商生成稳定哈希key

        :param text: 待嵌入的文本
        :param model: 模型名称
        :param provider: 提供商名称
        :return: 缓存键
        """
        h = hashlib.sha1()
        # 使用不可见分隔符，避免拼接歧义
        compound = f"{provider}\u241f{model}\u241f{text}".encode()
        h.update(compound)
        return h.hexdigest()

    def _cache_get(self, key: str) -> list[float] | None:
        """
        从缓存中获取向量

        :param key: 缓存键
        :return: 嵌入向量或None
        """
        if not self._cache_enabled:
            return None

        with self._cache_lock:
            if key in self._embedding_cache:
                # LRU: 命中后移动到队尾
                self._embedding_cache.move_to_end(key)
                return self._embedding_cache[key]
            return None

    def _cache_set(self, key: str, value: list[float]) -> None:
        """
        设置缓存值

        :param key: 缓存键
        :param value: 嵌入向量
        """
        if not self._cache_enabled:
            return

        with self._cache_lock:
            self._embedding_cache[key] = value
            self._embedding_cache.move_to_end(key)
            # 超限弹出最旧项
            if len(self._embedding_cache) > self._max_cache_size:
                self._embedding_cache.popitem(last=False)

    def _split_hits_misses(
        self,
        texts: list[str],
        model: str,
        provider: str,
    ) -> tuple[dict[int, list[float]], dict[str, list[int]]]:
        """
        将输入分为命中与未命中：
        - 返回 hits: {index -> embedding}
        - 返回 misses: {miss_key -> [indices]}
        同一批次中的重复文本仅计算一次

        :param texts: 文本列表
        :param model: 模型名称
        :param provider: 提供商名称
        :return: (命中的索引->向量映射, 未命中的键->索引列表映射)
        """
        hits: dict[int, list[float]] = {}
        misses: dict[str, list[int]] = {}

        for idx, text in enumerate(texts):
            key = self._make_cache_key(text, model, provider)
            cached = self._cache_get(key)
            if cached is not None:
                hits[idx] = cached
            else:
                misses.setdefault(key, []).append(idx)

        return hits, misses

    def _log_cache_details(
        self,
        texts: list[str],
        hits: dict[int, list[float]],
        misses: dict[str, list[int]],
        prefix: str = "",
    ) -> None:
        """打印缓存命中/未命中详单（每条文本≤1000字符）。

        - 每条文本单独限制长度至1000字符；不再限制整条日志的累计长度，仅保留索引次序。
        - 仅用于排查缓存问题，生产建议降低日志级别或通过配置关闭。
        """
        try:
            if not self._log_cache_details_enabled:
                return

            def sanitize_and_truncate(raw_text: str, max_chars: int = 1000) -> str:
                # 清理控制字符，并做长度限制
                preview = (
                    raw_text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
                )
                if len(preview) > max_chars:
                    preview = preview[:max_chars] + "…"
                return preview

            def build_preview(indices: list[int]) -> str:
                parts: list[str] = []
                for idx in indices:
                    # 文本预览：去除换行/制表，并限制长度
                    raw = texts[idx] if 0 <= idx < len(texts) else "<idx out of range>"
                    preview = sanitize_and_truncate(raw, 1000)
                    piece = f"\n[{idx}] [{preview}]"
                    parts.append(piece)
                return "; ".join(parts)

            # 命中索引（按升序）
            hit_indices = sorted(hits.keys())
            hits_str = build_preview(hit_indices)
            if hits_str:
                self._logger.info("%s缓存命中详单: %s", prefix, hits_str)
            else:
                self._logger.info("%s缓存命中详单: <空>", prefix)

            # 未命中索引（按输入出现顺序去重）
            seen = set()
            miss_indices: list[int] = []
            for _, idx_list in misses.items():
                for i in idx_list:
                    if i not in seen:
                        seen.add(i)
                        miss_indices.append(i)
            misses_str = build_preview(miss_indices)
            if misses_str:
                self._logger.info("%s未命中详单: %s", prefix, misses_str)
            else:
                self._logger.info("%s未命中详单: <空>", prefix)
        except Exception:
            # 仅日志构建失败时吞掉异常，避免影响主流程
            self._logger.exception("构建缓存命中/未命中详单日志失败")

    async def embed(
        self,
        text: str,
        model: str | None = None,
        provider: str | None = None,
        user: str | None = None,
    ) -> list[float]:
        """
        单文本嵌入接口

        :param text: 待嵌入的文本
        :param model: 模型名称（可选）
        :param provider: 供应商名称（可选）
        :param input_type: 输入类型
        :param user: 用户ID
        :return: 嵌入向量
        """

        result = await self.batch_embed(
            texts=[text], model=model, provider=provider, user=user
        )
        return result.embeddings[0] if result.embeddings else []

    async def batch_embed(
        self,
        texts: list[str],
        model: str | None = None,
        provider: str | None = None,
        user: str | None = None,
    ) -> TextEmbeddingResult:
        """
        批量文本嵌入接口

        :param texts: 待嵌入的文本列表
        :param model: 模型名称（可选）
        :param provider: 供应商名称（可选）
        :param user: 用户ID
        :return: 嵌入结果
        """
        if not texts or len(texts) == 0:
            self._logger.info("batch_embed: 文本数为0，直接返回空结果")
            usage = EmbeddingUsage(
                tokens=0,
                total_tokens=0,
                unit_price=Decimal(0),
                price_unit=Decimal(0),
                total_price=Decimal(0),
                currency="CNY",
                latency=0,
            )
            return TextEmbeddingResult(model=model, embeddings=[], usage=usage)

        if not provider or not model:
            provider, model = await self._resolve_default_model(
                ModelType.TEXT_EMBEDDING
            )

        self._logger.info(
            f"开始批量向量化: 模型={model}, 提供商={provider}, 文本数={len(texts)}, 缓存启用={self._cache_enabled}",
        )

        # 命中/未命中划分
        hits, misses = self._split_hits_misses(texts, model, provider)

        hit_count = len(hits)
        miss_count = sum(len(v) for v in misses.values())
        self._logger.debug(f"缓存命中={hit_count}, 未命中={miss_count}")

        # 打印命中/未命中详单
        self._log_cache_details(texts, hits, misses, prefix="")

        # 需要实际计算的唯一文本（按miss key聚合）
        unique_miss_texts: list[str] = []
        miss_keys_in_order: list[str] = []
        seen: set[str] = set()

        for miss_key, indices in misses.items():
            if miss_key in seen:
                continue
            seen.add(miss_key)
            # 取第一个出现该key的文本内容
            first_index = indices[0]
            unique_miss_texts.append(texts[first_index])
            miss_keys_in_order.append(miss_key)

        self._logger.debug(f"未命中去重后需计算={len(unique_miss_texts)}")

        usage = None
        # 计算未命中部分
        if len(unique_miss_texts) > 0:
            modelInstance: ModelInstance = await self._factory.get_model_instance(
                self._tenant_id,
                provider,
                model_type=ModelType.TEXT_EMBEDDING,
                model=model,
            )

            result = await modelInstance.invoke_text_embedding(
                texts=unique_miss_texts,
                user=user,
            )

            usage = result.usage
            computed_vectors = result.embeddings

            if len(computed_vectors) != len(unique_miss_texts):
                raise RuntimeError(
                    f"向量返回数量与输入不一致，请检查向量模型是否正常，当前模型：{model}"
                )

            # 写回缓存，并分发到所有对应索引
            for miss_key, vector in zip(miss_keys_in_order, computed_vectors):
                self._cache_set(miss_key, vector)
                for idx in misses.get(miss_key, []):
                    hits[idx] = vector

            self._logger.info(f"已计算向量={len(unique_miss_texts)}，缓存已写入")

        # 按原顺序组装
        try:
            result_embeddings: list[list[float]] = [hits[i] for i in range(len(texts))]
        except KeyError:
            raise RuntimeError("存在未填充的向量结果")

        self._logger.info(
            f"批量向量化完成: 返回向量数={len(result_embeddings)}, 缓存命中={hit_count}, 未命中={miss_count}",
        )

        if usage is None:
            usage = EmbeddingUsage(
                tokens=0,
                total_tokens=0,
                unit_price=Decimal(0),
                price_unit=Decimal(0),
                total_price=Decimal(0),
                currency="RMB",
                latency=0,
            )

        return TextEmbeddingResult(
            model=model, embeddings=result_embeddings, usage=usage
        )

    async def tokens(
        self,
        texts: list[str],
        model: str | None = None,
        provider: str | None = None,
    ) -> list[int]:
        """
        计算文本嵌入的token数量

        :param texts: 待嵌入的文本列表
        :param model: 模型名称（可选）
        :param provider: 供应商名称（可选）
        :return: 每个文本的token数量列表
        """

        if not provider or not model:
            provider, model = await self._resolve_default_model(
                ModelType.TEXT_EMBEDDING
            )

        modelInstance: ModelInstance = await self._factory.get_model_instance(
            self._tenant_id,
            provider,
            model_type=ModelType.TEXT_EMBEDDING,
            model=model,
        )

        result = await modelInstance.get_text_embedding_num_tokens(
            texts=texts,
        )

        return result
