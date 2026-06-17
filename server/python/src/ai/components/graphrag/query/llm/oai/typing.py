"""OpenAI 封装器选项。

OpenAI wrapper options.
"""

from enum import Enum
from typing import Any, cast

import openai

# OpenAI 重试错误类型 / OpenAI retry error types
OPENAI_RETRY_ERROR_TYPES = (
    # TODO: 更新到 OpenAI 1+ 库时更新这些 / update these when we update to OpenAI 1+ library
    cast("Any", openai).RateLimitError,
    cast("Any", openai).APIConnectionError,
    # TODO: 替换为 OpenAI 1+ 的对应错误 / replace with comparable OpenAI 1+ error
)


class OpenaiApiType(str, Enum):
    """
    OpenAI 类型枚举。

    The OpenAI Flavor.
    """

    OpenAI = "openai"
    AzureOpenAI = "azure"
