"""查询工厂方法,用于支持命令行接口。

Query Factory methods to support CLI.
"""

import tiktoken

from ai.components.graphrag.config import (
    GraphRagConfig,
    LLMType,
)
from ai.components.graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from ai.components.graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
)
from ai.components.graphrag.query.llm.oai.chat_openai import ChatOpenAI
from ai.components.graphrag.query.llm.oai.embedding import OpenAIEmbedding
from ai.components.graphrag.query.llm.oai.typing import OpenaiApiType
from ai.components.graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from ai.components.graphrag.query.structured_search.global_search.search import (
    GlobalSearch,
)
from ai.components.graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from ai.components.graphrag.query.structured_search.local_search.search import (
    LocalSearch,
)
from ai.components.graphrag.vector_stores import BaseVectorStore


def _get_azure_identity_deps():
    """
    延迟导入 Azure Identity 依赖.

    Lazily import Azure Identity dependencies.
    """
    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        return DefaultAzureCredential, get_bearer_token_provider
    except ImportError as e:
        msg = "Azure Identity 依赖未安装，请执行: pip install azure-identity"
        raise ImportError(msg) from e


def get_llm(config: GraphRagConfig) -> ChatOpenAI:
    """
    获取 LLM 客户端。

    Get the LLM client.

    参数 Parameters
    ----------
    - config (GraphRagConfig): GraphRAG 配置对象。GraphRAG configuration object

    返回 Returns
    -------
    - ChatOpenAI: 聊天 OpenAI 客户端实例。ChatOpenAI client instance
    """
    # 判断是否为 Azure 客户端类型
    # Check if it's an Azure client type
    is_azure_client = config.llm.type in (LLMType.AzureOpenAIChat, LLMType.AzureOpenAI)
    # 准备调试信息(隐藏 API 密钥)
    # Prepare debug info (hide API key)
    debug_llm_key = config.llm.api_key or ""
    llm_debug_info = {
        **config.llm.model_dump(),
        "api_key": f"REDACTED,len={len(debug_llm_key)}",
    }
    # 配置认知服务端点
    # Configure cognitive services endpoint
    if config.llm.cognitive_services_endpoint is None:
        cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
    else:
        cognitive_services_endpoint = config.llm.cognitive_services_endpoint
    print(f"creating llm client with {llm_debug_info}")

    # 延迟导入 Azure 依赖
    azure_ad_token_provider = None
    if is_azure_client and not config.llm.api_key:
        DefaultAzureCredential, get_bearer_token_provider = _get_azure_identity_deps()
        azure_ad_token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), cognitive_services_endpoint
        )

    # 创建并返回 ChatOpenAI 客户端
    # Create and return ChatOpenAI client
    return ChatOpenAI(
        api_key=config.llm.api_key,
        azure_ad_token_provider=azure_ad_token_provider,
        api_base=config.llm.api_base,
        organization=config.llm.organization,
        model=config.llm.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=config.llm.deployment_name,
        api_version=config.llm.api_version,
        max_retries=config.llm.max_retries,
    )


def get_text_embedder(config: GraphRagConfig) -> OpenAIEmbedding:
    """
    获取用于嵌入的 LLM 客户端。

    Get the LLM client for embeddings.

    参数 Parameters
    ----------
    - config (GraphRagConfig): GraphRAG 配置对象。GraphRAG configuration object

    返回 Returns
    -------
    - OpenAIEmbedding: OpenAI 嵌入客户端实例。OpenAI embedding client instance
    """
    # 判断是否为 Azure 嵌入客户端
    # Check if it's an Azure embedding client
    is_azure_client = config.embeddings.llm.type == LLMType.AzureOpenAIEmbedding
    # 准备嵌入 API 密钥调试信息
    # Prepare embedding API key debug info
    debug_embedding_api_key = config.embeddings.llm.api_key or ""
    llm_debug_info = {
        **config.embeddings.llm.model_dump(),
        "api_key": f"REDACTED,len={len(debug_embedding_api_key)}",
    }
    # 配置认知服务端点
    # Configure cognitive services endpoint
    if config.embeddings.llm.cognitive_services_endpoint is None:
        cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
    else:
        cognitive_services_endpoint = config.embeddings.llm.cognitive_services_endpoint
    print(f"creating embedding llm client with {llm_debug_info}")

    # 延迟导入 Azure 依赖
    azure_ad_token_provider = None
    if is_azure_client and not config.embeddings.llm.api_key:
        DefaultAzureCredential, get_bearer_token_provider = _get_azure_identity_deps()
        azure_ad_token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), cognitive_services_endpoint
        )

    # 创建并返回 OpenAI 嵌入客户端
    # Create and return OpenAI embedding client
    return OpenAIEmbedding(
        api_key=config.embeddings.llm.api_key,
        azure_ad_token_provider=azure_ad_token_provider,
        api_base=config.embeddings.llm.api_base,
        organization=config.llm.organization,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=config.embeddings.llm.model,
        deployment_name=config.embeddings.llm.deployment_name,
        api_version=config.embeddings.llm.api_version,
        max_retries=config.embeddings.llm.max_retries,
    )


