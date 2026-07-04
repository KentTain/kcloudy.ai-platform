# server/python/src/extended/langchain/callbacks/reasoning_types.py

"""推理步骤类型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class ReasoningStepType(str, Enum):
    """推理步骤类型枚举

    用于区分不同类型的推理步骤，帮助用户理解 AI 的思考过程。
    """

    REASONING = "reasoning"              # 推理分析
    DECISION = "decision"                # 决策制定
    TOOL_SELECTION = "tool_selection"    # 工具选择
    TOOL_EXECUTION = "tool_execution"    # 工具执行
    RESULT_ANALYSIS = "result_analysis"  # 结果分析
    ERROR_HANDLING = "error_handling"    # 错误处理


@dataclass
class ReasoningStep:
    """推理步骤数据结构

    表示推理过程中的一个步骤，包含步骤的基本信息和内容。

    Attributes:
        id: 步骤唯一标识符
        step_type: 步骤类型
        title: 步骤标题（可选）
        content: 步骤内容
        parent_id: 父步骤 ID（用于嵌套推理）
        metadata: 元数据
        created_at: 创建时间
    """

    id: str = field(default_factory=lambda: f"thinking-{uuid.uuid4().hex[:8]}")
    step_type: ReasoningStepType = ReasoningStepType.REASONING
    title: str | None = None
    content: str = ""
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，用于 SSE 事件

        Returns:
            包含步骤信息的字典
        """
        result = {
            "id": self.id,
            "stepType": self.step_type.value,
        }
        if self.title:
            result["title"] = self.title
        if self.content:
            result["delta"] = self.content
        return result
