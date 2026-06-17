"""为本地搜索提示构建上下文数据的算法。

Algorithms to build context data for local search prompt.
"""

import logging
from typing import Any

import pandas as pd
import tiktoken

from ai.components.graphrag.config import GraphRagConfig
from ai.components.graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from ai.components.graphrag.query.context_builder.community_context import (
    build_community_context,
)
from ai.components.graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from ai.components.graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
    map_query_to_entities,
)
from ai.components.graphrag.query.context_builder.local_context import (
    build_covariates_context,
    build_entity_context,
    build_relationship_context,
    get_candidate_context,
)
from ai.components.graphrag.query.context_builder.source_context import (
    build_text_unit_context,
    count_relationships,
)
from ai.components.graphrag.query.input.retrieval.community_reports import (
    get_candidate_communities,
)
from ai.components.graphrag.query.input.retrieval.text_units import (
    get_candidate_text_units,
)
from ai.components.graphrag.query.llm.base import BaseTextEmbedding
from ai.components.graphrag.query.llm.text_utils import num_tokens
from ai.components.graphrag.query.structured_search.base import LocalContextBuilder
from ai.components.graphrag.vector_stores import BaseVectorStore

log = logging.getLogger(__name__)


# 记录旧的reranker.min_score配置参数 / Record old reranker.min_score config parameter
RAW_CONFIG_RERANKER_MIN_SCORE = None


