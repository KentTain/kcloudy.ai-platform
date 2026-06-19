import decimal
import socket
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import final

import gevent.socket
from pydantic import ConfigDict

from ai_plugin.sdk.entities import I18nObject
from ai_plugin.sdk.entities.model import (
    PARAMETER_RULE_TEMPLATE,
    AIModelEntity,
    DefaultParameterName,
    ModelType,
    PriceConfig,
    PriceInfo,
    PriceType,
)
from ai_plugin.sdk.errors.model import InvokeAuthorizationError, InvokeError

if socket.socket is gevent.socket.socket:
    import gevent.threadpool

    threadpool = gevent.threadpool.ThreadPool(1)


class AIModel(ABC):
    """
    所有模型的基类

    定义了模型的基本接口和通用功能
    """

    model_type: ModelType
    model_schemas: list[AIModelEntity]
    started_at: float = 0

    # pydantic配置
    model_config = ConfigDict(protected_namespaces=())

    @final
    def __init__(self, model_schemas: list[AIModelEntity]) -> None:
        """
        初始化模型

        注意：此方法已标记为final，请不要重写

        :param model_schemas: 模型架构列表
        """
        self.model_schemas = [
            model_schema
            for model_schema in model_schemas
            if model_schema.model_type == self.model_type
        ]

    @abstractmethod
    def validate_credentials(self, model: str, credentials: Mapping) -> None:
        """
        验证模型凭证

        :param model: 模型名称
        :param credentials: 模型凭证
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        将模型调用错误映射到统一错误
        键是抛出给调用者的错误类型
        值是模型抛出的错误类型，需要转换为统一的错误类型给调用者

        :return: 调用错误映射
        """
        raise NotImplementedError

    def _transform_invoke_error(self, error: Exception) -> InvokeError:
        """
        将调用错误转换为统一错误

        :param error: 模型调用错误
        :return: 统一错误
        """
        provider_name = self.__class__.__module__.split(".")[-3]

        for invoke_error, model_errors in self._invoke_error_mapping.items():
            if isinstance(error, tuple(model_errors)):
                if invoke_error == InvokeAuthorizationError:
                    return invoke_error(
                        description=f"[{provider_name}] Incorrect model credentials provided, "
                        "please check and try again. ",
                    )

                return invoke_error(
                    description=f"[{provider_name}] {invoke_error.description}, {error!s}"
                )

        return InvokeError(description=f"[{provider_name}] Error: {error!s}")

    def get_price(
        self, model: str, credentials: dict, price_type: PriceType, tokens: int
    ) -> PriceInfo:
        """
        获取指定模型和token数的价格

        :param model: 模型名称
        :param credentials: 模型凭证
        :param price_type: 价格类型
        :param tokens: token数量
        :return: 价格信息
        """
        # 获取模型架构
        model_schema = self.get_model_schema(model, credentials)

        # 从预定义模型架构获取价格信息
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

        if unit_price is None:
            return PriceInfo(
                unit_price=decimal.Decimal("0.0"),
                unit=decimal.Decimal("0.0"),
                total_amount=decimal.Decimal("0.0"),
                currency="USD",
            )

        # 计算总金额
        if not price_config:
            raise ValueError(f"Price config not found for model {model}")
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

    def predefined_models(self) -> list[AIModelEntity]:
        """
        获取指定提供者的所有预定义模型

        :return: 预定义模型列表
        """
        return self.model_schemas

    def get_model_schema(
        self, model: str, credentials: Mapping | None = None
    ) -> AIModelEntity | None:
        """
        根据模型名称和凭证获取模型架构

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型架构
        """
        # 获取预定义模型 (predefined_models)
        models = self.predefined_models()

        model_map = {model.model: model for model in models}
        if model in model_map:
            return model_map[model]

        if credentials:
            model_schema = self.get_customizable_model_schema_from_credentials(
                model, credentials
            )
            if model_schema:
                return model_schema

        return None

    def get_customizable_model_schema_from_credentials(
        self, model: str, credentials: Mapping
    ) -> AIModelEntity | None:
        """
        从凭证获取可自定义的模型架构

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型架构
        """
        return self._get_customizable_model_schema(model, credentials)

    def _get_customizable_model_schema(
        self, model: str, credentials: Mapping
    ) -> AIModelEntity | None:
        """
        获取可自定义的模型架构并填充模板

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 填充后的模型架构
        """
        schema = self.get_customizable_model_schema(model, credentials)

        if not schema:
            return None

        # 填充模板
        new_parameter_rules = []
        for parameter_rule in schema.parameter_rules:
            if parameter_rule.use_template:
                try:
                    default_parameter_name = DefaultParameterName.value_of(
                        parameter_rule.use_template
                    )
                    default_parameter_rule = (
                        self._get_default_parameter_rule_variable_map(
                            default_parameter_name
                        )
                    )
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
                    if (
                        not parameter_rule.required
                        and "required" in default_parameter_rule
                    ):
                        parameter_rule.required = default_parameter_rule["required"]
                    if not parameter_rule.help and "help" in default_parameter_rule:
                        parameter_rule.help = I18nObject(
                            en_US=default_parameter_rule["help"]["en_US"],
                        )
                    if (
                        parameter_rule.help
                        and not parameter_rule.help.en_US
                        and (
                            "help" in default_parameter_rule
                            and "en_US" in default_parameter_rule["help"]
                        )
                    ):
                        parameter_rule.help.en_US = default_parameter_rule["help"][
                            "en_US"
                        ]
                    if (
                        parameter_rule.help
                        and not parameter_rule.help.zh_Hans
                        and (
                            "help" in default_parameter_rule
                            and "zh_Hans" in default_parameter_rule["help"]
                        )
                    ):
                        parameter_rule.help.zh_Hans = default_parameter_rule[
                            "help"
                        ].get(
                            "zh_Hans",
                            default_parameter_rule["help"]["en_US"],
                        )
                except ValueError:
                    pass

            new_parameter_rules.append(parameter_rule)

        schema.parameter_rules = new_parameter_rules

        return schema

    def get_customizable_model_schema(
        self, model: str, credentials: Mapping
    ) -> AIModelEntity | None:
        """
        获取可自定义的模型架构

        :param model: 模型名称
        :param credentials: 模型凭证
        :return: 模型架构
        """
        return None

    def _get_default_parameter_rule_variable_map(
        self, name: DefaultParameterName
    ) -> dict:
        """
        获取指定名称的默认参数规则

        :param name: 参数名称
        :return: 参数规则
        """
        default_parameter_rule = PARAMETER_RULE_TEMPLATE.get(name)

        if not default_parameter_rule:
            raise Exception(f"Invalid model parameter rule name {name}")

        return default_parameter_rule

    def _get_num_tokens_by_gpt2(self, text: str) -> int:
        """
        使用GPT2计算给定提示消息的token数量
        某些提供者模型不提供获取token数量的接口。
        这里使用gpt2分词器来计算token数量。
        此方法可以离线执行，gpt2分词器已缓存在项目中。

        :param text: 提示的纯文本。您需要将原始消息转换为纯文本
        :return: token数量
        """

        # 优化：
        # 为了避免性能问题，不计算过长文本的token数量
        # 仅保证文本长度小于100000
        if len(text) >= 100000:
            return len(text)

        # 检查gevent是否已打补丁到主线程
        import socket

        import tiktoken

        if socket.socket is gevent.socket.socket:
            # 使用gevent真实线程避免阻塞主线程
            result = threadpool.spawn(
                lambda: len(tiktoken.encoding_for_model("gpt2").encode(text))
            )
            return result.get(block=True) or 0

        return len(tiktoken.encoding_for_model("gpt2").encode(text))
