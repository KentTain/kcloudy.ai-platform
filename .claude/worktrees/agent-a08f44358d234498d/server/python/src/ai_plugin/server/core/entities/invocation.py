from enum import Enum


class InvokeType(Enum):
    """
    调用类型枚举

    定义插件系统中所有支持的调用类型
    """

    Tool = "tool"  # 工具调用
    LLM = "llm"  # 大语言模型调用
    TextEmbedding = "text_embedding"  # 文本嵌入调用
    Rerank = "rerank"  # 重排序调用
    TTS = "tts"  # 文本转语音调用
    Speech2Text = "speech2text"  # 语音转文本调用
    Moderation = "moderation"  # 内容审核调用
    NodeParameterExtractor = "node_parameter_extractor"  # 节点参数提取器
    NodeQuestionClassifier = "node_question_classifier"  # 节点问题分类器
    App = "app"  # 应用调用
    Storage = "storage"  # 存储调用
    UploadFile = "upload_file"  # 文件上传调用
    SYSTEM_SUMMARY = "system_summary"  # 系统摘要调用
    FetchApp = "fetch_app"  # 获取应用调用

    @classmethod
    def value_of(cls, value: str) -> "InvokeType":
        """
        根据给定值获取对应的调用类型

        Args:
            value: 调用类型字符串值

        Returns:
            InvokeType: 对应的调用类型枚举

        Raises:
            ValueError: 当传入无效的类型值时抛出
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"无效的类型值 {value}")
