"""
Output Parser 输出解析器示例

演示如何使用 LangChain 的输出解析器将 LLM 输出解析为结构化数据。
包括 PydanticOutputParser 和 JsonOutputParser。

Day 3 讲义：AI 智能体应用实战 - 提示词工程
"""

import json
from typing import Annotated

from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# ==================== Pydantic 模型定义 ====================


class PersonInfo(BaseModel):
    """人物信息模型"""

    name: Annotated[str, Field(description="人物姓名")]
    age: Annotated[int, Field(description="人物年龄")]
    occupation: Annotated[str, Field(description="职业")]
    hobbies: Annotated[list[str], Field(description="兴趣爱好列表")]


class ProductReview(BaseModel):
    """产品评论模型"""

    product_name: Annotated[str, Field(description="产品名称")]
    rating: Annotated[int, Field(ge=1, le=5, description="评分，1-5分")]
    pros: Annotated[list[str], Field(description="优点列表")]
    cons: Annotated[list[str], Field(description="缺点列表")]
    summary: Annotated[str, Field(description="一句话总结")]


# ==================== 解析器演示类 ====================


class PydanticParserDemo:
    """Pydantic 输出解析器演示"""

    def __init__(self, model_class: type[BaseModel]) -> None:
        """
        初始化 Pydantic 解析器

        Args:
            model_class: Pydantic 模型类
        """
        self.parser = PydanticOutputParser(pydantic_object=model_class)
        self.model_class = model_class

    def get_format_instructions(self) -> str:
        """
        获取格式化指令

        这些指令会告诉 LLM 如何格式化输出，
        以便解析器能够正确解析。

        Returns:
            格式化指令字符串
        """
        return self.parser.get_format_instructions()

    def create_prompt(
        self, template: str, input_variables: list[str]
    ) -> PromptTemplate:
        """
        创建带有格式化指令的提示词模板

        Args:
            template: 模板字符串
            input_variables: 输入变量列表

        Returns:
            PromptTemplate 实例
        """
        return PromptTemplate(
            template=template + "\n\n{format_instructions}",
            input_variables=input_variables,
            partial_variables={"format_instructions": self.get_format_instructions()},
        )

    def parse(self, text: str) -> BaseModel:
        """
        解析 LLM 输出

        Args:
            text: LLM 返回的文本

        Returns:
            解析后的 Pydantic 模型实例
        """
        return self.parser.parse(text)

    def demo_person_info(self) -> None:
        """演示人物信息解析"""
        print("=== PydanticOutputParser - 人物信息示例 ===\n")

        # 创建解析器
        demo = PydanticParserDemo(PersonInfo)

        # 获取格式化指令
        print("格式化指令：")
        print(demo.get_format_instructions())
        print()

        # 创建提示词
        prompt = demo.create_prompt(
            template="请从以下文本中提取人物信息：\n{text}",
            input_variables=["text"],
        )

        sample_text = "张三今年28岁，是一名软件工程师，平时喜欢打篮球、看电影和旅游。"
        formatted_prompt = prompt.format(text=sample_text)
        print("格式化后的提示词：")
        print(formatted_prompt)
        print()

        # 模拟 LLM 输出
        mock_llm_output = """
```json
{
  "name": "张三",
  "age": 28,
  "occupation": "软件工程师",
  "hobbies": ["打篮球", "看电影", "旅游"]
}
```
"""
        result = demo.parse(mock_llm_output)
        print(f"解析结果：{result}")
        print(f"类型：{type(result)}")
        print()


class JsonParserDemo:
    """JSON 输出解析器演示"""

    def __init__(self) -> None:
        """初始化 JSON 解析器"""
        self.parser = JsonOutputParser()

    def get_format_instructions(self) -> str:
        """
        获取格式化指令

        Returns:
            格式化指令字符串
        """
        return self.parser.get_format_instructions()

    def parse(self, text: str) -> dict:
        """
        解析 JSON 输出

        Args:
            text: LLM 返回的文本

        Returns:
            解析后的字典
        """
        return self.parser.parse(text)

    def demo_product_review(self) -> None:
        """演示产品评论解析"""
        print("=== JsonOutputParser - 产品评论示例 ===\n")

        demo = JsonParserDemo()

        # 创建提示词模板
        prompt = PromptTemplate(
            template="""
请分析以下产品评论，提取关键信息：

评论内容：{review}

{format_instructions}
""",
            input_variables=["review"],
            partial_variables={"format_instructions": demo.get_format_instructions()},
        )

        sample_review = """
这款蓝牙耳机用了两周，总体来说还不错。
优点：音质清晰，连接稳定，续航能达到8小时左右。
缺点：佩戴时间长了耳朵有点疼，降噪效果一般。
综合来看性价比还可以，给4分。
"""

        formatted_prompt = prompt.format(review=sample_review)
        print("格式化后的提示词：")
        print(formatted_prompt)
        print()

        # 模拟 LLM 输出
        mock_llm_output = """
{
  "product_name": "蓝牙耳机",
  "rating": 4,
  "pros": ["音质清晰", "连接稳定", "续航约8小时"],
  "cons": ["佩戴舒适度欠佳", "降噪效果一般"],
  "summary": "性价比尚可的蓝牙耳机，音质和续航不错，但舒适度和降噪有改进空间"
}
"""
        result = demo.parse(mock_llm_output)
        print("解析结果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()


def demo_list_parser() -> None:
    """演示列表解析"""
    print("=== 列表输出解析示例 ===\n")

    # 使用 JsonOutputParser 解析列表
    parser = JsonOutputParser()

    # 模拟 LLM 返回的列表输出
    mock_output = """
[
  {"name": "Python", "type": "编程语言", "difficulty": "中等"},
  {"name": "JavaScript", "type": "编程语言", "difficulty": "中等"},
  {"name": "Go", "type": "编程语言", "difficulty": "简单"}
]
"""

    result = parser.parse(mock_output)
    print("解析的列表：")
    for item in result:
        print(f"  - {item}")
    print()


if __name__ == "__main__":
    # Pydantic 解析器演示
    pydantic_demo = PydanticParserDemo(PersonInfo)
    pydantic_demo.demo_person_info()

    # JSON 解析器演示
    json_demo = JsonParserDemo()
    json_demo.demo_product_review()

    # 列表解析演示
    demo_list_parser()
