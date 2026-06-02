import asyncio
import functools
import inspect
import json
from collections.abc import AsyncGenerator, Callable

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from framework.configs.settings import Settings


REMOTABLE_REGISTRY: dict[str, type] = {}
"""全局注册表，用于存储所有被@remotable装饰的类。"""


class RemotableRequest(BaseModel):
    """远程调用请求模型"""

    args: list = []
    kwargs: dict = {}


class Remotable:
    """
    一个装饰器，使类的方法可以根据应用程序设置在本地或远程通过HTTP API调用。
    如果服务配置为这样做，它还会自动将类的方法公开为HTTP端点。

    用法:
        @Remotable()
        class MyService:
            def my_method(self, arg1: str) -> str:
                return f"Hello, {arg1}"

    参数:
        name: 可选的类名，如果不提供则使用类的原始名称
    """

    def __init__(self, name: str | None = None):
        """
        初始化Remotable装饰器。

        Args:
            name: 可选的类名，用于在注册表中标识该类
        """
        self.name = name

    def __call__(self, cls: type) -> type:
        """
        装饰器的实际执行逻辑，对传入的类进行包装。

        Args:
            cls: 被装饰的类

        Returns:
            包装后的类

        """
        if not self.name:
            self.name = cls.__name__

        # 包装公共方法以允许远程/本地切换
        for attr_name, attr_value in inspect.getmembers(cls):
            if not attr_name.startswith("_") and (
                inspect.isfunction(attr_value) or inspect.ismethod(attr_value)
            ):
                # 跳过构造函数
                if attr_name == "__init__":
                    continue

                original_method = attr_value

                # 如果是绑定方法，获取原始函数（修复类型检查器错误）
                if hasattr(original_method, "__func__") and inspect.ismethod(
                    original_method
                ):
                    original_method = original_method.__func__

                # 创建包装方法
                wrapped_method = self._create_wrapper(cls, self.name, original_method)
                setattr(cls, attr_name, wrapped_method)

        return cls

    def _create_wrapper(
        self, cls: type, class_name: str, original_method: Callable
    ) -> Callable:
        """
        为原始方法创建一个包装器，该包装器可以根据配置决定本地或远程调用。

        Args:
            cls: 类对象
            class_name: 类名
            original_method: 原始方法

        Returns:
            包装后的异步方法
        """

        @functools.wraps(original_method)
        async def wrapper(self_or_instance, *args, **kwargs):
            """
            方法包装器，根据配置选择本地或远程调用。

            在类方法调用中，第一个参数是`self`。
            当从静态上下文调用时，它可能是类本身。
            我们需要处理这两种情况。
            """

            # 判断方法是在实例上调用还是在类上调用
            is_instance_method = not inspect.isclass(self_or_instance)

            if Settings().plugin.invocation_mode == "remote":
                # 远程调用逻辑
                client = httpx.AsyncClient()
                try:
                    # 第一个参数是'self'，远程调用时不需要发送
                    remote_args = args[1:] if is_instance_method else args

                    # 构建远程调用的URL
                    url = f"{Settings().plugin.remote_plugin_base_url}/{Settings().plugin.remote_plugin_dispatch_path}/dispatch/{class_name}/{original_method.__name__}"

                    # 发送HTTP POST请求
                    response = await client.post(
                        url,
                        json={"args": remote_args, "kwargs": kwargs},
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    return response.json()
                finally:
                    await client.aclose()
            else:
                # 本地调用逻辑
                if inspect.iscoroutinefunction(original_method):
                    # 如果是协程函数，直接await调用
                    return await original_method(self_or_instance, *args, **kwargs)
                else:
                    # 如果是同步方法，在线程池中执行以避免阻塞事件循环
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None,
                        functools.partial(
                            original_method, self_or_instance, *args, **kwargs
                        ),
                    )

        # 即使原始方法不是异步的，我们仍然返回异步包装器以保持一致性
        # 这简化了调用逻辑，因为所有包装的方法都是可等待的。
        return wrapper


