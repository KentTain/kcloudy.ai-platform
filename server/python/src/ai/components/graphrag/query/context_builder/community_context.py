"""社区上下文。

Community Context.
"""

import logging
import random
from typing import Any, cast

import pandas as pd
import tiktoken

from ai.components.graphrag.model import CommunityReport, Entity
from ai.components.graphrag.query.llm.text_utils import num_tokens


log = logging.getLogger(__name__)

NO_COMMUNITY_RECORDS_WARNING: str = (
    "Warning: No community records added when building community context."
)


def build_community_context(
    community_reports: list[CommunityReport],
    entities: list[Entity] | None = None,
    token_encoder: tiktoken.Encoding | None = None,
    use_community_summary: bool = True,
    column_delimiter: str = "|",
    shuffle_data: bool = True,
    include_community_rank: bool = False,
    min_community_rank: int = 0,
    community_rank_name: str = "rank",
    include_community_weight: bool = True,
    community_weight_name: str = "occurrence weight",
    normalize_community_weight: bool = True,
    max_tokens: int = 8000,
    single_batch: bool = True,
    context_name: str = "Reports",
    random_state: int = 86,
) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
    """
    将社区报告数据表准备为系统提示词的上下文数据。

    如果提供了实体,则社区权重计算为与社区内实体关联的文本单元数量。
    计算的权重将作为属性添加到社区报告中,并添加到上下文数据表中。

    Prepare community report data table as context data for system prompt.

    If entities are provided, the community weight is calculated as the count of text units associated with entities within the community.

    The calculated weight is added as an attribute to the community reports and added to the context data table.

    参数 Parameters
    ----------
    - community_reports (list[CommunityReport]): 社区报告列表。Community reports list
    - entities (list[Entity] | None): 实体列表(可选)。Entities list (optional)
    - token_encoder (tiktoken.Encoding | None): 令牌编码器。Token encoder
    - use_community_summary (bool): 是否使用社区摘要。Whether to use community summary
    - column_delimiter (str): 列分隔符。Column delimiter
    - shuffle_data (bool): 是否打乱数据。Whether to shuffle data
    - include_community_rank (bool): 是否包含社区排名。Whether to include community rank
    - min_community_rank (int): 最小社区排名。Minimum community rank
    - community_rank_name (str): 社区排名字段名。Community rank field name
    - include_community_weight (bool): 是否包含社区权重。Whether to include community weight
    - community_weight_name (str): 社区权重字段名。Community weight field name
    - normalize_community_weight (bool): 是否归一化社区权重。Whether to normalize community weight
    - max_tokens (int): 最大令牌数。Maximum tokens
    - single_batch (bool): 是否单批次处理。Whether to process in single batch
    - context_name (str): 上下文名称。Context name
    - random_state (int): 随机种子。Random seed

    返回 Returns
    -------
    - tuple[str | list[str], dict[str, pd.DataFrame]]: 上下文文本和数据表字典。Context text and data tables dictionary
    """

    def _is_included(report: CommunityReport) -> bool:
        """
        检查报告是否满足最小排名要求。

        Check if report meets minimum rank requirement.
        """
        return report.rank is not None and report.rank >= min_community_rank

    def _get_header(attributes: list[str]) -> list[str]:
        """
        获取表头。

        Get table header.
        """
        header = ["id", "title"]
        attributes = [col for col in attributes if col not in header]
        # 如果不包含社区权重,则从属性中移除权重字段
        # If not including community weight, remove weight field from attributes
        if not include_community_weight:
            attributes = [col for col in attributes if col != community_weight_name]
        header.extend(attributes)
        # 根据配置添加摘要或完整内容
        # Add summary or full content based on configuration
        header.append("summary" if use_community_summary else "content")
        if include_community_rank:
            header.append(community_rank_name)
        return header

    def _report_context_text(
        report: CommunityReport, attributes: list[str]
    ) -> tuple[str, list[str]]:
        """
        构建单个报告的上下文文本。

        Build context text for a single report.
        """
        context: list[str] = [
            report.short_id if report.short_id else "",
            report.title,
            *[
                str(report.attributes.get(field, "")) if report.attributes else ""
                for field in attributes
            ],
        ]
        context.append(report.summary if use_community_summary else report.full_content)
        if include_community_rank:
            context.append(str(report.rank))
        result = column_delimiter.join(context) + "\n"
        return result, context

    # 判断是否需要计算社区权重
    # Check if community weights need to be computed
    compute_community_weights = (
        entities
        and len(community_reports) > 0
        and include_community_weight
        and (
            community_reports[0].attributes is None
            or community_weight_name not in community_reports[0].attributes
        )
    )
    if compute_community_weights:
        log.info("Computing community weights...")
        community_reports = _compute_community_weights(
            community_reports=community_reports,
            entities=entities,
            weight_attribute=community_weight_name,
            normalize=normalize_community_weight,
        )

    # 筛选满足排名要求的报告
    # Filter reports that meet rank requirements
    selected_reports = [report for report in community_reports if _is_included(report)]

    if not selected_reports or len(selected_reports) == 0:
        return ([], {})

    # 如果需要,打乱数据
    # Shuffle data if needed
    if shuffle_data:
        random.seed(random_state)
        random.shuffle(selected_reports)

    # "全局"变量 / "global" variables
    attributes = (
        list(community_reports[0].attributes.keys())
        if community_reports[0].attributes
        else []
    )
    header = _get_header(attributes)
    all_context_text: list[str] = []
    all_context_records: list[pd.DataFrame] = []

    # 批次变量 / batch variables
    batch_text: str = ""
    batch_tokens: int = 0
    batch_records: list[list[str]] = []

    def _init_batch() -> None:
        """
        初始化批次。

        Initialize batch.
        """
        nonlocal batch_text, batch_tokens, batch_records
        batch_text = (
            f"-----{context_name}-----" + "\n" + column_delimiter.join(header) + "\n"
        )
        batch_tokens = num_tokens(batch_text, token_encoder)
        batch_records = []

    def _cut_batch() -> None:
        """
        切割批次并转换为 DataFrame。

        Cut batch and convert to DataFrame.
        """
        # 将当前上下文记录转换为 pandas dataframe,并按权重和排名排序(如果存在)
        # convert the current context records to pandas dataframe and sort by weight and rank if exist
        record_df = _convert_report_context_to_df(
            context_records=batch_records,
            header=header,
            weight_column=(
                community_weight_name if entities and include_community_weight else None
            ),
            rank_column=community_rank_name if include_community_rank else None,
        )
        if len(record_df) == 0:
            return
        current_context_text = record_df.to_csv(index=False, sep=column_delimiter)
        all_context_text.append(current_context_text)
        all_context_records.append(record_df)

    # 初始化第一个批次 / initialize the first batch
    _init_batch()

    # 判断最后一次批次是否添加过
    # Track if last batch was added
    last_batch_added = True

    for report in selected_reports:
        new_context_text, new_context = _report_context_text(report, attributes)
        new_tokens = num_tokens(new_context_text, token_encoder)

        # 如果超过令牌限制,切割批次
        # If token limit exceeded, cut batch
        if batch_tokens + new_tokens > max_tokens:
            # 将当前批次添加到上下文数据,如果是多批次模式则开始新批次
            # add the current batch to the context data and start a new batch if we are in multi-batch mode
            last_batch_added = True
            _cut_batch()
            if single_batch:
                break
            _init_batch()

        # 将当前报告添加到当前批次 / add current report to the current batch
        last_batch_added = False
        batch_text += new_context_text
        batch_tokens += new_tokens
        batch_records.append(new_context)

    # 如果最后一个批次尚未添加,则添加它 / add the last batch if it has not been added
    if not last_batch_added:
        last_batch_added = True
        _cut_batch()

    if len(all_context_records) == 0:
        log.warning(NO_COMMUNITY_RECORDS_WARNING)
        return ([], {})

    return all_context_text, {
        context_name.lower(): pd.concat(all_context_records, ignore_index=True)
        if len(all_context_records) > 0
        else None
    }


