"""
领域事件基类

定义领域事件的基础结构。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class DomainEvent:
    """
    领域事件基类

    所有领域事件都应继承此类。事件是不可变的，携带特定业务含义。

    Attributes:
        event_id: 事件唯一标识
        event_type: 事件类型（自动从类名获取）
        timestamp: 事件发生时间
        metadata: 扩展元数据
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初始化后自动设置事件类型"""
        self.event_type = self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典格式

        Returns:
            事件数据的字典表示
        """
        data = asdict(self)
        # 处理 datetime 序列化
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """
        转换为 JSON 字符串

        Returns:
            事件的 JSON 字符串表示
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def get_stream_name(cls) -> str:
        """
        获取事件流名称

        默认使用类名转换为下划线格式。
        例如：ModuleAssigned -> module_assigned_events

        Returns:
            Redis Stream 名称
        """
        # 将驼峰命名转换为下划线命名
        name = cls.__name__
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return f"{''.join(result)}_events"


class EventStream:
    """
    事件流常量

    定义所有领域事件的流名称。
    """

    # 模块分配事件流
    MODULE_ASSIGNED = "module_assigned_events"
    MODULE_UNASSIGNED = "module_unassigned_events"

    # 模块菜单事件流
    MODULE_MENU_CREATED = "module_menu_created_events"
    MODULE_MENU_UPDATED = "module_menu_updated_events"
    MODULE_MENU_DELETED = "module_menu_deleted_events"

    # 模块权限事件流
    MODULE_PERMISSION_CREATED = "module_permission_created_events"
    MODULE_PERMISSION_UPDATED = "module_permission_updated_events"
    MODULE_PERMISSION_DELETED = "module_permission_deleted_events"

    # 模块角色事件流
    MODULE_ROLE_CREATED = "module_role_created_events"
    MODULE_ROLE_UPDATED = "module_role_updated_events"
    MODULE_ROLE_DELETED = "module_role_deleted_events"
    MODULE_ROLE_PERMISSION_CHANGED = "module_role_permission_changed_events"
