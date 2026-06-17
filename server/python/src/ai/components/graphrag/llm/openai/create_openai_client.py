"""创建 OpenAI 客户端实例模块。

本模块提供创建 OpenAI 和 Azure OpenAI 客户端的工厂函数。
支持标准 OpenAI API 和 Azure OpenAI 服务两种模式。
"""

import logging
from functools import cache

from openai import AsyncOpenAI

from ai.components.graphrag.llm.openai.openai_configuration import OpenAIConfiguration
from ai.components.graphrag.llm.openai.types import OpenAIClientTypes

log = logging.getLogger(__name__)

# 错误提示常量
API_BASE_REQUIRED_FOR_AZURE = "api_base is required for Azure OpenAI client"


def _get_azure_identity_deps():
    """
    延迟导入 Azure Identity 依赖.

    Lazily import Azure Identity dependencies.
    """
    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        return DefaultAzureCredential, get_bearer_token_provider
    except ImportError as e:
        msg = "Azure Identity 依赖未安装，请执行: pip install azure-identity"
        raise ImportError(msg) from e


@cache
def create_openai_client(
    configuration: OpenAIConfiguration, azure: bool
) -> OpenAIClientTypes:
    """
    创建openai_client。

    Args:
        configuration (OpenAIConfiguration): configuration 参数。
        azure (bool): azure 参数。

    Returns:
        处理结果。
    """
    if azure:
        # 延迟导入 Azure 依赖
        DefaultAzureCredential, get_bearer_token_provider = _get_azure_identity_deps()
        from openai import AsyncAzureOpenAI

        # Azure OpenAI 模式
        api_base = configuration.api_base
        if api_base is None:
            raise ValueError(API_BASE_REQUIRED_FOR_AZURE)

        log.info(
            "Creating Azure OpenAI client api_base=%s, deployment_name=%s",
            api_base,
            configuration.deployment_name,
        )

        # 设置认知服务端点
        if configuration.cognitive_services_endpoint is None:
            cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
        else:
            cognitive_services_endpoint = configuration.cognitive_services_endpoint

        return AsyncAzureOpenAI(
            api_key=configuration.api_key if configuration.api_key else None,
            # 如果没有提供 API 密钥,则使用 Azure AD 令牌提供器
            azure_ad_token_provider=get_bearer_token_provider(
                DefaultAzureCredential(), cognitive_services_endpoint
            )
            if not configuration.api_key
            else None,
            organization=configuration.organization,
            # Azure 特定配置
            api_version=configuration.api_version,
            azure_endpoint=api_base,
            azure_deployment=configuration.deployment_name,
            # 超时/重试配置 - 使用 Tenacity 进行重试,因此在此禁用内置重试
            timeout=configuration.request_timeout or 180.0,
            max_retries=0,
        )

    # 标准 OpenAI 模式
    log.info("Creating OpenAI client base_url=%s", configuration.api_base)
    return AsyncOpenAI(
        api_key=configuration.api_key,
        base_url=configuration.api_base,
        organization=configuration.organization,
        # 超时/重试配置 - 使用 Tenacity 进行重试,因此在此禁用内置重试
        timeout=configuration.request_timeout or 180.0,
        max_retries=0,
    )
