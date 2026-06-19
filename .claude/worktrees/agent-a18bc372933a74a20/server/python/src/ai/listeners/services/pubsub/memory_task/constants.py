"""内存任务相关常量定义"""

import asyncio
from collections import defaultdict


ACTIVE_ASYNCIO_TASKS: dict[str, dict[str, asyncio.Task]] = defaultdict(dict)
"""存储活跃的异步任务，按任务类型分组"""

ACTIVE_CLEANUP_TASKS: dict[str, dict[str, asyncio.Task]] = defaultdict(dict)
"""存储活跃的清理任务，按任务类型分组"""

# 任务类型常量
TASK_TYPE_GENERATE_LLM = "generate:llm"
"""任务类型：大模型输出任务"""