"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class EmbedGraphConfigInput(TypedDict):
    """Node2Vec 的默认配置部分."""

    enabled: NotRequired[bool | str | None]
    num_walks: NotRequired[int | str | None]
    walk_length: NotRequired[int | str | None]
    window_size: NotRequired[int | str | None]
    iterations: NotRequired[int | str | None]
    random_seed: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
