"""JavaScript 代码提供者"""

from textwrap import dedent

from ai.components.code_executor.code_executor import CodeLanguage
from ai.components.code_executor.code_node_provider import CodeNodeProvider


class JavascriptCodeProvider(CodeNodeProvider):
    """JavaScript 代码提供者"""

    @staticmethod
    def get_language() -> str:
        """获取语言类型"""
        return CodeLanguage.JAVASCRIPT

    @classmethod
    def get_default_code(cls) -> str:
        """获取默认代码模板"""
        return dedent(
            """
            function main({arg1, arg2}) {
                return {
                    result: arg1 + arg2
                }
            }
            """,
        )
