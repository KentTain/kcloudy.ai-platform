"""包含 entity_extract 方法的模块."""

import logging
from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    verb,
)

from ai.components.graphrag.index.bootstrap import bootstrap
from ai.components.graphrag.index.cache import PipelineCache

from .strategies.typing import Document, EntityExtractStrategy

log = logging.getLogger(__name__)


class ExtractEntityStrategyType(str, Enum):
    """ExtractEntityStrategyType 类定义."""

    graph_intelligence = "graph_intelligence"
    graph_intelligence_json = "graph_intelligence_json"
    nltk = "nltk"

    def __repr__(self):
        """获取字符串表示."""
        return f'"{self.value}"'


DEFAULT_ENTITY_TYPES = ["组织", "人物", "地点", "事件"]


@verb(name="entity_extract")
async def entity_extract(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    id_column: str,
    to: str,
    strategy: dict[str, Any] | None,
    graph_to: str | None = None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types=DEFAULT_ENTITY_TYPES,
    **kwargs,
) -> TableContainer:
    """
    从文本片段中提取实体。

    ## 用法
    ### json
    ```json
    {
        "verb": "entity_extract",
        "args": {
            "column": "the_document_text_column_to_extract_entities_from", /* 通常这将是您的文档文本列 */
            "id_column": "the_column_with_the_unique_id_for_each_row", /* 通常这将是您的文档 ID */
            "to": "the_column_to_output_the_entities_to", /* 这将是一个 list[dict[str, Any]],包含实体列表,每个实体有名称和附加属性 */
            "graph_to": "the_column_to_output_the_graphml_to", /* 可选:这将是一个 graphml 格式的字符串,表示实体及其关系 */
            "strategy": {...} <strategy_config>, 参见下面的策略部分
            "entity_types": ["list", "of", "entity", "types", "to", "extract"] /* 可选:限制提取的实体类型,默认: ["organization", "person", "geo", "event"] */
            "summarize_descriptions" : true | false /* 可选:是否总结实体和关系的描述,默认: true */
        }
    }
    ```
    ### yaml
    ```yaml
    verb: entity_extract
    args:
        column: the_document_text_column_to_extract_entities_from
        id_column: the_column_with_the_unique_id_for_each_row
        to: the_column_to_output_the_entities_to
        graph_to: the_column_to_output_the_graphml_to
        strategy: <strategy_config>, 参见下面的策略部分
        summarize_descriptions: true | false /* 可选:是否总结实体和关系的描述,默认: true */
        entity_types:
            - list
            - of
            - entity
            - types
            - to
            - extract
    ```

    ## 策略
    entity extract verb 使用策略从文档中提取实体。策略是一个 json 对象,定义要使用的策略。可用的策略如下:

    ### graph_intelligence
    此策略使用 [graph_intelligence] 库从文档中提取实体。特别是使用 LLM 从文本片段中提取实体。策略配置如下:

    ```yml
    strategy:
        type: graph_intelligence
        extraction_prompt: !include ./entity_extraction_prompt.txt # 可选,用于提取的提示
        completion_delimiter: "<|COMPLETE|>" # 可选,LLM 用于标记完成的分隔符
        tuple_delimiter: "<|>" # 可选,LLM 用于标记元组的分隔符
        record_delimiter: "##" # 可选,LLM 用于标记记录的分隔符

        prechunked: true | false # 可选,文档是否已预先分块,否则将文档分块为较小的部分。默认: false
        encoding_name: cl100k_base # 可选,LLM 使用的编码,如果尚未预先分块,默认: cl100k_base
        chunk_size: 1000 # 可选,LLM 使用的分块大小,如果尚未预先分块,默认: 1200
        chunk_overlap: 100 # 可选,LLM 使用的分块重叠,如果尚未预先分块,默认: 100

        llm: # LLM 的配置
            type: openai # 要使用的 LLM 类型,可用选项为: openai, azure, openai_chat, azure_openai_chat。最后两个是基于聊天的 LLM。
            api_key: !ENV ${GRAPHRAG_OPENAI_API_KEY} # openai 使用的 API 密钥
            model: !ENV ${GRAPHRAG_OPENAI_MODEL:gpt-4-turbo-preview} # openai 使用的模型
            max_tokens: !ENV ${GRAPHRAG_MAX_TOKENS:6000} # openai 使用的最大 token 数
            organization: !ENV ${GRAPHRAG_OPENAI_ORGANIZATION} # openai 使用的组织

            # 如果使用 azure 版本
            api_base: !ENV ${GRAPHRAG_OPENAI_API_BASE} # azure 使用的 API 基础地址
            api_version: !ENV ${GRAPHRAG_OPENAI_API_VERSION} # azure 使用的 API 版本
            proxy: !ENV ${GRAPHRAG_OPENAI_PROXY} # azure 使用的代理

    ```

    ### nltk
    此策略使用 [nltk] 库从文档中提取实体。特别是使用 nltk 从文本片段中提取实体。策略配置如下:
    ```yml
    strategy:
        type: nltk
    ```
    """
    log.debug("entity_extract strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES
    output = cast("pd.DataFrame", input.get_input())
    strategy = strategy or {}
    strategy_exec = _load_strategy(
        strategy.get("type", ExtractEntityStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    num_started = 0

    async def run_strategy(row):
        """
        执行strategy。

        Args:
            row: row 参数。

        Returns:
            处理结果。
        """
        nonlocal num_started
        text = row[column]
        id = row[id_column]
        result = await strategy_exec(
            [Document(text=text, id=id)],
            entity_types,
            callbacks,
            cache,
            strategy_config,
        )
        num_started += 1
        return [result.entities, result.graphml_graph]

    results = await derive_from_rows(
        output,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )

    to_result = []
    graph_to_result = []
    for result in results:
        if result:
            to_result.append(result[0])
            graph_to_result.append(result[1])
        else:
            to_result.append(None)
            graph_to_result.append(None)

    output[to] = to_result
    if graph_to is not None:
        output[graph_to] = graph_to_result

    return TableContainer(table=output.reset_index(drop=True))


def _load_strategy(strategy_type: ExtractEntityStrategyType) -> EntityExtractStrategy:
    """加载策略方法定义."""
    match strategy_type:
        case ExtractEntityStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run_gi

            return run_gi

        case ExtractEntityStrategyType.nltk:
            bootstrap()
            # 动态导入 nltk 策略以避免在未使用时产生依赖
            from .strategies.nltk import run as run_nltk

            return run_nltk
        case _:
            msg = f"未知策略: {strategy_type}"
            raise ValueError(msg)
