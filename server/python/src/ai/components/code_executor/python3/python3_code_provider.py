"""Python3 代码提供者"""

from textwrap import dedent

from ai.components.code_executor.code_executor import CodeLanguage
from ai.components.code_executor.code_node_provider import CodeNodeProvider


class Python3CodeProvider(CodeNodeProvider):
    """Python3 代码提供者"""

    @staticmethod
    def get_language() -> str:
        """获取语言类型"""
        return CodeLanguage.PYTHON3

    @classmethod
    def get_default_code(cls) -> str:
        """获取默认代码模板"""
        return dedent(
            """
            def main(arg1: str, arg2: str) -> dict:
                return {
                    "result": arg1 + arg2,
                }
            """,
        )
