from ai_plugin.sdk.entities.workflow_node import (
    ClassConfig,
    ModelConfig,
    NodeResponse,
)
from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class QuestionClassifierNodeInvocation(BackwardsInvocation[NodeResponse]):
    """问题分类节点调用类

    用于调用工作流中的问题分类节点，根据预定义的分类对用户问题进行分类。
    """

    def invoke(
        self,
        classes: list[ClassConfig],
        model: ModelConfig,
        query: str,
        instruction: str = "",
    ) -> NodeResponse:
        """调用问题分类节点

        Args:
            classes: 分类配置列表，定义可用的分类选项
            model: 模型配置对象，指定使用的分类模型
            query: 用户查询内容
            instruction: 分类指令，可选的额外指导信息

        Returns:
            节点响应对象，包含分类结果

        Raises:
            Exception: 当问题分类节点没有响应时抛出异常
        """
        # 调用后端问题分类服务
        response = self._backwards_invoke(
            InvokeType.NodeQuestionClassifier,
            NodeResponse,
            {
                "classes": classes,
                "model": model,
                "query": query,
                "instruction": instruction,
            },
        )

        # 返回第一个响应数据
        for data in response:
            return data

        raise Exception("工作流节点问题分类器没有响应")
