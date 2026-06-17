"""包含 the summarize_descriptions verb."""

import asyncio
import logging
from enum import Enum
from typing import Any, NamedTuple, cast

import networkx as nx
import pandas as pd
from datashaper import (
    ProgressTicker,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    progress_ticker,
    verb,
)

from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.utils import load_graph

from .strategies.typing import SummarizationStrategy

log = logging.getLogger(__name__)


class DescriptionSummarizeRow(NamedTuple):
    """DescriptionSummarizeRow 类定义."""

    graph: Any


class SummarizeStrategyType(str, Enum):
    """SummarizeStrategyType 类定义."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """
        实现 __repr__ 协议方法。

        Returns:
            处理结果。
        """
        return f'"{self.value}"'


@verb(name="summarize_descriptions")
async def summarize_descriptions(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    to: str,
    strategy: dict[str, Any] | None = None,
    **kwargs,
) -> TableContainer:
    """
    摘要summarize_descriptions。

    Args:
        input (VerbInput): input 参数。
        cache (PipelineCache): cache 参数。
        callbacks (VerbCallbacks): callbacks 参数。
        column (str): column 参数。
        to (str): to 参数。
        strategy (dict[str, Any] | None): strategy 参数。
        kwargs: kwargs 参数。

    Returns:
        处理结果。
    """
    log.debug("summarize_descriptions strategy=%s", strategy)
    output = cast("pd.DataFrame", input.get_input())
    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", SummarizeStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    async def get_resolved_entities(row, semaphore: asyncio.Semaphore):
        """
        获取resolved_entities。

        Args:
            row: row 参数。
            semaphore (asyncio.Semaphore): semaphore 参数。

        Returns:
            处理结果。
        """
        graph: nx.Graph = load_graph(cast("str | nx.Graph", getattr(row, column)))

        ticker_length = len(graph.nodes) + len(graph.edges)

        ticker = progress_ticker(callbacks.progress, ticker_length)

        futures = [
            do_summarize_descriptions(
                node,
                sorted(set(graph.nodes[node].get("description", "").split("\n"))),
                ticker,
                semaphore,
            )
            for node in graph.nodes()
        ]
        futures += [
            do_summarize_descriptions(
                edge,
                sorted(set(graph.edges[edge].get("description", "").split("\n"))),
                ticker,
                semaphore,
            )
            for edge in graph.edges()
        ]

        results = await asyncio.gather(*futures)

        for result in results:
            graph_item = result.items
            if isinstance(graph_item, str) and graph_item in graph.nodes():
                graph.nodes[graph_item]["description"] = result.description
            elif isinstance(graph_item, tuple) and graph_item in graph.edges():
                graph.edges[graph_item]["description"] = result.description

        return DescriptionSummarizeRow(
            graph="\n".join(nx.generate_graphml(graph)),
        )

    async def do_summarize_descriptions(
        graph_item: str | tuple[str, str],
        descriptions: list[str],
        ticker: ProgressTicker,
        semaphore: asyncio.Semaphore,
    ):
        """
        处理summarize_descriptions。

        Args:
            graph_item (str | tuple[str, str]): graph_item 参数。
            descriptions (list[str]): descriptions 参数。
            ticker (ProgressTicker): ticker 参数。
            semaphore (asyncio.Semaphore): semaphore 参数。

        Returns:
            处理结果。
        """
        async with semaphore:
            results = await strategy_exec(
                graph_item,
                descriptions,
                callbacks,
                cache,
                strategy_config,
            )
            ticker(1)
        return results

    # Graph is always on row 0, so here a derive from rows does not work
    # This iteration will only happen once, but avoids hardcoding a iloc[0]
    # Since parallelization is at graph level (nodes and edges), we can't use
    # the parallelization of the derive_from_rows
    semaphore = asyncio.Semaphore(kwargs.get("num_threads", 4))

    results = [
        await get_resolved_entities(row, semaphore) for row in output.itertuples()
    ]

    to_result = []

    for result in results:
        if result:
            to_result.append(result.graph)
        else:
            to_result.append(None)
    output[to] = to_result
    return TableContainer(table=output)


def load_strategy(strategy_type: SummarizeStrategyType) -> SummarizationStrategy:
    """
    加载load_strategy。

    Args:
        strategy_type (SummarizeStrategyType): strategy_type 参数。

    Returns:
        处理结果。
    """
    match strategy_type:
        case SummarizeStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run as run_gi

            return run_gi
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