async def _stream_async_generator_results(async_gen: AsyncGenerator):
    """
    将 AsyncGenerator 的结果作为流式响应输出

    Args:
        async_gen: 异步生成器

    Yields:
        JSON 格式的字符串，每行一个对象
    """
    async for item in async_gen:
        # 确保正确序列化 Pydantic 模型，包括枚举类型
        if hasattr(item, "model_dump"):
            # 使用 Pydantic 的 model_dump 方法，确保枚举等特殊类型被正确序列化
            data = item.model_dump(mode="json")
        elif hasattr(item, "dict"):
            # 兼容老版本的 Pydantic
            data = item.dict()
        else:
            # 对于普通对象，尝试直接使用
            data = item

        try:
            # 每个对象作为一行JSON输出，使用换行符分隔
            yield f"{json.dumps(data, ensure_ascii=False, default=str)}\n"
        except (TypeError, ValueError) as e:
            # 如果序列化失败，记录错误并跳过该项
            error_data = {
                "error": f"序列化失败: {str(e)}",
                "item_type": str(type(item)),
                "item_str": str(item)[:200] + "..."
                if len(str(item)) > 200
                else str(item),
            }
            yield f"{json.dumps(error_data, ensure_ascii=False)}\n"


def register_remotable_class():
    """
    注册一个remotable类
    """
    from ai.components.plugin.client.model_client import ModelClient
    from ai.components.plugin.client.tool_client import ToolClient

    REMOTABLE_REGISTRY["tool"] = ToolClient
    REMOTABLE_REGISTRY["model"] = ModelClient


def create_remotable_router() -> APIRouter:
    """
    创建一个FastAPI APIRouter，将所有注册的@Remotable类
    及其方法公开为HTTP端点。

    Returns:
        配置好的APIRouter实例
    """
    router = APIRouter()

    register_remotable_class()

    for class_name, cls in REMOTABLE_REGISTRY.items():
        # 创建类的实例，用于端点使用。
        # 这假设该类有一个可以不带参数调用的构造函数。
        # 对于依赖注入，这需要更复杂的处理。
        try:
            instance = cls()
        except Exception:
            # 如果失败，我们假设它需要FastAPI提供的依赖项。
            instance = None

        # 遍历类的所有方法
        for attr_name, method in inspect.getmembers(cls):
            if not attr_name.startswith("_") and (
                inspect.isfunction(method) or inspect.ismethod(method)
            ):
                if attr_name == "__init__":
                    continue

                # 要调用的实际函数是原始的、未包装的函数（修复类型检查器错误）
                original_method = method
                # 安全地获取__wrapped__属性，如果存在的话 (忽略类型检查器错误)
                wrapped_method = getattr(method, "__wrapped__", None)
                if wrapped_method is not None:
                    original_method = wrapped_method

                # 使用闭包捕获方法和实例，避免在函数参数中使用Callable类型
                def create_endpoint(captured_method, captured_instance, captured_cls):
                    async def endpoint(request: Request, body: RemotableRequest):
                        """
                        处理远程方法调用的HTTP端点。

                        Args:
                            request: FastAPI请求对象
                            body: 请求体，包含方法参数

                        Returns:
                            方法执行的结果（可能是普通结果或流式响应）
                        """
                        # 如果没有创建实例，我们假设它应该由FastAPI的依赖注入系统创建。
                        target_instance = captured_instance
                        if target_instance is None:
                            # 这是一个简化的依赖注入方法。真正的实现可能需要更强大的依赖解析器。
                            if hasattr(request.app.state, "container"):
                                target_instance = await request.app.state.container.get(
                                    captured_cls
                                )
                            else:
                                # 如果没有容器，尝试创建实例
                                target_instance = captured_cls()

                        # 获取请求参数
                        args = body.args
                        kwargs = body.kwargs

                        # 在实例上调用原始的、未包装的方法
                        if inspect.iscoroutinefunction(captured_method):
                            result = await captured_method(
                                target_instance, *args, **kwargs
                            )
                        else:
                            result = captured_method(target_instance, *args, **kwargs)

                        # 检查结果是否是 AsyncGenerator，如果是则返回流式响应
                        if inspect.isasyncgen(result):
                            return StreamingResponse(
                                _stream_async_generator_results(result),
                                media_type="text/event-stream",  # 使用 NDJSON (换行分隔的JSON) 格式
                                headers={
                                    "X-Content-Type": "stream",
                                    "Cache-Control": "no-cache",
                                    "Connection": "keep-alive",
                                },
                            )

                        return result

                    return endpoint

                # 创建API端点
                endpoint_func = create_endpoint(original_method, instance, cls)
                router.post(
                    f"/dispatch/{class_name}/{attr_name}",
                    name=f"remotable:{class_name}:{attr_name}",
                    summary=f"调用 {class_name}.{attr_name} 方法",
                    description=f"远程调用 {class_name} 类的 {attr_name} 方法（支持流式响应）",
                )(endpoint_func)

    return router


# 为了更容易使用的别名
remotable = Remotable
