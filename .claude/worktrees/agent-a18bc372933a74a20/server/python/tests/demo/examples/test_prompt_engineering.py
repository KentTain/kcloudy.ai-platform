"""
提示词工程示例单元测试

测试 prompt_engineering 模块的所有示例代码。
"""

import pytest

from demo.examples.prompt_engineering import (
    create_example_selector,
    create_few_shot_prompt,
    create_partial_template,
    create_prompt_template,
)
from demo.examples.prompt_engineering.output_parser_demo import (
    JsonParserDemo,
    PersonInfo,
    PydanticParserDemo,
)


class TestPromptTemplate:
    """测试 PromptTemplate 功能"""

    def test_create_basic_template(self) -> None:
        """测试创建基础模板"""
        template = create_prompt_template(
            template="你好，{name}！你是{role}。",
            input_variables=["name", "role"],
        )

        result = template.format(name="小明", role="开发者")
        assert result == "你好，小明！你是开发者。"

    def test_create_template_missing_variable(self) -> None:
        """测试缺少变量时抛出异常"""
        template = create_prompt_template(
            template="你好，{name}！你是{role}。",
            input_variables=["name", "role"],
        )

        with pytest.raises(KeyError):
            template.format(name="小明")  # 缺少 role

    def test_create_partial_template(self) -> None:
        """测试部分变量绑定"""
        template = create_partial_template(
            template="你好，{name}！今天是{day}。",
            input_variables=["name", "day"],
            partial_variables={"day": "星期一"},
        )

        result = template.format(name="小明")
        assert result == "你好，小明！今天是星期一。"

    def test_partial_template_override(self) -> None:
        """测试部分变量可以被覆盖"""
        template = create_partial_template(
            template="你好，{name}！今天是{day}。",
            input_variables=["name", "day"],
            partial_variables={"day": "星期一"},
        )

        # 可以覆盖部分变量
        result = template.format(name="小明", day="星期二")
        assert result == "你好，小明！今天是星期二。"


class TestFewShotPrompt:
    """测试 FewShotPromptTemplate 功能"""

    def test_create_few_shot_prompt(self) -> None:
        """测试创建少样本提示词"""
        from langchain_core.prompts import PromptTemplate

        examples = [
            {"input": "快乐", "output": "悲伤"},
            {"input": "高大", "output": "矮小"},
        ]

        example_prompt = PromptTemplate(
            template="输入: {input}\n输出: {output}",
            input_variables=["input", "output"],
        )

        few_shot = create_few_shot_prompt(
            examples=examples,
            example_prompt=example_prompt,
            prefix="请写出反义词：\n",
            suffix="输入: {input}\n输出:",
            input_variables=["input"],
        )

        result = few_shot.format(input="明亮")
        assert "快乐" in result
        assert "悲伤" in result
        assert "明亮" in result
        assert "请写出反义词" in result

    def test_few_shot_prompt_multiple_examples(self) -> None:
        """测试多个示例的少样本提示词"""
        from langchain_core.prompts import PromptTemplate

        examples = [
            {"text": "好", "label": "正面"},
            {"text": "差", "label": "负面"},
            {"text": "一般", "label": "中性"},
        ]

        example_prompt = PromptTemplate(
            template="文本：{text}，标签：{label}",
            input_variables=["text", "label"],
        )

        few_shot = create_few_shot_prompt(
            examples=examples,
            example_prompt=example_prompt,
            suffix="文本：{text}，标签：",
            input_variables=["text"],
        )

        result = few_shot.format(text="不错")
        # 所有示例都应该出现在结果中
        assert "好" in result
        assert "差" in result
        assert "一般" in result


class TestOutputParser:
    """测试输出解析器功能"""

    def test_pydantic_parser_format_instructions(self) -> None:
        """测试 Pydantic 解析器的格式化指令"""
        demo = PydanticParserDemo(PersonInfo)

        instructions = demo.get_format_instructions()
        assert "JSON" in instructions
        assert "name" in instructions
        assert "age" in instructions
        assert "occupation" in instructions

    def test_pydantic_parser_parse_valid_json(self) -> None:
        """测试解析有效的 JSON 输出"""
        demo = PydanticParserDemo(PersonInfo)

        mock_output = """
{
  "name": "张三",
  "age": 28,
  "occupation": "工程师",
  "hobbies": ["篮球", "电影"]
}
"""
        result = demo.parse(mock_output)

        assert isinstance(result, PersonInfo)
        assert result.name == "张三"
        assert result.age == 28
        assert result.occupation == "工程师"
        assert "篮球" in result.hobbies

    def test_pydantic_parser_parse_with_markdown(self) -> None:
        """测试解析带有 markdown 代码块的输出"""
        demo = PydanticParserDemo(PersonInfo)

        mock_output = """
```json
{
  "name": "李四",
  "age": 30,
  "occupation": "设计师",
  "hobbies": ["绘画", "摄影"]
}
```
"""
        result = demo.parse(mock_output)

        assert isinstance(result, PersonInfo)
        assert result.name == "李四"

    def test_json_parser_format_instructions(self) -> None:
        """测试 JSON 解析器的格式化指令"""
        demo = JsonParserDemo()

        instructions = demo.get_format_instructions()
        assert "JSON" in instructions

    def test_json_parser_parse(self) -> None:
        """测试 JSON 解析器解析输出"""
        demo = JsonParserDemo()

        mock_output = """
{
  "product_name": "耳机",
  "rating": 4,
  "pros": ["音质好"],
  "cons": ["价格高"],
  "summary": "性价比一般"
}
"""
        result = demo.parse(mock_output)

        assert isinstance(result, dict)
        assert result["product_name"] == "耳机"
        assert result["rating"] == 4
        assert "音质好" in result["pros"]

    def test_json_parser_parse_list(self) -> None:
        """测试 JSON 解析器解析列表"""
        demo = JsonParserDemo()

        mock_output = """
[
  {"name": "Python", "level": 3},
  {"name": "JavaScript", "level": 2}
]
"""
        result = demo.parse(mock_output)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Python"


class TestPromptComposition:
    """测试提示词组合功能"""

    def test_template_from_string(self) -> None:
        """测试从字符串创建模板"""
        from langchain_core.prompts import PromptTemplate

        template = PromptTemplate.from_template("写一首关于{topic}的诗")
        result = template.format(topic="春天")
        assert result == "写一首关于春天的诗"

    def test_template_with_multiple_variables(self) -> None:
        """测试多变量模板"""
        template = create_prompt_template(
            template="{greeting}，{name}！欢迎来到{place}。",
            input_variables=["greeting", "name", "place"],
        )

        result = template.format(greeting="你好", name="张三", place="北京")
        assert result == "你好，张三！欢迎来到北京。"
