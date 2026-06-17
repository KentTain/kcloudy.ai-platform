"""包含'GraphExtractionResult'和'GraphExtractor'模型的模块."""

import logging
import numbers
import re
import traceback
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import networkx as nx
import tiktoken

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.index.graph.extractors.graph.prompts import (
    CONTINUE_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    LOOP_PROMPT,
)
from ai.components.graphrag.index.typing import ErrorHandlerFn
from ai.components.graphrag.index.utils import clean_str
from ai.components.graphrag.llm import CompletionLLM

DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"
DEFAULT_ENTITY_TYPES = ["组织", "人物", "地点", "事件"]


@dataclass
class GraphExtractionResult:
    """单分图提取结果类定义."""

    output: nx.Graph
    source_docs: dict[Any, Any]


class GraphExtractor:
    """单分图提取器类定义."""

    _llm: CompletionLLM
    _join_descriptions: bool
    _tuple_delimiter_key: str
    _record_delimiter_key: str
    _entity_types_key: str
    _input_text_key: str
    _completion_delimiter_key: str
    _entity_name_key: str
    _input_descriptions_key: str
    _extraction_prompt: str
    _summarization_prompt: str
    _loop_args: dict[str, Any]
    _max_gleanings: int
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        tuple_delimiter_key: str | None = None,
        record_delimiter_key: str | None = None,
        input_text_key: str | None = None,
        entity_types_key: str | None = None,
        completion_delimiter_key: str | None = None,
        prompt: str | None = None,
        join_descriptions=True,
        encoding_model: str | None = None,
        max_gleanings: int | None = None,
        on_error: ErrorHandlerFn | None = None,
    ):
        """初始化方法定义."""
        # TODO: 简化构造
        self._llm = llm_invoker
        self._join_descriptions = join_descriptions
        self._input_text_key = input_text_key or "input_text"
        self._tuple_delimiter_key = tuple_delimiter_key or "tuple_delimiter"
        self._record_delimiter_key = record_delimiter_key or "record_delimiter"
        self._completion_delimiter_key = (
            completion_delimiter_key or "completion_delimiter"
        )
        self._entity_types_key = entity_types_key or "entity_types"
        self._extraction_prompt = prompt or GRAPH_EXTRACTION_PROMPT
        self._max_gleanings = (
            max_gleanings
            if max_gleanings is not None
            else defs.ENTITY_EXTRACTION_MAX_GLEANINGS
        )
        self._on_error = on_error or (lambda _e, _s, _d: None)

        # 构造循环参数
        encoding = tiktoken.get_encoding(encoding_model or "cl100k_base")
        yes = encoding.encode("YES")
        no = encoding.encode("NO")
        self._loop_args = {"logit_bias": {yes[0]: 100, no[0]: 100}, "max_tokens": 1}

    async def __call__(
        self, texts: list[str], prompt_variables: dict[str, Any] | None = None
    ) -> GraphExtractionResult:
        """调用方法定义."""
        if prompt_variables is None:
            prompt_variables = {}
        all_records: dict[int, str] = {}
        source_doc_map: dict[int, str] = {}

        # 将默认值连接到提示变量中
        prompt_variables = {
            **prompt_variables,
            self._tuple_delimiter_key: prompt_variables.get(self._tuple_delimiter_key)
            or DEFAULT_TUPLE_DELIMITER,
            self._record_delimiter_key: prompt_variables.get(self._record_delimiter_key)
            or DEFAULT_RECORD_DELIMITER,
            self._completion_delimiter_key: prompt_variables.get(
                self._completion_delimiter_key
            )
            or DEFAULT_COMPLETION_DELIMITER,
            self._entity_types_key: ",".join(
                prompt_variables.get(self._entity_types_key) or DEFAULT_ENTITY_TYPES
            ),
        }

        for doc_index, text in enumerate(texts):
            try:
                # 调用实体提取
                result = await self._process_document(text, prompt_variables)
                source_doc_map[doc_index] = text
                all_records[doc_index] = result
            except Exception as e:
                logging.exception("error extracting graph")
                self._on_error(
                    e,
                    traceback.format_exc(),
                    {
                        "doc_index": doc_index,
                        "text": text,
                    },
                )

        output = await self._process_results(
            all_records,
            prompt_variables.get(self._tuple_delimiter_key, DEFAULT_TUPLE_DELIMITER),
            prompt_variables.get(self._record_delimiter_key, DEFAULT_RECORD_DELIMITER),
        )

        return GraphExtractionResult(
            output=output,
            source_docs=source_doc_map,
        )

    async def _process_document(
        self, text: str, prompt_variables: dict[str, str]
    ) -> str:
        """
        处理process_document。

        Args:
            text (str): text 参数。
            prompt_variables (dict[str, str]): prompt_variables 参数。

        Returns:
            处理结果。
        """
        response = await self._llm(
            self._extraction_prompt,
            variables={
                **prompt_variables,
                self._input_text_key: text,
            },
        )
        results = response.output or ""

        # 重复以确保最大化实体数量
        for i in range(self._max_gleanings):
            response = await self._llm(
                CONTINUE_PROMPT,
                name=f"extract-continuation-{i}",
                history=response.history,
            )
            results += response.output or ""

            # 如果这是最后一次收集,不要更新继续标志
            if i >= self._max_gleanings - 1:
                break

            response = await self._llm(
                LOOP_PROMPT,
                name=f"extract-loopcheck-{i}",
                history=response.history,
                model_parameters=self._loop_args,
            )
            if response.output != "YES":
                break

        return results

    async def _process_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str,
        record_delimiter: str,
    ) -> nx.Graph:
        """
        处理process_results。

        Args:
            results (dict[int, str]): results 参数。
            tuple_delimiter (str): tuple_delimiter 参数。
            record_delimiter (str): record_delimiter 参数。

        Returns:
            处理结果。
        """
        graph = nx.Graph()
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # 将此记录作为节点添加到图中
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list(
                                    {
                                        *_unpack_descriptions(node),
                                        entity_description,
                                    }
                                )
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list(
                                {
                                    *_unpack_source_ids(node),
                                    str(source_doc_id),
                                }
                            )
                        )
                        node["entity_type"] = (
                            entity_type if entity_type != "" else node["entity_type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if record_attributes[0] == '"relationship"':
                    # 兼容两种格式:
                    # 新格式 (5字段): ("relationship"<|><source><|><target><|><relationship_type><|><description><|><weight>)
                    # 旧格式 (4字段): ("relationship"<|><source><|><target><|><description><|><weight>)
                    if len(record_attributes) >= 6:
                        # 新格式: 包含 relationship_type
                        source = clean_str(record_attributes[1].upper())
                        target = clean_str(record_attributes[2].upper())
                        edge_type = clean_str(record_attributes[3])
                        edge_description = clean_str(record_attributes[4])
                    elif len(record_attributes) >= 5:
                        # 旧格式: 无 relationship_type
                        source = clean_str(record_attributes[1].upper())
                        target = clean_str(record_attributes[2].upper())
                        edge_type = ""
                        edge_description = clean_str(record_attributes[3])
                    else:
                        continue  # 格式错误，跳过此记录

                    edge_source_id = clean_str(str(source_doc_id))
                    weight = (
                        float(record_attributes[-1])
                        if isinstance(record_attributes[-1], numbers.Number)
                        else 1.0
                    )
                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data is not None:
                            weight += edge_data["weight"]
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list(
                                        {
                                            *_unpack_descriptions(edge_data),
                                            edge_description,
                                        }
                                    )
                                )
                            edge_source_id = ", ".join(
                                list(
                                    {
                                        *_unpack_source_ids(edge_data),
                                        str(source_doc_id),
                                    }
                                )
                            )
                    graph.add_edge(
                        source,
                        target,
                        weight=weight,
                        type=edge_type,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph


def _unpack_descriptions(data: Mapping) -> list[str]:
    """
    处理unpack_descriptions。

    Args:
        data (Mapping): data 参数。

    Returns:
        处理结果。
    """
    value = data.get("description", None)
    return [] if value is None else value.split("\n")


def _unpack_source_ids(data: Mapping) -> list[str]:
    """
    处理unpack_source_ids。

    Args:
        data (Mapping): data 参数。

    Returns:
        处理结果。
    """
    value = data.get("source_id", None)
    return [] if value is None else value.split(", ")
