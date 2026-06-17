"""代码节点提供者基类"""

from abc import abstractmethod

from pydantic import BaseModel


class CodeNodeProvider(BaseModel):
    """代码节点提供者基类"""

    @staticmethod
    @abstractmethod
    def get_language() -> str:
        """获取语言类型"""
        pass

    @classmethod
    def is_accept_language(cls, language: str) -> bool:
        """检查是否接受指定语言"""
        return language == cls.get_language()

    @classmethod
    @abstractmethod
    def get_default_code(cls) -> str:
        """获取默认代码模板"""
        pass

    @classmethod
    def get_default_config(cls) -> dict:
        """获取默认配置"""
        return {
            "type": "code",
            "config": {
                "variables": [
                    {"variable": "arg1", "value_selector": []},
                    {"variable": "arg2", "value_selector": []},
                ],
                "code_language": cls.get_language(),
                "code": cls.get_default_code(),
                "outputs": {"result": {"type": "string", "children": None}},
            },
        }
