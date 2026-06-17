"""包含 run_gi,  run_resolve_entities and _create_text_list_splitter methods to run graph intelligence."""

from datashaper import VerbCallbacks

from ai.components.graphrag.config.enums import LLMType
from ai.components.graphrag.index.cache import PipelineCache
from ai.components.graphrag.index.graph.extractors.summarize import SummarizeExtractor
from ai.components.graphrag.index.llm import load_llm
from ai.components.graphrag.index.verbs.entities.summarize.strategies.graph_intelligence.defaults import (
    DEFAULT_LLM_CONFIG,
)
from ai.components.graphrag.index.verbs.entities.summarize.strategies.typing import (
    StrategyConfig,
    SummarizedDescriptionResult,
)
from ai.components.graphrag.llm import CompletionLLM


async def run(
    described_items: str | tuple[str, str],
    descriptions: list[str],
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """
    执行run。

    Args:
        described_items (str | tuple[str, str]): described_items 参数。
        descriptions (list[str]): descriptions 参数。
        reporter (VerbCallbacks): reporter 参数。
        pipeline_cache (PipelineCache): pipeline_cache 参数。
        args (StrategyConfig): args 参数。

    Returns:
        处理结果。
    """
    llm_config = args.get("llm", DEFAULT_LLM_CONFIG)
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm(
        "summarize_descriptions", llm_type, reporter, pipeline_cache, llm_config
    )
    return await run_summarize_descriptions(
        llm, described_items, descriptions, reporter, args
    )


async def run_summarize_descriptions(
    llm: CompletionLLM,
    items: str | tuple[str, str],
    descriptions: list[str],
    reporter: VerbCallbacks,
    args: StrategyConfig,
) -> SummarizedDescriptionResult:
    """
    执行summarize_descriptions。

    Args:
        llm (CompletionLLM): llm 参数。
        items (str | tuple[str, str]): items 参数。
        descriptions (list[str]): descriptions 参数。
        reporter (VerbCallbacks): reporter 参数。
        args (StrategyConfig): args 参数。

    Returns:
        处理结果。
    """
    # Extraction Arguments
    summarize_prompt = args.get("summarize_prompt", None)
    entity_name_key = args.get("entity_name_key", "entity_name")
    input_descriptions_key = args.get("input_descriptions_key", "description_list")
    max_tokens = args.get("max_tokens", None)

    extractor = SummarizeExtractor(
        llm_invoker=llm,
        summarization_prompt=summarize_prompt,
        entity_name_key=entity_name_key,
        input_descriptions_key=input_descriptions_key,
        on_error=lambda e, stack, details: (
            reporter.error("Entity Extraction Error", e, stack, details)
            if reporter
            else None
        ),
        max_summary_length=args.get("max_summary_length", None),
        max_input_tokens=max_tokens,
    )

    result = await extractor(items=items, descriptions=descriptions)
    return SummarizedDescriptionResult(
        items=result.items, description=result.description
    )
