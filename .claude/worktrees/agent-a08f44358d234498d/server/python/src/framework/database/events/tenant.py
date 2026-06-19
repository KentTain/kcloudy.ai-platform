"""
租户事件

提供多租户隔离的事件监听。
"""

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from framework.common.ctx import get_tenant_id
from framework.database.mixins.tenant import should_skip_tenant


class TenantEventListener:
    """租户事件监听器"""

    @staticmethod
    def before_insert(mapper: Any, connection: Any, target: Any) -> None:
        """插入前事件 - 自动设置租户 ID

        场景：插入数据自动填充 tenant_id
        WHEN 创建新记录且未指定 tenant_id
        THEN 自动从 TenantContext 获取当前租户 ID 并填充

        场景：管理员场景跳过自动填充
        WHEN 设置 skip_tenant=True 标志
        THEN 不自动填充 tenant_id
        """
        # 检查是否跳过租户过滤
        if should_skip_tenant():
            return

        if hasattr(target, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id and target.tenant_id is None:
                target.tenant_id = tenant_id

    @staticmethod
    def before_update(mapper: Any, connection: Any, target: Any) -> None:
        """更新前事件 - 防止修改 tenant_id"""
        # 可以在这里添加逻辑防止租户 ID 被篡改
        pass

    @staticmethod
    def before_delete(mapper: Any, connection: Any, target: Any) -> None:
        """删除前事件 - 可用于级联清理"""
        pass


def register_tenant_events(base_class: type) -> None:
    """
    注册租户事件监听器

    Args:
        base_class: 基础模型类
    """
    event.listen(base_class, "before_insert", TenantEventListener.before_insert)
    event.listen(base_class, "before_update", TenantEventListener.before_update)
    event.listen(base_class, "before_delete", TenantEventListener.before_delete)


class TenantQueryInterceptor:
    """租户查询拦截器"""

    @staticmethod
    def inject_tenant_filter(query: Any, model_class: type) -> Any:
        """
        注入租户过滤条件

        场景：查询自动过滤
        WHEN 执行查询操作
        THEN 自动添加 WHERE tenant_id = :current_tenant_id 条件

        场景：管理员场景跳过自动过滤
        WHEN 设置 skip_tenant=True 标志
        THEN 不添加 tenant_id 过滤条件

        Args:
            query: 查询对象
            model_class: 模型类

        Returns:
            添加租户过滤后的查询
        """
        # 检查是否跳过租户过滤
        if should_skip_tenant():
            return query

        if hasattr(model_class, "tenant_id"):
            tenant_id = get_tenant_id()
            if tenant_id:
                query = query.where(model_class.tenant_id == tenant_id)

        return query
