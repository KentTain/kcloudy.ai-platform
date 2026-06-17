"""默认配置的参数化设置."""

from typing import NotRequired

from typing_extensions import TypedDict


class ClusterGraphConfigInput(TypedDict):
    """图聚类的配置部分."""

    max_cluster_size: NotRequired[int | None]
    strategy: NotRequired[dict | None]
