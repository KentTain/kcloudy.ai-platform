import inspect
import logging
from collections.abc import Callable
from typing import Any

from ai_plugin.server.core.runtime import Session
from ai_plugin.server.core.server.__base.request_reader import RequestReader
from ai_plugin.server.core.server.__base.response_writer import ResponseWriter


logger = logging.getLogger(__file__)


class Route:
    """路由类，封装路由过滤器和处理函数"""

    filter: Callable[[dict], bool]  # 路由过滤器函数
    func: Callable  # 路由处理函数

    def __init__(self, filter: Callable[[dict], bool], func) -> None:
        """
        初始化路由

        Args:
            filter: 过滤器函数，用于判断是否匹配当前路由
            func: 路由处理函数
        """
        self.filter = filter
        self.func = func


class Router:
    """路由器类，负责注册和分发路由请求"""

    routes: list[Route]  # 路由列表
    request_reader: RequestReader  # 请求读取器

    def __init__(
        self, request_reader: RequestReader, response_writer: ResponseWriter | None
    ) -> None:
        """
        初始化路由器

        Args:
            request_reader: 请求读取器
            response_writer: 可选的响应写入器
        """
        self.routes = []
        self.request_reader = request_reader
        self.response_writer = response_writer

    def register_route(
        self, f: Callable, filter: Callable[[dict], bool], instance: Any = None
    ):
        """
        注册路由

        Args:
            f: 路由处理函数
            filter: 路由过滤器函数
            instance: 可选的实例对象，用于实例方法的路由

        Raises:
            ValueError: 当路由函数参数不足时抛出异常

        根据函数签名自动包装参数验证和错误处理逻辑
        """
        # 获取函数签名信息
        sig = inspect.signature(f)
        parameters = list(sig.parameters.values())
        if len(parameters) == 0:
            raise ValueError("路由函数必须至少有一个参数")

        if instance:
            # 处理实例方法路由
            # 获取第三个参数（跳过self和session）
            parameter = parameters[2]
            # 获取参数的类型注解
            annotation = parameter.annotation

            def wrapper(session: Session, data: dict):
                """
                实例方法路由包装器

                Args:
                    session: 会话对象
                    data: 请求数据字典

                对请求数据进行类型验证，如果失败则发送错误响应
                """
                try:
                    data = annotation(**data)
                except TypeError as e:
                    if not self.response_writer:
                        logger.exception("路由请求失败: %s")
                    else:
                        self.response_writer.error(
                            session_id=session.session_id,
                            data={"error": str(e), "error_type": type(e).__name__},
                        )
                return f(instance, session, data)
        else:
            # 处理普通函数路由
            # 获取第二个参数（跳过session）
            parameter = parameters[1]
            # 获取参数的类型注解
            annotation = parameter.annotation

            def wrapper(session: Session, data: dict):
                """
                普通函数路由包装器

                Args:
                    session: 会话对象
                    data: 请求数据字典

                对请求数据进行类型验证，如果失败则发送错误响应
                """
                try:
                    data = annotation(**data)
                except TypeError as e:
                    if not self.response_writer:
                        logger.exception("路由请求失败: %s")
                    else:
                        self.response_writer.error(
                            session_id=session.session_id,
                            data={"error": str(e), "error_type": type(e).__name__},
                        )
                return f(session, data)

        # 将包装后的函数添加到路由列表
        self.routes.append(Route(filter, wrapper))

    def dispatch(self, session: Session, data: dict) -> Any:
        """
        分发请求到匹配的路由

        Args:
            session: 会话对象
            data: 请求数据字典

        Returns:
            Any: 路由处理函数的返回值，如果没有匹配的路由则返回None

        遍历所有注册的路由，找到第一个匹配的路由并执行其处理函数
        """
        for route in self.routes:
            if route.filter(data):
                return route.func(session, data)
