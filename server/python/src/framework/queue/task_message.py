"""
任务消息格式

定义标准的任务消息格式，支持租户上下文传递。
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from framework.tenant.context import get_tenant_id


@dataclass
class TaskMessage:
    """
    任务消息

    场景：任务消息结构
    WHEN 创建任务消息
    THEN 消息包含以下字段：
      - task_id: 任务唯一标识
      - task_type: 任务类型
      - payload: 任务负载数据
      - tenant_id: 租户 ID（自动填充）
      - created_at: 创建时间
    """

    task_type: str
    """任务类型"""

    payload: dict[str, Any]
    """任务负载数据"""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """任务唯一标识"""

    tenant_id: str | None = field(default=None)
    """租户 ID（自动填充）"""

    created_at: datetime = field(default_factory=datetime.now)
    """创建时间"""

    def __post_init__(self):
        """
        场景：任务入队自动携带租户 ID
        WHEN 在租户上下文为 `tenant_001` 时入队任务
        THEN 任务消息自动包含 `tenant_id: "tenant_001"`
        """
        if self.tenant_id is None:
            self.tenant_id = get_tenant_id()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMessage":
        """从字典创建"""
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            task_type=data["task_type"],
            payload=data.get("payload", {}),
            tenant_id=data.get("tenant_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TaskMessage":
        """从 JSON 字符串创建"""
        return cls.from_dict(json.loads(json_str))
