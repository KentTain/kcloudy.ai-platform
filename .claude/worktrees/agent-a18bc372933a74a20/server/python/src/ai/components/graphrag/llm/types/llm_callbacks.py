"""
LLM 回调函数类型定义

定义了 LLM 模块使用的各种回调函数类型。
"""

from collections.abc import Callable

from ai.components.graphrag.llm.types.llm_invocation_result import LLMInvocationResult

# 错误处理函数类型定义
# 参数:异常对象,堆栈跟踪字符串,额外的调试信息字典
ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]
"""错误处理函数类型,用于处理 LLM 调用过程中的错误"""

# LLM 调用结果处理函数类型定义
# 参数:LLM 调用结果对象
LLMInvocationFn = Callable[[LLMInvocationResult], None]
"""LLM 调用结果处理函数类型,用于处理 LLM 调用完成后的结果"""

# 缓存操作处理函数类型定义
# 参数:缓存键,操作名称(可选)
OnCacheActionFn = Callable[[str, str | None], None]
"""缓存操作处理函数类型,用于处理缓存命中或未命中事件"""

# 响应验证函数类型定义
# 参数:LLM 响应字典
# 返回:是否有效
IsResponseValidFn = Callable[[dict], bool]
"""响应验证函数类型,用于检查 LLM 响应是否有效"""
