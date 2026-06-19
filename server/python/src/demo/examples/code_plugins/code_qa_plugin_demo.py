"""
代码问答插件示例

演示代码插件开发：
- 基于关键词的代码示例查询
- 预设代码模板
- 可扩展的问答规则

示例使用：
    plugin = CodeQAPlugin()
    result = plugin.query("Python 函数示例")
"""



class CodeQAPlugin:
    """代码问答插件基类

    提供基于关键词的代码示例查询功能。
    """

    def __init__(self) -> None:
        """初始化插件"""
        self._rules: dict[str, str] = {}

    def add_rule(self, keyword: str, answer: str) -> None:
        """添加问答规则

        Args:
            keyword: 关键词
            answer: 回答内容
        """
        self._rules[keyword.lower()] = answer

    def query(self, question: str) -> str:
        """查询问题

        Args:
            question: 用户问题

        Returns:
            回答内容
        """
        question_lower = question.lower()

        for keyword, answer in self._rules.items():
            if keyword in question_lower:
                return answer

        return "未找到相关代码"

    def list_keywords(self) -> list[str]:
        """列出所有关键词"""
        return list(self._rules.keys())


class PythonCodeQA(CodeQAPlugin):
    """Python 代码问答插件

    预设 Python 相关的问答规则。
    """

    def __init__(self) -> None:
        """初始化 Python 代码问答插件"""
        super().__init__()

        # 预设 Python 问答规则
        self.add_rule(
            "函数",
            """def example_function(param1, param2):
    \"\"\"函数示例

    Args:
        param1: 参数1
        param2: 参数2

    Returns:
        返回值
    \"\"\"
    return param1 + param2""",
        )

        self.add_rule(
            "类",
            """class ExampleClass:
    \"\"\"类示例\"\"\"

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

    @property
    def info(self) -> dict:
        return {"name": self.name}""",
        )

        self.add_rule(
            "列表",
            """# 列表操作示例
my_list = [1, 2, 3, 4, 5]

# 添加元素
my_list.append(6)

# 列表推导式
squares = [x**2 for x in my_list]

# 过滤
even_numbers = [x for x in my_list if x % 2 == 0]""",
        )

        self.add_rule(
            "字典",
            """# 字典操作示例
my_dict = {"name": "Python", "version": 3.12}

# 访问元素
name = my_dict["name"]
version = my_dict.get("version", "未知")

# 遍历
for key, value in my_dict.items():
    print(f"{key}: {value}")

# 字典推导式
squared = {k: v**2 for k, v in my_dict.items() if isinstance(v, int)}""",
        )

        self.add_rule(
            "异常",
            """# 异常处理示例
try:
    result = risky_operation()
except ValueError as e:
    print(f"值错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
else:
    print(f"成功: {result}")
finally:
    cleanup()""",
        )

        self.add_rule(
            "装饰器",
            """# 装饰器示例
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("调用前")
        result = func(*args, **kwargs)
        print("调用后")
        return result
    return wrapper

@my_decorator
def my_function():
    print("函数执行")""",
        )


class CodeQADemo:
    """代码问答演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.plugin = PythonCodeQA()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("代码问答插件示例")
        print("=" * 50)

        # 显示可用关键词
        print(f"\n可用关键词: {self.plugin.list_keywords()}")

        # 查询演示
        questions = [
            "Python 函数示例",
            "如何定义类？",
            "列表操作",
            "字典用法",
            "异常处理",
            "装饰器怎么写？",
            "未知主题",
        ]

        for question in questions:
            print(f"\n问题: {question}")
            print("-" * 30)
            answer = self.plugin.query(question)
            if answer == "未找到相关代码":
                print(f"回答: {answer}")
            else:
                print("代码示例:")
                print(answer)


def demo() -> None:
    """演示代码问答功能"""
    demo_instance = CodeQADemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
