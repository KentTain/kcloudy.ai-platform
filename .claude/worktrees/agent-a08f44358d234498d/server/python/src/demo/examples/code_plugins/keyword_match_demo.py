"""
关键词匹配插件示例

演示关键词匹配逻辑：
- 单关键词匹配
- 多关键词匹配
- 优先级匹配

示例使用：
    plugin = KeywordMatchPlugin()
    plugin.add_rule(MatchRule("Python", "Python 是编程语言"))
    result = plugin.match("什么是 Python")
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MatchRule:
    """匹配规则

    Attributes:
        keyword: 关键词
        answer: 回答内容
        priority: 优先级（数字越大优先级越高）
    """

    keyword: str
    answer: str
    priority: int = 0


class KeywordMatchPlugin:
    """关键词匹配插件

    支持多关键词匹配和优先级排序。
    """

    def __init__(self) -> None:
        """初始化插件"""
        self._rules: list[MatchRule] = []

    def add_rule(self, rule: MatchRule) -> None:
        """添加匹配规则

        Args:
            rule: 匹配规则
        """
        self._rules.append(rule)
        # 按优先级排序
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def add_rules(self, rules: list[MatchRule]) -> None:
        """批量添加规则

        Args:
            rules: 规则列表
        """
        for rule in rules:
            self.add_rule(rule)

    def match(self, text: str) -> dict[str, Any]:
        """匹配文本

        Args:
            text: 输入文本

        Returns:
            匹配结果
        """
        text_lower = text.lower()
        matches: list[MatchRule] = []

        for rule in self._rules:
            if rule.keyword.lower() in text_lower:
                matches.append(rule)

        if not matches:
            return {
                "matched": False,
                "answer": "未找到匹配内容",
                "keyword": None,
                "priority": None,
            }

        # 返回优先级最高的匹配
        best_match = matches[0]
        return {
            "matched": True,
            "answer": best_match.answer,
            "keyword": best_match.keyword,
            "priority": best_match.priority,
            "all_matches": [
                {"keyword": r.keyword, "priority": r.priority} for r in matches
            ],
        }

    def match_all(self, text: str) -> list[dict[str, Any]]:
        """返回所有匹配结果

        Args:
            text: 输入文本

        Returns:
            所有匹配结果列表
        """
        text_lower = text.lower()
        results: list[dict[str, Any]] = []

        for rule in self._rules:
            if rule.keyword.lower() in text_lower:
                results.append(
                    {
                        "keyword": rule.keyword,
                        "answer": rule.answer,
                        "priority": rule.priority,
                    }
                )

        return results

    def clear_rules(self) -> None:
        """清空所有规则"""
        self._rules.clear()

    def count_rules(self) -> int:
        """返回规则数量"""
        return len(self._rules)


class KeywordMatchDemo:
    """关键词匹配演示类"""

    def __init__(self) -> None:
        """初始化演示"""
        self.plugin = KeywordMatchPlugin()

        # 添加示例规则
        self.plugin.add_rules(
            [
                MatchRule("Python", "Python 是一种解释型编程语言", priority=5),
                MatchRule("函数", "函数使用 def 关键字定义", priority=3),
                MatchRule("类", "类使用 class 关键字定义", priority=3),
                MatchRule("列表", "列表是有序的可变序列", priority=2),
                MatchRule("编程", "编程是编写计算机程序的过程", priority=1),
            ]
        )

    def run_demo(self) -> None:
        """运行演示"""
        print("=" * 50)
        print("关键词匹配插件示例")
        print("=" * 50)

        print(f"\n已加载 {self.plugin.count_rules()} 条规则")

        # 单关键词匹配
        print("\n1. 单关键词匹配")
        result = self.plugin.match("什么是 Python？")
        print(f"匹配结果: {result['matched']}")
        print(f"关键词: {result['keyword']}")
        print(f"回答: {result['answer']}")

        # 多关键词匹配
        print("\n2. 多关键词匹配")
        result = self.plugin.match("Python 函数和类怎么定义？")
        print(f"最佳匹配: {result['keyword']} (优先级: {result['priority']})")
        print(f"所有匹配: {result.get('all_matches', [])}")

        # 获取所有匹配
        print("\n3. 获取所有匹配")
        all_matches = self.plugin.match_all("Python 编程入门")
        for m in all_matches:
            print(f"  - [{m['priority']}] {m['keyword']}: {m['answer'][:30]}...")

        # 无匹配
        print("\n4. 无匹配情况")
        result = self.plugin.match("Java 怎么样？")
        print(f"匹配结果: {result['matched']}")
        print(f"回答: {result['answer']}")


def demo() -> None:
    """演示关键词匹配功能"""
    demo_instance = KeywordMatchDemo()
    demo_instance.run_demo()


if __name__ == "__main__":
    demo()