def _compute_community_weights(
    community_reports: list[CommunityReport],
    entities: list[Entity] | None,
    weight_attribute: str = "occurrence",
    normalize: bool = True,
) -> list[CommunityReport]:
    """
    计算社区权重,作为与社区内实体关联的文本单元数量。

    Calculate a community's weight as count of text units associated with entities within the community.

    参数 Parameters
    ----------
    - community_reports (list[CommunityReport]): 社区报告列表。Community reports list
    - entities (list[Entity] | None): 实体列表。Entities list
    - weight_attribute (str): 权重属性名。Weight attribute name
    - normalize (bool): 是否归一化权重。Whether to normalize weights

    返回 Returns
    -------
    - list[CommunityReport]: 添加了权重的社区报告列表。Community reports list with weights added
    """
    if not entities:
        return community_reports

    # 构建社区到文本单元的映射 / Build community to text units mapping
    community_text_units = {}
    for entity in entities:
        if entity.community_ids:
            for community_id in entity.community_ids:
                if community_id not in community_text_units:
                    community_text_units[community_id] = []
                community_text_units[community_id].extend(entity.text_unit_ids)

    # 为每个报告设置权重 / Set weight for each report
    for report in community_reports:
        if not report.attributes:
            report.attributes = {}
        # 使用集合去重计算唯一文本单元数量 / Use set to count unique text units
        report.attributes[weight_attribute] = len(
            set(community_text_units.get(report.community_id, []))
        )

    # 归一化权重 / Normalize weights
    if normalize:
        # 按最大权重归一化 / normalize by max weight
        all_weights = [
            report.attributes[weight_attribute]
            for report in community_reports
            if report.attributes
        ]
        max_weight = max(all_weights)
        for report in community_reports:
            if report.attributes:
                report.attributes[weight_attribute] = (
                    report.attributes[weight_attribute] / max_weight
                )
    return community_reports


