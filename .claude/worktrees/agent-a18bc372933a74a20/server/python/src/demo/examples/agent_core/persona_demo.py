"""
智能体人设配置示例

演示如何配置智能体的：
- 角色（Role）
- 语气（Tone）
- 系统提示词（System Prompt）

示例使用：
    persona = PersonaConfig(
        role="Python 专家",
        tone="专业、简洁",
        system_prompt="你是 Python 编程专家..."
    )
"""

from string import Template
from typing import Any


class PersonaConfig:
    """智能体人设配置

    定义智能体的角色、语气和系统提示词。

    Attributes:
        role: 角色名称
        tone: 语气风格
        system_prompt: 系统提示词模板
    """

    # 预定义角色模板
    ROLE_TEMPLATES: dict[str, dict[str, str]] = {
        "python_expert": {
            "role": "Python 编程专家",
            "tone": "专业、简洁、准确",
            "template": """你是一名专业的 Python 编程专家。

角色：$role
语气：$tone

回答规则：
1. 回答需基于知识库内容，若无相关知识则说明
2. 代码示例使用标准 Python 语法
3. 输出格式为"答案：[内容]"
4. 涉及天气查询则调用 Weather 工具""",
        },
        "code_reviewer": {
            "role": "代码审查专家",
            "tone": "严谨、建设性",
            "template": """你是一名经验丰富的代码审查专家。

角色：$role
语气：$tone

审查规则：
1. 关注代码质量、性能、安全性
2. 提供具体改进建议
3. 使用友好但专业的语言""",
        },
        "qa_assistant": {
            "role": "智能问答助手",
            "tone": "友好、耐心",
            "template": """你是一个智能问答助手。

角色：$role
语气：$tone

回答规则：
1. 尽可能提供准确、有帮助的回答
2. 如果不确定，诚实说明
3. 必要时提供相关资源链接""",
        },
    }

    def __init__(
        self,
        role: str = "智能助手",
        tone: str = "友好、专业",
        system_prompt: str | None = None,
        template_name: str | None = None,
    ) -> None:
        """初始化人设配置

        Args:
            role: 角色名称
            tone: 语气风格
            system_prompt: 自定义系统提示词
            template_name: 预定义模板名称
        """
        if template_name and template_name in self.ROLE_TEMPLATES:
            template_data = self.ROLE_TEMPLATES[template_name]
            self.role = template_data["role"]
            self.tone = template_data["tone"]
            self._template = template_data["template"]
        else:
            self.role = role
            self.tone = tone
            self._template = system_prompt or self._default_template()

    def _default_template(self) -> str:
        """返回默认模板"""
        return """你是一个智能助手。

角色：$role
语气：$tone

请根据用户问题提供有帮助的回答。"""

    @property
    def system_prompt(self) -> str:
        """生成系统提示词"""
        template = Template(self._template)
        return template.substitute(role=self.role, tone=self.tone)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "tone": self.tone,
            "system_prompt": self.system_prompt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaConfig":
        """从字典创建"""
        return cls(
            role=data.get("role", "智能助手"),
            tone=data.get("tone", "友好、专业"),
            system_prompt=data.get("system_prompt"),
        )


class AgentPersona:
    """智能体人设管理器

    管理智能体的完整人设配置，包括：
    - 角色定义
    - 语气风格
    - 行为约束
    - 输出格式
    """

    def __init__(self, config: PersonaConfig) -> None:
        """初始化人设管理器

        Args:
            config: 人设配置
        """
        self.config = config
        self._constraints: list[str] = []
        self._output_format: str | None = None

    def add_constraint(self, constraint: str) -> None:
        """添加行为约束

        Args:
            constraint: 约束描述
        """
        self._constraints.append(constraint)

    def set_output_format(self, format_template: str) -> None:
        """设置输出格式

        Args:
            format_template: 输出格式模板
        """
        self._output_format = format_template

    def get_full_prompt(self) -> str:
        """获取完整提示词

        Returns:
            包含所有配置的完整提示词
        """
        prompt = self.config.system_prompt

        if self._constraints:
            constraints_text = "\n".join(f"- {c}" for c in self._constraints)
            prompt += f"\n\n行为约束：\n{constraints_text}"

        if self._output_format:
            prompt += f"\n\n输出格式：\n{self._output_format}"

        return prompt

    def format_response(self, content: str) -> str:
        """格式化响应内容

        Args:
            content: 原始内容

        Returns:
            格式化后的响应
        """
        if self._output_format:
            return self._output_format.format(content=content)
        return f"答案：{content}"


class PersonaDemo:
    """人设配置演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.personas: dict[str, PersonaConfig] = {}

    def create_persona(
        self,
        name: str,
        template_name: str | None = None,
        **kwargs: Any,
    ) -> PersonaConfig:
        """创建人设配置

        Args:
            name: 人设名称
            template_name: 预定义模板名称
            **kwargs: 其他配置参数

        Returns:
            人设配置实例
        """
        config = PersonaConfig(template_name=template_name, **kwargs)
        self.personas[name] = config
        return config

    def get_persona(self, name: str) -> PersonaConfig | None:
        """获取人设配置

        Args:
            name: 人设名称

        Returns:
            人设配置实例
        """
        return self.personas.get(name)

    def list_personas(self) -> list[str]:
        """列出所有人设名称"""
        return list(self.personas.keys())


def demo() -> None:
    """演示人设配置功能"""
    print("=" * 50)
    print("智能体人设配置示例")
    print("=" * 50)

    # 使用预定义模板
    print("\n1. 使用预定义模板")
    persona = PersonaConfig(template_name="python_expert")
    print(f"角色: {persona.role}")
    print(f"语气: {persona.tone}")
    print(f"\n系统提示词:\n{persona.system_prompt}")

    # 自定义配置
    print("\n" + "-" * 50)
    print("\n2. 自定义配置")
    custom_persona = PersonaConfig(
        role="技术文档撰写专家",
        tone="清晰、结构化",
        system_prompt="你是技术文档撰写专家，擅长编写清晰易懂的技术文档。",
    )
    print(f"角色: {custom_persona.role}")
    print(f"语气: {custom_persona.tone}")

    # 使用 AgentPersona 管理器
    print("\n" + "-" * 50)
    print("\n3. 使用 AgentPersona 管理器")
    agent = AgentPersona(persona)
    agent.add_constraint("代码示例必须可运行")
    agent.add_constraint("避免使用专业术语过多")
    agent.set_output_format("【回答】\n{content}")

    print("完整提示词:")
    print(agent.get_full_prompt())


if __name__ == "__main__":
    demo()
