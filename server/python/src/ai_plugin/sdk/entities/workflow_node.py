from enum import Enum

from pydantic import BaseModel, Field

from ai_plugin.sdk.entities.model.llm import LLMMode


class NodeResponse(BaseModel):
    """
    节点响应模型类

    定义工作流节点执行后的响应数据结构
    """

    process_data: dict  # 处理数据
    inputs: dict  # 输入数据
    outputs: dict  # 输出数据


class NodeType(str, Enum):
    """
    节点类型枚举类

    定义工作流中支持的各种节点类型
    """

    START = "start"  # 开始节点
    END = "end"  # 结束节点
    ANSWER = "answer"  # 答案节点
    LLM = "llm"  # 大语言模型节点
    KNOWLEDGE_RETRIEVAL = "knowledge-retrieval"  # 知识检索节点
    IF_ELSE = "if-else"  # 条件判断节点
    CODE = "code"  # 代码执行节点
    TEMPLATE_TRANSFORM = "template-transform"  # 模板转换节点
    QUESTION_CLASSIFIER = "question-classifier"  # 问题分类节点
    HTTP_REQUEST = "http-request"  # HTTP请求节点
    TOOL = "tool"  # 工具节点
    VARIABLE_AGGREGATOR = "variable-aggregator"  # 变量聚合节点
    LOOP = "loop"  # 循环节点
    ITERATION = "iteration"  # 迭代节点
    PARAMETER_EXTRACTOR = "parameter-extractor"  # 参数提取节点
    CONVERSATION_VARIABLE_ASSIGNER = "assigner"  # 会话变量分配节点

    @classmethod
    def value_of(cls, value: str) -> "NodeType":
        """
        根据给定值获取对应的节点类型

        Args:
            value: 节点类型值

        Returns:
            NodeType: 节点类型枚举

        Raises:
            ValueError: 当节点类型值无效时抛出
        """
        for node_type in cls:
            if node_type.value == value:
                return node_type
        raise ValueError(f"无效的节点类型值 {value}")


class ModelConfig(BaseModel):
    """
    模型配置类

    定义工作流节点中使用的模型配置信息
    """

    provider: str  # 模型提供者
    name: str  # 模型名称
    mode: LLMMode = LLMMode.CHAT  # 模型模式，默认为聊天模式
    completion_params: dict | None = None  # 补全参数（可选）


class ParameterConfig(BaseModel):
    """
    参数配置类

    定义节点参数的配置信息
    """

    name: str  # 参数名称
    type: str  # 参数类型
    options: list[str] = Field(default_factory=list)  # 参数选项列表
    description: str | None  # 参数描述（可选）
    required: bool | None  # 是否必填（可选）


class ClassConfig(BaseModel):
    """
    类配置类

    定义节点类的配置信息
    """

    id: str  # 类ID
    name: str  # 类名
