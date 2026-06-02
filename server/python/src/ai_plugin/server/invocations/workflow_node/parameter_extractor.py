from ai_plugin.sdk.entities.workflow_node import (
    ModelConfig,
    NodeResponse,
    ParameterConfig,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class ParameterExtractorNodeInvocation(BackwardsInvocation[NodeResponse]):
    """参数提取节点调用类

    用于调用工作流中的参数提取节点，从用户输入中提取结构化参数。
    """

    def invoke(
        self,
        parameters: list[ParameterConfig],
        model: ModelConfig,
        query: str,
        instruction: str = "",
    ) -> NodeResponse:
        """调用参数提取节点

        Args:
            parameters: 参数配置列表，定义需要提取的参数规格
            model: 模型配置对象，指定使用的提取模型
            query: 用户查询内容
            instruction: 提取指令，可选的额外指导信息

        Returns:
            节点响应对象，包含提取的参数结果

        Raises:
            Exception: 当参数提取节点没有响应时抛出异常
        """
        # 调用后端参数提取服务
        response = self._backwards_invoke(
            InvokeType.NodeParameterExtractor,
            NodeResponse,
            {
                "parameters": parameters,
                "model": model,
                "query": query,
                "instruction": instruction,
            },
        )

        # 返回第一个响应数据
        for data in response:
            return data

        raise Exception("工作流节点参数提取器没有响应")
