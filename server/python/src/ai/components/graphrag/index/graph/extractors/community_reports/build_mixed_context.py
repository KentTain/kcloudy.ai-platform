"""包含build_mixed_context方法定义的模块."""

import pandas as pd

from ai.components.graphrag.index.graph.extractors.community_reports import schemas
from ai.components.graphrag.index.graph.extractors.community_reports.sort_context import (
    sort_context,
)
from ai.components.graphrag.query.llm.text_utils import num_tokens


def build_mixed_context(context: list[dict], max_tokens: int) -> str:
    """
    通过连接所有子社区的上下文来构建父上下文。

    如果上下文超过限制,我们使用子社区报告代替。
    """
    sorted_context = sorted(
        context, key=lambda x: x[schemas.CONTEXT_SIZE], reverse=True
    )

    # 用子社区报告替换本地上下文,从最大的子社区开始
    substitute_reports = []
    final_local_contexts = []
    exceeded_limit = True
    context_string = ""

    for idx, sub_community_context in enumerate(sorted_context):
        if exceeded_limit:
            if sub_community_context[schemas.FULL_CONTENT]:
                substitute_reports.append(
                    {
                        schemas.COMMUNITY_ID: sub_community_context[
                            schemas.SUB_COMMUNITY
                        ],
                        schemas.FULL_CONTENT: sub_community_context[
                            schemas.FULL_CONTENT
                        ],
                    }
                )
            else:
                # 这个子社区没有报告,所以我们使用它的本地上下文
                final_local_contexts.extend(sub_community_context[schemas.ALL_CONTEXT])
                continue

            # 为剩余的子社区添加本地上下文
            remaining_local_context = []
            for rid in range(idx + 1, len(sorted_context)):
                remaining_local_context.extend(sorted_context[rid][schemas.ALL_CONTEXT])
            new_context_string = sort_context(
                local_context=remaining_local_context + final_local_contexts,
                sub_community_reports=substitute_reports,
            )
            if num_tokens(new_context_string) <= max_tokens:
                exceeded_limit = False
                context_string = new_context_string
                break

    if exceeded_limit:
        # 如果所有子社区报告都超过限制,我们添加报告直到上下文满
        substitute_reports = []
        for sub_community_context in sorted_context:
            substitute_reports.append(
                {
                    schemas.COMMUNITY_ID: sub_community_context[schemas.SUB_COMMUNITY],
                    schemas.FULL_CONTENT: sub_community_context[schemas.FULL_CONTENT],
                }
            )
            new_context_string = pd.DataFrame(substitute_reports).to_csv(
                index=False, sep=","
            )
            if num_tokens(new_context_string) > max_tokens:
                break

            context_string = new_context_string
    return context_string
