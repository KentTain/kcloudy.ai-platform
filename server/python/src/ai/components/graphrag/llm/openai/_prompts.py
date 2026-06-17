"""底层 LLM 调用的实用提示词模块。

本模块提供用于 LLM 底层调用的工具性提示词,主要用于 JSON 格式修复。
"""

# JSON 检查和修复提示词
JSON_CHECK_PROMPT = """。
你将收到一个在执行 json.loads 时抛出错误的格式错误的 JSON 字符串。
它可能包含不必要的转义序列,或者在某处缺少逗号或冒号。
你的任务是修复这个字符串并返回一个格式良好的 JSON 字符串,包含单个对象。
消除任何不必要的转义序列。
只返回有效的 JSON,可以使用 json.loads 解析,不要添加任何注释。

# 示例
-----------
文本: {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}
输出: {{"title": "abc", "summary": "def"}}
-----------
文本: {{"title": "abc", "summary": "def"
输出: {{"title": "abc", "summary": "def"}}
-----------
文本: {{"title': "abc", 'summary": "def"
输出: {{"title": "abc", "summary": "def"}}
-----------
文本: "{{"title": "abc", "summary": "def"}}"
输出: {{"title": "abc", "summary": "def"}}
-----------
文本: [{{"title": "abc", "summary": "def"}}]
输出: [{{"title": "abc", "summary": "def"}}]
-----------
文本: [{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]
输出: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]
-----------
文本: ```json\n[{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]```
输出: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]


# 实际数据
文本: {input_text}
输出:"""