class LocalSearchMixedContext(LocalContextBuilder):
    """
    为本地搜索提示构建数据上下文,结合社区报告和实体/关系/协变量表。

    Build data context for local search prompt combining community reports and entity/relationship/covariate tables.
    """

    def __init__(
        self,
        entities: list[Entity],
        entity_text_embeddings: BaseVectorStore,
        text_embedder: BaseTextEmbedding,
        text_units: list[TextUnit] | None = None,
        community_reports: list[CommunityReport] | None = None,
        relationships: list[Relationship] | None = None,
        covariates: dict[str, list[Covariate]] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
        config: GraphRagConfig = None,
    ):
        """
        初始化实例。

        Args:
            entities (list[Entity]): entities 参数。
            entity_text_embeddings (BaseVectorStore): entity_text_embeddings 参数。
            text_embedder (BaseTextEmbedding): text_embedder 参数。
            text_units (list[TextUnit] | None): text_units 参数。
            community_reports (list[CommunityReport] | None): community_reports 参数。
            relationships (list[Relationship] | None): relationships 参数。
            covariates (dict[str, list[Covariate]] | None): covariates 参数。
            token_encoder (tiktoken.Encoding | None): token_encoder 参数。
            embedding_vectorstore_key (str): embedding_vectorstore_key 参数。
            config (GraphRagConfig): config 参数。
        """
        if community_reports is None:
            community_reports = []
        if relationships is None:
            relationships = []
        if covariates is None:
            covariates = {}
        if text_units is None:
            text_units = []
        self.entities = {entity.id: entity for entity in entities}
        self.community_reports = {
            community.id: community for community in community_reports
        }
        self.text_units = {unit.id: unit for unit in text_units}
        self.relationships = {
            relationship.id: relationship for relationship in relationships
        }
        self.covariates = covariates
        self.entity_text_embeddings = entity_text_embeddings
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.embedding_vectorstore_key = embedding_vectorstore_key
        self.config = config

    def filter_by_entity_keys(self, entity_keys: list[int] | list[str]):
        """
        根据实体键过滤实体文本嵌入。

        Filter entity text embeddings by entity keys.
        """
        self.entity_text_embeddings.filter_by_id(entity_keys)

    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        include_entity_names: list[str] | None = None,
        exclude_entity_names: list[str] | None = None,
        conversation_history_max_turns: int | None = 5,
        conversation_history_user_turns_only: bool = True,
        max_tokens: int = 8000,
        text_unit_prop: float = 0.5,
        community_prop: float = 0.25,
        top_k_mapped_entities: int = 10,
        top_k_relationships: int = 10,
        include_community_rank: bool = False,
        include_entity_rank: bool = False,
        rank_description: str = "number of relationships",
        include_relationship_weight: bool = False,
        relationship_ranking_attribute: str = "rank",
        return_candidate_context: bool = False,
        use_community_summary: bool = False,
        min_community_rank: int = 0,
        community_context_name: str = "Reports",
        column_delimiter: str = "|",
        **kwargs: dict[str, Any],
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """
        为本地搜索提示构建数据上下文。

        通过结合社区报告和实体/关系/协变量表以及文本单元,使用由 summary_prop 设置的预定义比率构建上下文。

        Build data context for local search prompt.

        Build a context by combining community reports and entity/relationship/covariate tables, and text units using a predefined ratio set by summary_prop.

        参数 Parameters
        ----------
        - query (str): 用户查询。User query
        - conversation_history (ConversationHistory | None): 对话历史。Conversation history
        - include_entity_names (list[str] | None): 要包含的实体名称。Entity names to include
        - exclude_entity_names (list[str] | None): 要排除的实体名称。Entity names to exclude
        - conversation_history_max_turns (int | None): 对话历史最大轮次。Maximum conversation history turns
        - conversation_history_user_turns_only (bool): 是否仅包含用户轮次。Whether to include user turns only
        - max_tokens (int): 最大令牌数。Maximum tokens
        - text_unit_prop (float): 文本单元比例。Text unit proportion
        - community_prop (float): 社区比例。Community proportion
        - top_k_mapped_entities (int): 映射实体的 top k 数量。Top k mapped entities
        - top_k_relationships (int): 关系的 top k 数量。Top k relationships
        - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
        - include_entity_rank (bool): 是否包含实体排名。Whether to include entity rank
        - rank_description (str): 排名描述。Rank description
        - include_relationship_weight (bool): 是否包含关系权重。Whether to include relationship weight
        - relationship_ranking_attribute (str): 关系排名属性。Relationship ranking attribute
        - return_candidate_context (bool): 是否返回候选上下文。Whether to return candidate context
        - use_community_summary (bool): 是否使用社区摘要。Whether to use community summary
        - min_community_rank (int): 最小社区排名。Minimum community rank
        - community_context_name (str): 社区上下文名称。Community context name
        - column_delimiter (str): 列分隔符。Column delimiter
        - **kwargs: 其他参数。Additional arguments

        返回 Returns
        -------
        - tuple[str | list[str], dict[str, pd.DataFrame]]: (上下文文本, 上下文数据)。(Context text, context data)
        """
        if include_entity_names is None:
            include_entity_names = []
        if exclude_entity_names is None:
            exclude_entity_names = []
        if community_prop + text_unit_prop > 1:
            value_error = (
                "The sum of community_prop and text_unit_prop should not exceed 1."
            )
            raise ValueError(value_error)

        # 将用户查询映射到实体 / map user query to entities
        # 如果有对话历史,则将先前的用户问题附加到当前查询 / if there is conversation history, attached the previous user questions to the current query
        if conversation_history:
            pre_user_questions = "\n".join(
                conversation_history.get_user_turns(conversation_history_max_turns)
            )
            query = f"{query}\n{pre_user_questions}"

        global RAW_CONFIG_RERANKER_MIN_SCORE
        if RAW_CONFIG_RERANKER_MIN_SCORE is None:
            # 如果为空,则记录当前值,以便后续恢复,因为self.config.reranker.min_score是在下面的代码中被动态设置的,所以此处的取值肯定是配置文件中的值
            # If empty, record current value for later restoration, as self.config.reranker.min_score is dynamically set in the code below
            RAW_CONFIG_RERANKER_MIN_SCORE = self.config.reranker.min_score
        else:
            # 恢复旧值 / Restore old value
            self.config.reranker.min_score = RAW_CONFIG_RERANKER_MIN_SCORE

        min_score = kwargs.get("min_score")
        if min_score is not None:
            self.config.reranker.min_score = min_score

        # 映射查询到实体 / Map query to entities
        selected_entities = map_query_to_entities(
            query=query,
            text_embedding_vectorstore=self.entity_text_embeddings,
            text_embedder=self.text_embedder,
            all_entities=list(self.entities.values()),
            embedding_vectorstore_key=self.embedding_vectorstore_key,
            include_entity_names=include_entity_names,
            exclude_entity_names=exclude_entity_names,
            k=top_k_mapped_entities,
            oversample_scaler=2,
            config=self.config,
        )

        # 构建上下文 / build context
        final_context = list[str]()
        final_context_data = dict[str, pd.DataFrame]()

        if conversation_history:
            # 构建对话历史上下文 / build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_tokens=max_tokens,
                recency_bias=False,
            )
            if conversation_history_context.strip() != "":
                final_context.append(conversation_history_context)
                final_context_data = conversation_history_context_data
                max_tokens = max_tokens - num_tokens(
                    conversation_history_context, self.token_encoder
                )

        # 构建社区上下文 / build community context
        community_tokens = max(int(max_tokens * community_prop), 0)
        community_context, community_context_data = self._build_community_context(
            selected_entities=selected_entities,
            max_tokens=community_tokens,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            return_candidate_context=return_candidate_context,
            context_name=community_context_name,
        )
        if community_context.strip() != "":
            final_context.append(community_context)
            final_context_data = {**final_context_data, **community_context_data}

        # 构建本地(即实体-关系-协变量)上下文 / build local (i.e. entity-relationship-covariate) context
        local_prop = 1 - community_prop - text_unit_prop
        local_tokens = max(int(max_tokens * local_prop), 0)
        local_context, local_context_data = self._build_local_context(
            selected_entities=selected_entities,
            max_tokens=local_tokens,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            include_relationship_weight=include_relationship_weight,
            top_k_relationships=top_k_relationships,
            relationship_ranking_attribute=relationship_ranking_attribute,
            return_candidate_context=return_candidate_context,
            column_delimiter=column_delimiter,
        )
        if local_context.strip() != "":
            final_context.append(str(local_context))
            final_context_data = {**final_context_data, **local_context_data}

        # 构建文本单元上下文 / build text unit context
        text_unit_tokens = max(int(max_tokens * text_unit_prop), 0)
        text_unit_context, text_unit_context_data = self._build_text_unit_context(
            selected_entities=selected_entities,
            max_tokens=text_unit_tokens,
            return_candidate_context=return_candidate_context,
        )
        if text_unit_context.strip() != "":
            final_context.append(text_unit_context)
            final_context_data = {**final_context_data, **text_unit_context_data}

        return ("\n\n".join(final_context), final_context_data)

    def _build_community_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 4000,
        use_community_summary: bool = False,
        column_delimiter: str = "|",
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        return_candidate_context: bool = False,
        context_name: str = "Reports",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """
        将社区数据添加到上下文窗口,直到达到 max_tokens 限制。

        Add community data to the context window until it hits the max_tokens limit.

        参数 Parameters
        ----------
        - selected_entities (list[Entity]): 选定的实体。Selected entities
        - max_tokens (int): 最大令牌数。Maximum tokens
        - use_community_summary (bool): 是否使用社区摘要。Whether to use community summary
        - column_delimiter (str): 列分隔符。Column delimiter
        - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
        - min_community_rank (int): 最小社区排名。Minimum community rank
        - return_candidate_context (bool): 是否返回候选上下文。Whether to return candidate context
        - context_name (str): 上下文名称。Context name

        返回 Returns
        -------
        - tuple[str, dict[str, pd.DataFrame]]: (上下文文本, 上下文数据)。(Context text, context data)
        """
        if len(selected_entities) == 0 or len(self.community_reports) == 0:
            return ("", {context_name.lower(): pd.DataFrame()})

        community_matches = {}
        for entity in selected_entities:
            # 增加该实体所属社区的计数 / increase count of the community that this entity belongs to
            if entity.community_ids:
                for community_id in entity.community_ids:
                    community_matches[community_id] = (
                        community_matches.get(community_id, 0) + 1
                    )

        # 按匹配实体数量和排名对社区排序 / sort communities by number of matched entities and rank
        selected_communities = [
            self.community_reports[community_id]
            for community_id in community_matches
            if community_id in self.community_reports
        ]
        for community in selected_communities:
            if community.attributes is None:
                community.attributes = {}
            community.attributes["matches"] = community_matches[community.id]
        selected_communities.sort(
            key=lambda x: (x.attributes["matches"], x.rank),  # type: ignore
            reverse=True,  # type: ignore
        )
        for community in selected_communities:
            del community.attributes["matches"]  # type: ignore

        # 构建社区上下文 / Build community context
        context_text, context_data = build_community_context(
            community_reports=selected_communities,
            token_encoder=self.token_encoder,
            use_community_summary=use_community_summary,
            column_delimiter=column_delimiter,
            shuffle_data=False,
            include_community_rank=include_community_rank,
            min_community_rank=min_community_rank,
            max_tokens=max_tokens,
            single_batch=True,
            context_name=context_name,
        )
        if isinstance(context_text, list) and len(context_text) > 0:
            context_text = "\n\n".join(context_text)

        if return_candidate_context:
            candidate_context_data = get_candidate_communities(
                selected_entities=selected_entities,
                community_reports=list(self.community_reports.values()),
                use_community_summary=use_community_summary,
                include_community_rank=include_community_rank,
            )
            context_key = context_name.lower()
            if context_key not in context_data:
                context_data[context_key] = candidate_context_data
                context_data[context_key]["in_context"] = False
            else:
                if (
                    "id" in candidate_context_data.columns
                    and "id" in context_data[context_key].columns
                ):
                    candidate_context_data["in_context"] = candidate_context_data[
                        "id"
                    ].isin(  # cspell:disable-line
                        context_data[context_key]["id"]
                    )
                    context_data[context_key] = candidate_context_data
                else:
                    context_data[context_key]["in_context"] = True
        return (str(context_text), context_data)

    def _build_text_unit_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 8000,
        return_candidate_context: bool = False,
        column_delimiter: str = "|",
        context_name: str = "Sources",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """
        对匹配的文本单元进行排名,并将它们添加到上下文窗口,直到达到 max_tokens 限制。

        Rank matching text units and add them to the context window until it hits the max_tokens limit.

        参数 Parameters
        ----------
        - selected_entities (list[Entity]): 选定的实体。Selected entities
        - max_tokens (int): 最大令牌数。Maximum tokens
        - return_candidate_context (bool): 是否返回候选上下文。Whether to return candidate context
        - column_delimiter (str): 列分隔符。Column delimiter
        - context_name (str): 上下文名称。Context name

        返回 Returns
        -------
        - tuple[str, dict[str, pd.DataFrame]]: (上下文文本, 上下文数据)。(Context text, context data)
        """
        if len(selected_entities) == 0 or len(self.text_units) == 0:
            return ("", {context_name.lower(): pd.DataFrame()})

        selected_text_units = list[TextUnit]()
        # 对于每个匹配的文本单元,首先按匹配的实体的顺序排名,然后按文本单元与匹配实体的匹配关系数量排名
        # for each matching text unit, rank first by the order of the entities that match it, then by the number of matching relationships
        # that the text unit has with the matching entities
        for index, entity in enumerate(selected_entities):
            if entity.text_unit_ids:
                for text_id in entity.text_unit_ids:
                    if (
                        text_id not in [unit.id for unit in selected_text_units]
                        and text_id in self.text_units
                    ):
                        selected_unit = self.text_units[text_id]
                        num_relationships = count_relationships(
                            selected_unit, entity, self.relationships
                        )
                        if selected_unit.attributes is None:
                            selected_unit.attributes = {}
                        selected_unit.attributes["entity_order"] = index
                        selected_unit.attributes["num_relationships"] = (
                            num_relationships
                        )
                        selected_text_units.append(selected_unit)

        # 按实体顺序升序和关系数量降序对选定的文本单元排序
        # sort selected text units by ascending order of entity order and descending order of number of relationships
        selected_text_units.sort(
            key=lambda x: (
                x.attributes["entity_order"],  # type: ignore
                -x.attributes["num_relationships"],  # type: ignore
            )
        )

        for unit in selected_text_units:
            del unit.attributes["entity_order"]  # type: ignore
            del unit.attributes["num_relationships"]  # type: ignore

        # 构建文本单元上下文 / Build text unit context
        context_text, context_data = build_text_unit_context(
            text_units=selected_text_units,
            token_encoder=self.token_encoder,
            max_tokens=max_tokens,
            shuffle_data=False,
            context_name=context_name,
            column_delimiter=column_delimiter,
        )

        if return_candidate_context:
            candidate_context_data = get_candidate_text_units(
                selected_entities=selected_entities,
                text_units=list(self.text_units.values()),
            )
            context_key = context_name.lower()
            if context_key not in context_data:
                context_data[context_key] = candidate_context_data
                context_data[context_key]["in_context"] = False
            else:
                if (
                    "id" in candidate_context_data.columns
                    and "id" in context_data[context_key].columns
                ):
                    candidate_context_data["in_context"] = candidate_context_data[
                        "id"
                    ].isin(  # cspell:disable-line
                        context_data[context_key]["id"]
                    )
                    context_data[context_key] = candidate_context_data
                else:
                    context_data[context_key]["in_context"] = True
        return (str(context_text), context_data)

    def _build_local_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 8000,
        include_entity_rank: bool = False,
        rank_description: str = "relationship count",
        include_relationship_weight: bool = False,
        top_k_relationships: int = 10,
        relationship_ranking_attribute: str = "rank",
        return_candidate_context: bool = False,
        column_delimiter: str = "|",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """
        为本地搜索提示构建数据上下文,结合实体/关系/协变量表。

        Build data context for local search prompt combining entity/relationship/covariate tables.

        参数 Parameters
        ----------
        - selected_entities (list[Entity]): 选定的实体。Selected entities
        - max_tokens (int): 最大令牌数。Maximum tokens
        - include_entity_rank (bool): 是否包含实体排名。Whether to include entity rank
        - rank_description (str): 排名描述。Rank description
        - include_relationship_weight (bool): 是否包含关系权重。Whether to include relationship weight
        - top_k_relationships (int): 关系的 top k 数量。Top k relationships
        - relationship_ranking_attribute (str): 关系排名属性。Relationship ranking attribute
        - return_candidate_context (bool): 是否返回候选上下文。Whether to return candidate context
        - column_delimiter (str): 列分隔符。Column delimiter

        返回 Returns
        -------
        - tuple[str, dict[str, pd.DataFrame]]: (上下文文本, 上下文数据)。(Context text, context data)
        """
        # 构建实体上下文 / build entity context
        entity_context, entity_context_data = build_entity_context(
            selected_entities=selected_entities,
            token_encoder=self.token_encoder,
            max_tokens=max_tokens,
            column_delimiter=column_delimiter,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            context_name="Entities",
        )
        entity_tokens = num_tokens(entity_context, self.token_encoder)

        # 构建关系-协变量上下文 / build relationship-covariate context
        added_entities = []
        final_context = []
        final_context_data = {}

        # 逐步添加实体和相关元数据到上下文,直到达到限制
        # gradually add entities and associated metadata to the context until we reach limit
        for entity in selected_entities:
            current_context = []
            current_context_data = {}
            added_entities.append(entity)

            # 构建关系上下文 / build relationship context
            (
                relationship_context,
                relationship_context_data,
            ) = build_relationship_context(
                selected_entities=added_entities,
                relationships=list(self.relationships.values()),
                token_encoder=self.token_encoder,
                max_tokens=max_tokens,
                column_delimiter=column_delimiter,
                top_k_relationships=top_k_relationships,
                include_relationship_weight=include_relationship_weight,
                relationship_ranking_attribute=relationship_ranking_attribute,
                context_name="Relationships",
            )
            current_context.append(relationship_context)
            current_context_data["relationships"] = relationship_context_data
            total_tokens = entity_tokens + num_tokens(
                relationship_context, self.token_encoder
            )

            # 构建协变量上下文 / build covariate context
            for covariate in self.covariates:
                covariate_context, covariate_context_data = build_covariates_context(
                    selected_entities=added_entities,
                    covariates=self.covariates[covariate],
                    token_encoder=self.token_encoder,
                    max_tokens=max_tokens,
                    column_delimiter=column_delimiter,
                    context_name=covariate,
                )
                total_tokens += num_tokens(covariate_context, self.token_encoder)
                current_context.append(covariate_context)
                current_context_data[covariate.lower()] = covariate_context_data

            if total_tokens > max_tokens:
                log.info("Reached token limit - reverting to previous context state")

                # 超过大小之后,目前暂时继续使用该状态,使其内容更加丰富。todo liangyuxiang 后续考虑需要跟进token数进行裁剪
                # After exceeding size, currently continue to use this state to make the content richer. todo liangyuxiang consider trimming based on token count later
                final_context = current_context
                final_context_data = current_context_data
                break

            final_context = current_context
            final_context_data = current_context_data

        # 将实体上下文附加到最终上下文 / attach entity context to final context
        final_context_text = entity_context + "\n\n" + "\n\n".join(final_context)
        final_context_data["entities"] = entity_context_data

        if return_candidate_context:
            # 我们返回所有候选实体/关系/协变量(不仅仅是那些适合上下文窗口的),并添加标记以指示哪些记录包含在上下文窗口中
            # we return all the candidate entities/relationships/covariates (not only those that were fitted into the context window)
            # and add a tag to indicate which records were included in the context window
            candidate_context_data = get_candidate_context(
                selected_entities=selected_entities,
                entities=list(self.entities.values()),
                relationships=list(self.relationships.values()),
                covariates=self.covariates,
                include_entity_rank=include_entity_rank,
                entity_rank_description=rank_description,
                include_relationship_weight=include_relationship_weight,
            )
            for key in candidate_context_data:
                candidate_df = candidate_context_data[key]
                if key not in final_context_data:
                    final_context_data[key] = candidate_df
                    final_context_data[key]["in_context"] = False
                else:
                    in_context_df = final_context_data[key]

                    if "id" in in_context_df.columns and "id" in candidate_df.columns:
                        candidate_df["in_context"] = candidate_df[
                            "id"
                        ].isin(  # cspell:disable-line
                            in_context_df["id"]
                        )
                        final_context_data[key] = candidate_df
                    else:
                        final_context_data[key]["in_context"] = True

        else:
            for key in final_context_data:
                final_context_data[key]["in_context"] = True
        return (final_context_text, final_context_data)