def _rank_report_context(
    report_df: pd.DataFrame,
    weight_column: str | None = "occurrence weight",
    rank_column: str | None = "rank",
) -> pd.DataFrame:
    """
    按社区权重和排名对报告上下文进行排序(如果存在)。

    Sort report context by community weight and rank if exist.

    参数 Parameters
    ----------
    - report_df (pd.DataFrame): 报告 DataFrame。Report DataFrame
    - weight_column (str | None): 权重列名。Weight column name
    - rank_column (str | None): 排名列名。Rank column name

    返回 Returns
    -------
    - pd.DataFrame: 排序后的报告 DataFrame。Sorted report DataFrame
    """
    rank_attributes: list[str] = []
    if weight_column:
        rank_attributes.append(weight_column)
        report_df[weight_column] = report_df[weight_column].astype(float)
    if rank_column:
        rank_attributes.append(rank_column)
        report_df[rank_column] = report_df[rank_column].astype(float)
    # 按排名属性降序排序 / Sort by rank attributes in descending order
    if len(rank_attributes) > 0:
        report_df.sort_values(by=rank_attributes, ascending=False, inplace=True)
    return report_df


def _convert_report_context_to_df(
    context_records: list[list[str]],
    header: list[str],
    weight_column: str | None = None,
    rank_column: str | None = None,
) -> pd.DataFrame:
    """
    将报告上下文记录转换为 pandas dataframe,并按权重和排名排序(如果存在)。

    Convert report context records to pandas dataframe and sort by weight and rank if exist.

    参数 Parameters
    ----------
    - context_records (list[list[str]]): 上下文记录列表。Context records list
    - header (list[str]): 表头列表。Header list
    - weight_column (str | None): 权重列名。Weight column name
    - rank_column (str | None): 排名列名。Rank column name

    返回 Returns
    -------
    - pd.DataFrame: 转换后的 DataFrame。Converted DataFrame
    """
    if len(context_records) == 0:
        return pd.DataFrame()

    record_df = pd.DataFrame(
        context_records,
        columns=cast("Any", header),
    )
    return _rank_report_context(
        report_df=record_df,
        weight_column=weight_column,
        rank_column=rank_column,
    )
