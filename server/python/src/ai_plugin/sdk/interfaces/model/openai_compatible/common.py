import requests

from ai_plugin.sdk.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)


class _CommonOaiApiCompat:
    """OpenAI API兼容的通用类"""

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        将模型调用错误映射到统一错误
        键是抛出给调用者的错误类型
        值是模型抛出的错误类型，需要转换为统一的错误类型给调用者

        :return: 调用错误映射
        """
        return {
            InvokeAuthorizationError: [
                requests.exceptions.InvalidHeader,  # 缺失或无效的API密钥
            ],
            InvokeBadRequestError: [
                requests.exceptions.HTTPError,  # 无效的端点URL或模型名称
                requests.exceptions.InvalidURL,  # 请求配置错误或其他API错误
            ],
            InvokeRateLimitError: [
                requests.exceptions.RetryError,  # 在短时间内发送了太多请求
            ],
            InvokeServerUnavailableError: [
                requests.exceptions.ConnectionError,  # 引擎过载
                requests.exceptions.HTTPError,  # 服务器错误
            ],
            InvokeConnectionError: [
                requests.exceptions.ConnectTimeout,  # 连接超时
                requests.exceptions.ReadTimeout,  # 读取超时
            ],
        }
