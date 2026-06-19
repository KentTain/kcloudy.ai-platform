"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class LocalSearchConfigInput(TypedDict):
    """本地搜索的默认配置部分."""

    text_unit_prop: NotRequired[float | str | None]
    community_prop: NotRequired[float | str | None]
    conversation_history_max_turns: NotRequired[int | str | None]
    top_k_entities: NotRequired[int | str | None]
    top_k_relationships: NotRequired[int | str | None]
    max_tokens: NotRequired[int | str | None]
    llm_max_tokens: NotRequired[int | str | None]
