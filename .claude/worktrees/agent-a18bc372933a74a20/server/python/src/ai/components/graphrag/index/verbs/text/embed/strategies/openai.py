"""包含 run 方法定义的模块."""

import asyncio
import logging
from typing import Any

import numpy as np
from datashaper import ProgressTicker, VerbCallbacks, progress_ticker

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.llm import load_llm_embeddings
from ai.components.graphrag.index.text_splitting import TokenTextSplitter
from ai.components.graphrag.index.utils import is_null
from ai.components.graphrag.index.verbs.text.embed.strategies.typing import (
    TextEmbeddingResult,
)
from ai.components.graphrag.llm import EmbeddingLLM, OpenAIConfiguration

log = logging.getLogger(__name__)


async def run(
    input: list[str],
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    args: dict[str, Any],
) -> TextEmbeddingResult:
    """
    执行run。

    Args:
        input (list[str]): input 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        cache (PipelineCache): cache 参数。
        args (dict[str, Any]): args 参数。

    Returns:
        处理结果。
    """
    if is_null(input):
        return TextEmbeddingResult(embeddings=None)

    llm_config = args.get("llm", {})
    batch_size = args.get("batch_size", 16)
    batch_max_tokens = args.get("batch_max_tokens", 8191)
    oai_config = OpenAIConfiguration(llm_config)
    splitter = _get_splitter(oai_config, batch_max_tokens)
    llm = _get_llm(oai_config, callbacks, cache)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(args.get("num_threads", 4))

    # Break up the input texts. The sizes here indicate how many snippets are in each input text
    texts, input_sizes = _prepare_embed_texts(input, splitter)
    text_batches = _create_text_batches(
        texts,
        batch_size,
        batch_max_tokens,
        splitter,
    )
    log.info(
        "embedding %d inputs via %d snippets using %d batches. max_batch_size=%d, max_tokens=%d",
        len(input),
        len(texts),
        len(text_batches),
        batch_size,
        batch_max_tokens,
    )
    ticker = progress_ticker(callbacks.progress, len(text_batches))

    # Embed each chunk of snippets
    embeddings = await _execute(llm, text_batches, ticker, semaphore)
    embeddings = _reconstitute_embeddings(embeddings, input_sizes)

    return TextEmbeddingResult(embeddings=embeddings)


def _get_splitter(
    config: OpenAIConfiguration, batch_max_tokens: int
) -> TokenTextSplitter:
    """
    获取splitter。

    Args:
        config (OpenAIConfiguration): config 参数。
        batch_max_tokens (int): batch_max_tokens 参数。

    Returns:
        处理结果。
    """
    return TokenTextSplitter(
        encoding_name=config.encoding_model or defs.ENCODING_MODEL,
        chunk_size=batch_max_tokens,
    )


def _get_llm(
    config: OpenAIConfiguration,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
) -> EmbeddingLLM:
    """
    获取llm。

    Args:
        config (OpenAIConfiguration): config 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        cache (PipelineCache): cache 参数。

    Returns:
        处理结果。
    """
    llm_type = config.lookup("type", "Unknown")
    return load_llm_embeddings(
        "text_embedding",
        llm_type,
        callbacks,
        cache,
        config.raw_config,
    )


async def _execute(
    llm: EmbeddingLLM,
    chunks: list[list[str]],
    tick: ProgressTicker,
    semaphore: asyncio.Semaphore,
) -> list[list[float]]:
    """
    执行execute。

    Args:
        llm (EmbeddingLLM): llm 参数。
        chunks (list[list[str]]): chunks 参数。
        tick (ProgressTicker): tick 参数。
        semaphore (asyncio.Semaphore): semaphore 参数。

    Returns:
        处理结果。
    """

    async def embed(chunk: list[str]):
        """
        嵌入embed。

        Args:
            chunk (list[str]): chunk 参数。

        Returns:
            处理结果。
        """
        async with semaphore:
            chunk_embeddings = await llm(chunk)
            result = np.array(chunk_embeddings.output)
            tick(1)
        return result

    futures = [embed(chunk) for chunk in chunks]
    results = await asyncio.gather(*futures)
    # merge results in a single list of lists (reduce the collect dimension)
    return [item for sublist in results for item in sublist]


def _create_text_batches(
    texts: list[str],
    max_batch_size: int,
    max_batch_tokens: int,
    splitter: TokenTextSplitter,
) -> list[list[str]]:
    """
    创建text_batches。

    Args:
        texts (list[str]): texts 参数。
        max_batch_size (int): max_batch_size 参数。
        max_batch_tokens (int): max_batch_tokens 参数。
        splitter (TokenTextSplitter): splitter 参数。

    Returns:
        处理结果。
    """
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
    # According to this embeddings reference, Azure limits us to 16 concurrent embeddings and 8191 tokens per request
    result = []
    current_batch = []
    current_batch_tokens = 0

    for text in texts:
        token_count = splitter.num_tokens(text)
        if (
            len(current_batch) >= max_batch_size
            or current_batch_tokens + token_count > max_batch_tokens
        ):
            result.append(current_batch)
            current_batch = []
            current_batch_tokens = 0

        current_batch.append(text)
        current_batch_tokens += token_count

    if len(current_batch) > 0:
        result.append(current_batch)

    return result


def _prepare_embed_texts(
    input: list[str], splitter: TokenTextSplitter
) -> tuple[list[str], list[int]]:
    """
    处理prepare_embed_texts。

    Args:
        input (list[str]): input 参数。
        splitter (TokenTextSplitter): splitter 参数。

    Returns:
        处理结果。
    """
    sizes: list[int] = []
    snippets: list[str] = []

    for text in input:
        # Split the input text and filter out any empty content
        split_texts = splitter.split_text(text)
        if split_texts is None:
            continue
        split_texts = [text for text in split_texts if len(text) > 0]

        sizes.append(len(split_texts))
        snippets.extend(split_texts)

    return snippets, sizes


def _reconstitute_embeddings(
    raw_embeddings: list[list[float]], sizes: list[int]
) -> list[list[float] | None]:
    """
    处理reconstitute_embeddings。

    Args:
        raw_embeddings (list[list[float]]): raw_embeddings 参数。
        sizes (list[int]): sizes 参数。

    Returns:
        处理结果。
    """
    embeddings: list[list[float] | None] = []
    cursor = 0
    for size in sizes:
        if size == 0:
            embeddings.append(None)
        elif size == 1:
            embedding = raw_embeddings[cursor]
            embeddings.append(embedding)
            cursor += 1
        else:
            chunk = raw_embeddings[cursor : cursor + size]
            average = np.average(chunk, axis=0)
            normalized = average / np.linalg.norm(average)
            embeddings.append(normalized.tolist())
            cursor += size
    return embeddings
