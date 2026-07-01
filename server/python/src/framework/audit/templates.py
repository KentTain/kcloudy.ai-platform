"""
审计日志模板

提供审计日志 detail 字段的模板构建功能。
"""

from typing import Any


class AuditTemplateBuilder:
    """审计日志模板构建器"""

    # 操作类型中文映射
    ACTION_LABELS = {
        "create": "创建",
        "update": "更新",
        "delete": "删除",
        "enable": "启用",
        "disable": "禁用",
        "assign": "分配",
        "remove": "移除",
    }

    # 资源类型中文映射
    RESOURCE_LABELS = {
        "user": "用户",
        "role": "角色",
        "organization": "组织",
        "permission": "权限",
        "menu": "菜单",
    }

    def build_template_key(self, module: str, resource: str, action: str) -> str:
        """
        构建模板 Key

        Args:
            module: 模块名称
            resource: 资源类型
            action: 操作类型

        Returns:
            模板 Key，格式：audit.{module}.{resource}.{action}
        """
        return f"audit.{module}.{resource}.{action}"

    def build_detail(
        self,
        module: str,
        resource: str,
        action: str,
        operator_name: str,
        operated_at: str,
        resource_name: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        构建 detail 字段

        Args:
            module: 模块名称
            resource: 资源类型
            action: 操作类型
            operator_name: 操作人名称
            operated_at: 操作时间
            resource_name: 资源名称
            extra: 额外信息

        Returns:
            detail 字典
        """
        # 获取操作类型标签
        action_label = self.ACTION_LABELS.get(action, action)

        # 获取资源类型标签
        resource_label = self.RESOURCE_LABELS.get(resource, resource)

        # 构建文本
        text = f'{operator_name}在{operated_at}对{resource_label}"{resource_name}"进行了{action_label}操作'

        # 构建模板 Key
        template_key = self.build_template_key(module, resource, action)

        # 构建参数
        params = {
            "operator_name": operator_name,
            "operated_at": operated_at,
            "resource_name": resource_name,
            "operation_type": action_label,
        }

        # 构建 detail
        detail = {
            "text": text,
            "template_key": template_key,
            "params": params,
        }

        # 添加额外信息
        if extra:
            detail["extra"] = extra

        return detail
