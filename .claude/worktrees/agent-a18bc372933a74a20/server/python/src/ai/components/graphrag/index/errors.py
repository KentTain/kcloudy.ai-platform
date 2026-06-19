"""GraphRAG索引错误类型."""


class NoWorkflowsDefinedError(ValueError):
    """未定义工作流的异常."""

    def __init__(self):
        """初始化实例。"""
        super().__init__("No workflows defined.")


class UndefinedWorkflowError(ValueError):
    """无效动词输入的异常."""

    def __init__(self):
        """初始化实例。"""
        super().__init__("Workflow name is undefined.")


class UnknownWorkflowError(ValueError):
    """无效动词输入的异常."""

    def __init__(self, name: str):
        """
        初始化实例。

        Args:
            name (str): name 参数。
        """
        super().__init__(f"Unknown workflow: {name}")
