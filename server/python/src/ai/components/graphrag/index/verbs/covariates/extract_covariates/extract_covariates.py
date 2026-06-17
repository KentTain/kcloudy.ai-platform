"""包含 extract_covariates verb 定义的模块."""

import logging
from dataclasses import asdict
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

from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.verbs.covariates.typing import (
    Covariate,
    CovariateExtractStrategy,
)

log = logging.getLogger(__name__)


class ExtractClaimsStrategyType(str, Enum):
    """ExtractClaimsStrategyType 类定义."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """获取字符串表示."""
        return f'"{self.value}"'


DEFAULT_ENTITY_TYPES = ["组织", "人物", "地点", "事件"]


@verb(name="extract_covariates")
async def extract_covariates(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    covariate_type: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    **kwargs,
) -> TableContainer:
    """
    从文本片段中提取声明。

    ## 用法
    TODO
    """
    log.debug("extract_covariates strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES
    output = cast("pd.DataFrame", input.get_input())

    resolved_entities_map = {}

    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", ExtractClaimsStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    async def run_strategy(row):
        """
        执行strategy。

        Args:
            row: row 参数。

        Returns:
            处理结果。
        """
        text = row[column]
        result = await strategy_exec(
            text, entity_types, resolved_entities_map, callbacks, cache, strategy_config
        )
        return [
            create_row_from_claim_data(row, item, covariate_type)
            for item in result.covariate_data
        ]

    results = await derive_from_rows(
        output,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    output = pd.DataFrame([item for row in results for item in row or []])
    return TableContainer(table=output)


def load_strategy(strategy_type: ExtractClaimsStrategyType) -> CovariateExtractStrategy:
    """加载策略方法定义."""
    match strategy_type:
        case ExtractClaimsStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run as run_gi

            return run_gi
        case _:
            msg = f"未知策略: {strategy_type}"
            raise ValueError(msg)


def create_row_from_claim_data(row, covariate_data: Covariate, covariate_type: str):
    """从声明数据和输入行创建一行."""
    item = {**row, **asdict(covariate_data), "covariate_type": covariate_type}
    # TODO: 从提取中获取的 doc_id 不是必需的
    # 因为分块发生在此之前
    del item["doc_id"]
    return item
