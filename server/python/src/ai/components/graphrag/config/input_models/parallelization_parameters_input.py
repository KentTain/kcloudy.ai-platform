"""并行化参数模型."""

from typing import NotRequired

from typing_extensions import TypedDict


class ParallelizationParametersInput(TypedDict):
    """并行化参数模型."""

    stagger: NotRequired[float | str | None]
    num_threads: NotRequired[int | str | None]
