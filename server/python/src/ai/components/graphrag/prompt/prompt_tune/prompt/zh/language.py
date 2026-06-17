"""提供组件图谱检索增强生成相关功能。"""

DETECT_LANGUAGE_PROMPT = """。
您是一位帮助人类分析文本文档中信息的智能助手。
给定一段示例文本,通过确定所提供文本的主要语言来帮助用户。
示例包括: "Chinese", "English", "Spanish", "Japanese", "Portuguese" 等等。

文本:
{input_text}

语言:

"""
