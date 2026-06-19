"""
AI 模型基类

迁移自 Alon: src/alon/components/model/model_providers/__base__/ai_model.py

所有模型提供者的基础实现类，通过插件系统调用实际的模型服务
"""

import asyncio
import decimal
import hashlib

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from ai.components.model.entities.plugin_entities import PluginModelProviderEntity
from ai.components.model.errors.error import (
    ModelCredentialError,
    ModelInvocationError,
    ModelTimeoutError,
)
from ai.components.plugin.client.model_client import ModelClient
from ai_plugin.sdk.entities.model import (
    PARAMETER_RULE_TEMPLATE,
    AIModelEntity,
    DefaultParameterName,
    ModelType,
    PriceConfig,
    PriceInfo,
    PriceType,
)
from ai_plugin.sdk.errors.invoke import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)

_logger = logger.bind(name=__name__)


class AIModelImpl(BaseModel):
    """
    所有模型的基础类

    提供模型的通用功能，包括价格计算、模型结构获取、错误转换等
    """

    tenant_id: str = Field(description="租户ID")
    model_type: ModelType = Field(description="模型类型")
    plugin_id: str = Field(description="插件ID")
    provider_name: str = Field(description="供应商")
    plugin_model_provider: PluginModelProviderEntity = Field(
        description="插件模型供应商"
    )
    started_at: float = Field(description="调用开始时间", default=0)

    # pydantic 配置
    model_config = ConfigDict(protected_namespaces=())

    @property
    def _invoke_error_mapping(self) -> dict[type[Exception], list[type[Exception]]]:
        """
        将模型调用错误映射到统一错误类型

        key 是抛给调用者的错误类型
        value 是模型抛出的错误类型，需要转换为统一错误类型供调用者使用

        :return: 调用错误映射关系
        """
        return {
            InvokeConnectionError: [InvokeConnectionError],
            InvokeServerUnavailableError: [InvokeServerUnavailableError],
            InvokeRateLimitError: [InvokeRateLimitError],
            InvokeAuthorizationError: [InvokeAuthorizationError],
            InvokeBadRequestError: [InvokeBadRequestError],
            ValueError: [ValueError],
        }

    def _transform_invoke_error(self, error: Exception) -> Exception:
        """
        转换调用错误为统一错误类型

        将插件通信错误、超时错误、凭证错误转换为相应的模型错误

        :param error: 模型调用错误
        :return: 统一错误类型
        """
        # 处理超时错误
        if isinstance(error, asyncio.TimeoutError):
            return ModelTimeoutError(
                message=f"[{self.provider_name}] 模型调用超时: {str(error)}",
            )

        # 处理凭证错误
        if isinstance(error, InvokeAuthorizationError):
            return ModelCredentialError(
                message=f"[{self.provider_name}] 模型凭证无效: {str(error)}",
                provider=self.provider_name,
            )

        # 处理连接错误 -> 模型调用错误
        if isinstance(error, InvokeConnectionError):
            return ModelInvocationError(
                message=f"[{self.provider_name}] 插件通信失败: {str(error)}",
                original_error=error,
            )

        # 处理服务器不可用错误 -> 模型调用错误
        if isinstance(error, InvokeServerUnavailableError):
            return ModelInvocationError(
                message=f"[{self.provider_name}] 模型服务不可用: {str(error)}",
                original_error=error,
            )

        # 遍历错误映射，查找匹配的错误类型
        for invoke_error, model_errors in self._invoke_error_mapping.items():
            if isinstance(error, tuple(model_errors)):
                if isinstance(invoke_error, InvokeError):
                    return ModelInvocationError(
                        message=f"[{self.provider_name}] {invoke_error.description}: {str(error)}",
                        original_error=error,
                    )
                else:
                    return error

        # 默认返回模型调用错误
        return ModelInvocationError(
            message=f"[{self.provider_name}] 模型调用错误: {str(error)}",
            original_error=error,
        )

    async def get_price(
        self, model: str, credentials: dict, price_type: PriceType, tokens: int
    ) -> PriceInfo:
        """
        获取给定模型和 token 数量的价格信息

        :param model: 模型名称
        :param credentials: 模型凭证
        :param price_type: 价格类型（输入/输出）
        :param tokens: token 数量
        :return: 价格信息
        """
        # 获取模型结构配置
        model_schema = await self.get_model_schema(model, credentials)

        # 从预定义的模型结构中获取价格信息
        price_config: PriceConfig | None = None
        if model_schema and model_schema.pricing:
            price_config = model_schema.pricing

        # 获取单价
        unit_price = None
        if price_config:
            if price_type == PriceType.INPUT:
                unit_price = price_config.input
            elif price_type == PriceType.OUTPUT and price_config.output is not None:
                unit_price = price_config.output

        # 如果没有价格配置，返回零价格
        if unit_price is None:
            return PriceInfo(
                unit_price=decimal.Decimal("0.0"),
                unit=decimal.Decimal("0.0"),
                total_amount=decimal.Decimal("0.0"),
                currency="USD",
            )

        # 计算总费用
        if not price_config:
            raise ValueError(f"未找到模型 {model} 的价格配置")
        total_amount = tokens * unit_price * price_config.unit
        total_amount = total_amount.quantize(
            decimal.Decimal("0.0000001"), rounding=decimal.ROUND_HALF_UP
        )

        return PriceInfo(
            unit_price=unit_price,
            unit=price_config.unit,
            total_amount=total_amount,
            currency=price_config.currency,
        )

    async def get_model_schema(
        self, model: str, credentials: dict | None = None
    ) -> AIModelEntity | None:
        """
        根据模型名称和凭证获取模型结构配置

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型结构配置
        """
        # 构建缓存键，包含租户、插件、供应商、模型类型和模型名称
        cache_key = f"{self.tenant_id}:{self.plugin_id}:{self.provider_name}:{self.model_type.value}:{model}"
        # 对凭证进行排序并生成 MD5 哈希
        sorted_credentials = sorted(credentials.items()) if credentials else []
        cache_key += ":".join(
            [
                hashlib.md5(f"{k}:{v}".encode()).hexdigest()
                for k, v in sorted_credentials
            ]
        )

        model_client = ModelClient()

        # 从插件管理器获取模型结构
        schema = await model_client.get_model_schema(
            tenant_id=self.tenant_id,
            user_id="unknown",
            plugin_id=self.plugin_id,
            provider=self.provider_name,
            model_type=self.model_type,
            model=model,
            credentials=credentials or {},
        )

        return schema

    async def get_customizable_model_schema_from_credentials(
        self,
        model: str,
        credentials: dict,
    ) -> AIModelEntity | None:
        """
        从凭证中获取可自定义的模型结构配置

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型结构配置
        """
        # 获取可自定义的模型结构配置
        schema = await self.get_customizable_model_schema(model, credentials)
        if not schema:
            return None

        # 填充模板参数
        new_parameter_rules = []
        for parameter_rule in schema.parameter_rules:
            if parameter_rule.use_template:
                try:
                    # 解析默认参数名称
                    default_parameter_name = DefaultParameterName.value_of(
                        parameter_rule.use_template
                    )
                    default_parameter_rule = (
                        self._get_default_parameter_rule_variable_map(
                            default_parameter_name
                        )
                    )
                    # 填充缺失的参数配置
                    if not parameter_rule.max and "max" in default_parameter_rule:
                        parameter_rule.max = default_parameter_rule["max"]
                    if not parameter_rule.min and "min" in default_parameter_rule:
                        parameter_rule.min = default_parameter_rule["min"]
                    if (
                        not parameter_rule.default
                        and "default" in default_parameter_rule
                    ):
                        parameter_rule.default = default_parameter_rule["default"]
                    if (
                        not parameter_rule.precision
                        and "precision" in default_parameter_rule
                    ):
                        parameter_rule.precision = default_parameter_rule["precision"]
                except ValueError:
                    # 如果找不到对应的默认参数配置，跳过
                    pass

            new_parameter_rules.append(parameter_rule)

        schema.parameter_rules = new_parameter_rules
        return schema

    async def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> AIModelEntity | None:
        """
        获取可自定义的模型结构配置
        此方法需要在子类中实现

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型结构配置
        """
        return None

    def _get_default_parameter_rule_variable_map(
        self, name: DefaultParameterName
    ) -> dict:
        """
        根据默认参数名称获取参数规则变量映射

        :param name: 默认参数名称
        :return: 参数规则变量映射
        """
        return PARAMETER_RULE_TEMPLATE[name]