def get_local_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    text_units: list[TextUnit],
    entities: list[Entity],
    relationships: list[Relationship],
    covariates: dict[str, list[Covariate]],
    response_type: str,
    description_embedding_store: BaseVectorStore,
) -> LocalSearch:
    """
    基于数据和配置创建本地搜索引擎。

    Create a local search engine based on data + configuration.

    参数 Parameters
    ----------
    - config (GraphRagConfig): GraphRAG 配置对象。GraphRAG configuration object
    - reports (list[CommunityReport]): 社区报告列表。List of community reports
    - text_units (list[TextUnit]): 文本单元列表。List of text units
    - entities (list[Entity]): 实体列表。List of entities
    - relationships (list[Relationship]): 关系列表。List of relationships
    - covariates (dict[str, list[Covariate]]): 协变量字典。Dictionary of covariates
    - response_type (str): 响应类型。Response type
    - description_embedding_store (BaseVectorStore): 描述嵌入向量存储。Description embedding vector store

    返回 Returns
    -------
    - LocalSearch: 本地搜索引擎实例。Local search engine instance
    """
    # 获取 LLM 客户端和文本嵌入器
    # Get LLM client and text embedder
    llm = get_llm(config)
    text_embedder = get_text_embedder(config)
    token_encoder = tiktoken.get_encoding(config.encoding_model)

    # 获取本地搜索配置
    # Get local search configuration
    ls_config = config.local_search

    # 创建并返回本地搜索引擎
    # Create and return local search engine
    return LocalSearch(
        llm=llm,
        context_builder=LocalSearchMixedContext(
            community_reports=reports,
            text_units=text_units,
            entities=entities,
            relationships=relationships,
            covariates=covariates,
            entity_text_embeddings=description_embedding_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID,  # 如果向量存储使用实体标题作为 ID，将其设置为 EntityVectorStoreKey.TITLE / if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
            text_embedder=text_embedder,
            token_encoder=token_encoder,
            config=config,
        ),
        token_encoder=token_encoder,
        llm_params={
            "max_tokens": ls_config.llm_max_tokens,  # 根据模型的令牌限制更改此值（如果使用 8k 限制的模型，建议设置为 1000-1500） / change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
            "temperature": ls_config.temperature,
            "top_p": ls_config.top_p,
            "n": ls_config.n,
        },
        context_builder_params={
            "text_unit_prop": ls_config.text_unit_prop,
            "community_prop": ls_config.community_prop,
            "conversation_history_max_turns": ls_config.conversation_history_max_turns,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": ls_config.top_k_entities,
            "top_k_relationships": ls_config.top_k_relationships,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # 如果向量存储使用实体标题作为 ID，将其设置为 EntityVectorStoreKey.TITLE / set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
            "max_tokens": ls_config.max_tokens,  # 根据模型的令牌限制更改此值（如果使用 8k 限制的模型，建议设置为 5000） / change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
        },
        response_type=response_type,
    )


def get_global_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    entities: list[Entity],
    response_type: str,
):
    """
    基于数据和配置创建全局搜索引擎。

    Create a global search engine based on data + configuration.

    参数 Parameters
    ----------
    - config (GraphRagConfig): GraphRAG 配置对象。GraphRAG configuration object
    - reports (list[CommunityReport]): 社区报告列表。List of community reports
    - entities (list[Entity]): 实体列表。List of entities
    - response_type (str): 响应类型。Response type

    返回 Returns
    -------
    - GlobalSearch: 全局搜索引擎实例。Global search engine instance
    """
    # 获取令牌编码器和全局搜索配置
    # Get token encoder and global search configuration
    token_encoder = tiktoken.get_encoding(config.encoding_model)
    gs_config = config.global_search

    # 创建并返回全局搜索引擎
    # Create and return global search engine
    return GlobalSearch(
        llm=get_llm(config),
        context_builder=GlobalCommunityContext(
            community_reports=reports, entities=entities, token_encoder=token_encoder
        ),
        token_encoder=token_encoder,
        max_data_tokens=gs_config.data_max_tokens,
        map_llm_params={
            "max_tokens": gs_config.map_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
            "n": gs_config.n,
        },
        reduce_llm_params={
            "max_tokens": gs_config.reduce_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
            "n": gs_config.n,
        },
        allow_general_knowledge=False,
        json_mode=False,
        context_builder_params={
            "use_community_summary": False,
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": gs_config.max_tokens,
            "context_name": "Reports",
        },
        concurrent_coroutines=gs_config.concurrency,
        response_type=response_type,
    )
