"""自动模板化 API。

Auto Templating API.

此 API 提供对 GraphRAG 自动模板化功能的访问,允许外部应用程序
接入 GraphRAG 并从私有数据生成提示词。

This API provides access to the auto templating feature of graphrag, allowing external applications
to hook into graphrag and generate prompts from private data.

警告:此 API 正在开发中,可能在未来版本中发生变化。
目前不保证向后兼容性。

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from datashaper import NoopVerbCallbacks
from pydantic import PositiveInt, validate_call

from ai.components.graphrag.config.models.graph_rag_config import GraphRagConfig
from ai.components.graphrag.index.llm import load_llm
from ai.components.graphrag.index.progress import PrintProgressReporter
from ai.components.graphrag.prompt_tune.cli import DocSelectionType
from ai.components.graphrag.prompt_tune.generator import (
    MAX_TOKEN_COUNT,
    create_community_summarization_prompt,
    create_entity_extraction_prompt,
    create_entity_summarization_prompt,
    detect_language,
    generate_community_report_rating,
    generate_community_reporter_role,
    generate_domain,
    generate_entity_relationship_examples,
    generate_entity_types,
    generate_persona,
)
from ai.components.graphrag.prompt_tune.loader import (
    MIN_CHUNK_SIZE,
    load_docs_in_chunks,
)


@validate_call
async def generate_indexing_prompts(
    config: GraphRagConfig,
    root: str,
    chunk_size: PositiveInt = MIN_CHUNK_SIZE,
    limit: PositiveInt = 15,
    selection_method: DocSelectionType = DocSelectionType.RANDOM,
    domain: str | None = None,
    language: str | None = None,
    max_tokens: int = MAX_TOKEN_COUNT,
    skip_entity_types: bool = False,
    min_examples_required: PositiveInt = 2,
    n_subset_max: PositiveInt = 300,
    k: PositiveInt = 15,
) -> tuple[str, str, str]:
    """
    生成索引提示词。

    根据输入的文档和配置,自动生成三种类型的提示词:
    实体抽取提示词,实体摘要提示词和社区摘要提示词。

    Generate indexing prompts.

    参数 Parameters
    ----------
    - config: GraphRAG 配置对象。The GraphRag configuration.
    - root: 数据根目录路径。The root directory path.
    - chunk_size: 输入文本单元使用的分块 token 大小。默认:200。The chunk token size to use for input text units.
    - limit: 要加载的文档块数量限制。默认:15。The limit of chunks to load.
    - selection_method: 文档块选择方法。默认:RANDOM。The chunk selection method.
    - domain: 输入文档映射到的领域。如果为 None,将自动推断。The domain to map the input documents to.
    - language: 提示词使用的语言。如果为 None,将自动检测。The language to use for the prompts.
    - max_tokens: 实体抽取提示词的最大 token 数。默认:8000。The maximum number of tokens to use on entity extraction prompts.
    - skip_entity_types: 是否跳过生成实体类型。默认:False。Skip generating entity types.
    - min_examples_required: 实体抽取提示词所需的最小示例数。默认:2。The minimum number of examples required for entity extraction prompts.
    - n_subset_max: 使用自动选择方法时要嵌入的文本块数量。默认:300。The number of text chunks to embed when using auto selection method.
    - k: 使用自动选择方法时要选择的文档数量。默认:15。The number of documents to select when using auto selection method.

    返回 Returns
    -------
    tuple[str, str, str]: 包含三个提示词的元组:(实体抽取提示词, 实体摘要提示词, 社区摘要提示词)。
    tuple[str, str, str]: entity extraction prompt, entity summarization prompt, community summarization prompt.
    """
    reporter = PrintProgressReporter("")

    # 检索文档
    # Retrieve documents
    doc_list = await load_docs_in_chunks(
        root=root,
        config=config,
        limit=limit,
        select_method=selection_method,
        reporter=reporter,
        chunk_size=chunk_size,
        n_subset_max=n_subset_max,
        k=k,
    )

    # 从配置创建 LLM
    # Create LLM from config
    llm = load_llm(
        "prompt_tuning",
        config.llm.type,
        NoopVerbCallbacks(),
        None,
        config.llm.model_dump(),
    )

    # 生成或使用提供的领域
    # Generate or use provided domain
    if not domain:
        reporter.info("Generating domain...")
        domain = await generate_domain(llm, doc_list)
        reporter.info(f"Generated domain: {domain}")

    # 检测或使用提供的语言
    # Detect or use provided language
    if not language:
        reporter.info("Detecting language...")
        language = await detect_language(llm, doc_list)

    # 生成角色设定
    # Generate persona
    reporter.info("Generating persona...")
    persona = await generate_persona(llm, domain)

    # 生成社区报告排名描述
    # Generate community report ranking description
    reporter.info("Generating community report ranking description...")
    community_report_ranking = await generate_community_report_rating(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    # 生成实体类型(如果未跳过)
    # Generate entity types (if not skipped)
    entity_types = None
    if not skip_entity_types:
        reporter.info("Generating entity types...")
        entity_types = await generate_entity_types(
            llm,
            domain=domain,
            persona=persona,
            docs=doc_list,
            json_mode=config.llm.model_supports_json or False,
        )

    # 生成实体关系示例
    # Generate entity relationship examples
    reporter.info("Generating entity relationship examples...")
    examples = await generate_entity_relationship_examples(
        llm,
        persona=persona,
        entity_types=entity_types,
        docs=doc_list,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but this prompts are used in non-json by the index engine
    )

    # 创建实体抽取提示词
    # Create entity extraction prompt
    reporter.info("Generating entity extraction prompt...")
    entity_extraction_prompt = create_entity_extraction_prompt(
        entity_types=entity_types,
        docs=doc_list,
        examples=examples,
        language=language,
        json_mode=False,  # config.llm.model_supports_json should be used, but these prompts are used in non-json by the index engine
        encoding_model=config.encoding_model,
        max_token_count=max_tokens,
        min_examples_required=min_examples_required,
    )

    # 创建实体摘要提示词
    # Create entity summarization prompt
    reporter.info("Generating entity summarization prompt...")
    entity_summarization_prompt = create_entity_summarization_prompt(
        persona=persona,
        language=language,
    )

    # 生成社区报告者角色
    # Generate community reporter role
    reporter.info("Generating community reporter role...")
    community_reporter_role = await generate_community_reporter_role(
        llm, domain=domain, persona=persona, docs=doc_list
    )

    # 创建社区摘要提示词
    # Create community summarization prompt
    reporter.info("Generating community summarization prompt...")
    community_summarization_prompt = create_community_summarization_prompt(
        persona=persona,
        role=community_reporter_role,
        report_rating_description=community_report_ranking,
        language=language,
    )

    return (
        entity_extraction_prompt,
        entity_summarization_prompt,
        community_summarization_prompt,
    )
