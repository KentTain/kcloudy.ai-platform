"""
完整智能体示例

演示如何整合四大支柱（人设、知识库、插件、工作流）
构建完整的智能体。

示例使用：
    agent = SimpleAgent()
    response = agent.chat("Python 如何定义函数？")
"""

from typing import Any

from demo.examples.agent_core.knowledge_base_demo import AgentKnowledgeBase
from demo.examples.agent_core.persona_demo import AgentPersona, PersonaConfig
from demo.examples.agent_core.workflow_demo import AgentWorkflow


class SimpleAgent:
    """简单智能体

    整合四大支柱的完整智能体实现：
    - 人设：定义角色和语气
    - 知识库：提供检索增强
    - 插件：通过工作流调用
    - 工作流：协调各组件
    """

    def __init__(
        self,
        persona_config: PersonaConfig | None = None,
        knowledge_base: AgentKnowledgeBase | None = None,
    ) -> None:
        """初始化智能体

        Args:
            persona_config: 人设配置
            knowledge_base: 知识库实例
        """
        # 初始化人设
        config = persona_config or PersonaConfig(template_name="python_expert")
        self.persona = AgentPersona(config)
        self.persona.add_constraint("回答必须基于知识库或工具结果")
        self.persona.set_output_format("【{content}】")

        # 初始化知识库
        self.kb = knowledge_base or AgentKnowledgeBase()

        # 初始化工作流
        self.workflow = AgentWorkflow()

        # 对话历史
        self._history: list[dict[str, str]] = []

    def add_knowledge(self, documents: list[str]) -> None:
        """添加知识到知识库

        Args:
            documents: 文档列表
        """
        self.kb.add_documents(documents)

    def chat(self, query: str) -> dict[str, Any]:
        """与智能体对话

        Args:
            query: 用户问题

        Returns:
            响应结果
        """
        # 记录用户消息
        self._history.append({"role": "user", "content": query})

        # 运行工作流
        result = self.workflow.run(query)

        # 格式化响应
        response = self.persona.format_response(result["response"])

        # 记录助手响应
        self._history.append({"role": "assistant", "content": response})

        return {
            "query": query,
            "response": response,
            "intent": result["intent"],
            "context": result.get("context", ""),
            "tool_result": result.get("tool_result", ""),
        }

    def get_history(self) -> list[dict[str, str]]:
        """获取对话历史"""
        return self._history.copy()

    def clear_history(self) -> None:
        """清空对话历史"""
        self._history.clear()

    def get_system_prompt(self) -> str:
        """获取完整系统提示词"""
        return self.persona.get_full_prompt()


class AgentDemo:
    """智能体演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.agent = SimpleAgent()

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("完整智能体示例")
        print("=" * 50)

        # 配置智能体
        print("\n1. 智能体配置")
        print(f"角色: {self.agent.persona.config.role}")
        print(f"语气: {self.agent.persona.config.tone}")

        # 添加知识
        print("\n2. 添加知识到知识库")
        documents = [
            "Python 使用 def 关键字定义函数",
            "Python 支持列表、字典、集合等数据结构",
            "Python 是解释型语言，无需编译",
        ]
        self.agent.add_knowledge(documents)
        print(f"已添加 {len(documents)} 条知识")

        # 对话演示
        print("\n3. 对话演示")
        queries = [
            "Python 如何定义函数？",
            "北京天气怎么样？",
            "Python 是编译型语言吗？",
        ]

        for query in queries:
            print(f"\n用户: {query}")
            result = self.agent.chat(query)
            print(f"智能体: {result['response']}")
            print(f"意图: {result['intent']}")

        # 显示对话历史
        print("\n4. 对话历史")
        for msg in self.agent.get_history():
            role = "用户" if msg["role"] == "user" else "智能体"
            content = (
                msg["content"][:50] + "..."
                if len(msg["content"]) > 50
                else msg["content"]
            )
            print(f"[{role}] {content}")


def demo() -> None:
    """演示智能体功能"""
    demo_instance = AgentDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
