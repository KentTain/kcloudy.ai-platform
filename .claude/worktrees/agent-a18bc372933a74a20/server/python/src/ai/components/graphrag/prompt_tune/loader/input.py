"""输入加载模块。

Input loading module.
"""

from typing import cast

import numpy as np
import pandas as pd
from datashaper import NoopVerbCallbacks, TableContainer, VerbInput

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.config.models.graph_rag_config import GraphRagConfig
from ai.components.graphrag.index.input import load_input
from ai.components.graphrag.index.llm import load_llm_embeddings
from ai.components.graphrag.index.progress.types import ProgressReporter
from ai.components.graphrag.index.verbs import chunk
from ai.components.graphrag.llm.types.llm_types import EmbeddingLLM
from ai.components.graphrag.prompt_tune.types import DocSelectionType

# 最小文档块重叠大小(token 数)
# Minimum chunk overlap size (in tokens)
MIN_CHUNK_OVERLAP = 0

# 最小文档块大小(token 数)
# Minimum chunk size (in tokens)
MIN_CHUNK_SIZE = 200

# 使用自动选择方法时的最大子集数量
# Maximum subset size when using auto selection method
N_SUBSET_MAX = 300

# 使用自动选择方法时每个聚类中心选择的文档数
# Number of documents to select from each centroid when using auto selection method
K = 15


async def _embed_chunks(
    text_chunks: pd.DataFrame,
    embedding_llm: EmbeddingLLM,
    n_subset_max: int = N_SUBSET_MAX,
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    将文本块转换为稠密的文本嵌入向量。

    从文本块中随机采样(最多 n_subset_max 个),然后使用 LLM 生成嵌入向量。

    Convert text chunks into dense text embeddings.

    参数 Parameters
    ----------
    - text_chunks: 包含文本块的 DataFrame,需要有 "chunks" 列。DataFrame containing text chunks.
    - embedding_llm: 用于生成嵌入的 LLM。The embedding LLM.
    - n_subset_max: 要嵌入的最大文本块数。默认:300。Maximum number of text chunks to embed.

    返回 Returns
    -------
    tuple[pd.DataFrame, np.ndarray]: 返回原始 DataFrame 和嵌入向量数组。
    tuple[pd.DataFrame, np.ndarray]: Returns the original DataFrame and embeddings array.
    """
    sampled_text_chunks = text_chunks.sample(n=min(n_subset_max, len(text_chunks)))
    embeddings = await embedding_llm(sampled_text_chunks["chunks"].tolist())
    return text_chunks, np.array(embeddings.output)


def _sample_chunks_from_embeddings(
    text_chunks: pd.DataFrame,
    embeddings,
    k: int = K,
) -> pd.DataFrame:
    """
    从嵌入向量中采样文本块。

    计算所有嵌入向量的中心点,然后选择距离中心最近的 k 个文本块。

    Sample text chunks from embeddings.

    参数 Parameters
    ----------
    - text_chunks: 包含文本块的 DataFrame。DataFrame containing text chunks.
    - embeddings: 嵌入向量数组。Embeddings array.
    - k: 要选择的文本块数量。默认:15。Number of chunks to select.

    返回 Returns
    -------
    pd.DataFrame: 采样后的文本块 DataFrame。Sampled text chunks DataFrame.
    """
    # 计算嵌入向量的中心点
    # Calculate the center of embeddings
    center = np.mean(embeddings, axis=0)

    # 计算每个嵌入向量到中心的距离
    # Calculate distances from embeddings to center
    distances = np.linalg.norm(embeddings - center, axis=1)

    # 选择距离最近的 k 个索引
    # Select k nearest indices
    nearest_indices = np.argsort(distances)[:k]

    return text_chunks.iloc[nearest_indices]


async def load_docs_in_chunks(
    root: str,
    config: GraphRagConfig,
    select_method: DocSelectionType,
    limit: int,
    reporter: ProgressReporter,
    chunk_size: int = MIN_CHUNK_SIZE,
    n_subset_max: int = N_SUBSET_MAX,
    k: int = K,
) -> list[str]:
    """
    以分块形式加载文档用于生成提示词。

    根据选择方法(TOP/RANDOM/AUTO)从输入数据中选择文档块。

    Load docs into chunks for generating prompts.

    参数 Parameters
    ----------
    - root: 数据根目录。Root directory.
    - config: GraphRAG 配置对象。GraphRAG configuration.
    - select_method: 文档选择方法(TOP/RANDOM/AUTO)。Document selection method.
    - limit: 要选择的文档块数量限制。Limit of chunks to select.
    - reporter: 进度报告器。Progress reporter.
    - chunk_size: 分块大小(token 数)。默认:200。Chunk size in tokens.
    - n_subset_max: 使用自动选择时的最大子集数量。默认:300。Maximum subset size for auto selection.
    - k: 使用自动选择时每个聚类中心选择的文档数。默认:15。Number of documents per centroid for auto selection.

    返回 Returns
    -------
    list[str]: 文档块文本列表。List of document chunk texts.
    """
    # 加载输入数据集
    # Load input dataset
    dataset = await load_input(config.input, reporter, root)

    # 转换为文本单元
    # Convert to text units
    input = VerbInput(input=TableContainer(table=dataset))
    chunk_strategy = config.chunks.resolved_strategy(defs.ENCODING_MODEL)

    # 使用较小的块大小,避免生成过大的提示词
    # Use smaller chunks to avoid huge prompts
    chunk_strategy["chunk_size"] = chunk_size
    chunk_strategy["chunk_overlap"] = MIN_CHUNK_OVERLAP

    dataset_chunks_table_container = chunk(
        input,
        column="text",
        to="chunks",
        callbacks=NoopVerbCallbacks(),
        strategy=chunk_strategy,
    )

    dataset_chunks = cast("pd.DataFrame", dataset_chunks_table_container.table)

    # 选择块到新的 DataFrame 并展开
    # Select chunks into a new DataFrame and explode it
    chunks_df = pd.DataFrame(dataset_chunks["chunks"].explode())  # type: ignore

    # 根据选择方法构建数据集
    # Build dataset based on selection method
    if limit <= 0 or limit > len(chunks_df):
        limit = len(chunks_df)

    if select_method == DocSelectionType.TOP:
        # 选择前 limit 个块
        # Select top limit chunks
        chunks_df = chunks_df[:limit]
    elif select_method == DocSelectionType.RANDOM:
        # 随机选择 limit 个块
        # Randomly select limit chunks
        chunks_df = chunks_df.sample(n=limit)
    elif select_method == DocSelectionType.AUTO:
        # 自动选择:基于嵌入向量的聚类中心选择
        # Auto selection: select based on embedding cluster centroids
        if k is None or k <= 0:
            msg = "k must be an integer > 0"
            raise ValueError(msg)
        embedding_llm = load_llm_embeddings(
            name="prompt_tuning_embeddings",
            llm_type=config.embeddings.resolved_strategy()["llm"]["type"],
            callbacks=NoopVerbCallbacks(),
            cache=None,
            llm_config=config.embeddings.resolved_strategy()["llm"],
        )

        chunks_df, embeddings = await _embed_chunks(
            chunks_df, embedding_llm, n_subset_max=n_subset_max
        )
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # 将数据集转换为列表形式,得到文档列表
    # Convert the dataset to list form, so we have a list of documents
    return chunks_df["chunks"].tolist()
