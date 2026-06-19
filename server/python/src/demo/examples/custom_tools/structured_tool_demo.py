"""
StructuredTool 结构化工具示例

演示如何使用 StructuredTool 创建复杂的结构化工具。
适合需要复杂输入参数、错误处理和状态管理的工具。

Day 3 讲义：AI 智能体应用实战 - 自定义工具开发
"""

from typing import Annotated

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# ==================== 输入模型定义 ====================


class SearchInput(BaseModel):
    """搜索工具输入参数"""

    query: Annotated[str, Field(description="搜索关键词")]
    max_results: Annotated[
        int, Field(default=5, ge=1, le=20, description="最大返回结果数")
    ]
    include_images: Annotated[
        bool, Field(default=False, description="是否包含图片结果")
    ]


class DatabaseQueryInput(BaseModel):
    """数据库查询输入参数"""

    table_name: Annotated[str, Field(description="表名")]
    columns: Annotated[list[str], Field(default=["*"], description="要查询的列名列表")]
    where_clause: Annotated[str | None, Field(default=None, description="WHERE 条件")]
    limit: Annotated[int, Field(default=10, ge=1, le=100, description="返回行数限制")]


class EmailInput(BaseModel):
    """邮件发送输入参数"""

    to: Annotated[str, Field(description="收件人邮箱")]
    subject: Annotated[str, Field(description="邮件主题")]
    body: Annotated[str, Field(description="邮件正文")]
    cc: Annotated[list[str] | None, Field(default=None, description="抄送列表")]
    priority: Annotated[
        str, Field(default="normal", description="优先级：high, normal, low")
    ]


# ==================== 结构化工具类 ====================


class SearchTool:
    """
    搜索工具类

    使用 StructuredTool 创建，支持复杂的输入验证和错误处理。
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        初始化搜索工具

        Args:
            api_key: API 密钥（模拟）
        """
        self.api_key = api_key
        self._call_count = 0

    def _search(
        self,
        query: str,
        max_results: int = 5,
        include_images: bool = False,
    ) -> str:
        """
        执行搜索（模拟）

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            include_images: 是否包含图片

        Returns:
            搜索结果
        """
        self._call_count += 1

        # 模拟搜索结果
        results = []
        for i in range(max_results):
            result = {
                "title": f"{query} - 结果 {i + 1}",
                "url": f"https://example.com/search/{query}/{i + 1}",
                "snippet": f"这是关于 {query} 的第 {i + 1} 条搜索结果...",
            }
            if include_images:
                result["image"] = f"https://images.example.com/{query}_{i + 1}.jpg"
            results.append(result)

        # 格式化输出
        output = f"搜索 '{query}' 找到 {len(results)} 个结果（调用次数：{self._call_count}）：\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   URL: {r['url']}\n"
            output += f"   摘要: {r['snippet']}\n"
            if "image" in r:
                output += f"   图片: {r['image']}\n"
            output += "\n"

        return output

    def _handle_error(self, error: Exception) -> str:
        """
        错误处理

        Args:
            error: 异常对象

        Returns:
            错误消息
        """
        return f"搜索失败: {error!s}"

    def create_tool(self) -> StructuredTool:
        """
        创建 StructuredTool 实例

        Returns:
            StructuredTool 实例
        """
        return StructuredTool(
            name="search",
            description="搜索网络获取信息。支持指定最大结果数和是否包含图片。",
            func=self._search,
            args_schema=SearchInput,
            handle_tool_error=self._handle_error,
        )


class DatabaseQueryTool:
    """
    数据库查询工具

    展示如何创建需要多个复杂参数的工具。
    """

    def __init__(self) -> None:
        """初始化数据库连接（模拟）"""
        self._mock_data = {
            "users": [
                {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
                {"id": 2, "name": "李四", "email": "lisi@example.com"},
                {"id": 3, "name": "王五", "email": "wangwu@example.com"},
            ],
            "products": [
                {"id": 1, "name": "笔记本电脑", "price": 5999},
                {"id": 2, "name": "鼠标", "price": 99},
                {"id": 3, "name": "键盘", "price": 199},
            ],
        }

    def _query(
        self,
        table_name: str,
        columns: list[str] | None = None,
        where_clause: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        执行数据库查询（模拟）

        Args:
            table_name: 表名
            columns: 要查询的列名列表
            where_clause: WHERE 条件
            limit: 返回行数限制

        Returns:
            查询结果
        """
        if columns is None:
            columns = ["*"]

        # 检查表是否存在
        if table_name not in self._mock_data:
            return f"错误：表 '{table_name}' 不存在。可用表：{list(self._mock_data.keys())}"

        data = self._mock_data[table_name]

        # 应用 WHERE 条件（简化模拟）
        if where_clause:
            # 实际应用中应该解析 WHERE 子句
            data = [row for row in data if eval(where_clause, {}, row)]

        # 应用列选择
        if columns != ["*"]:
            data = [{k: v for k, v in row.items() if k in columns} for row in data]

        # 应用限制
        data = data[:limit]

        # 格式化输出
        import json

        return json.dumps(data, ensure_ascii=False, indent=2)

    def create_tool(self) -> StructuredTool:
        """
        创建 StructuredTool 实例

        Returns:
            StructuredTool 实例
        """
        return StructuredTool(
            name="database_query",
            description="查询数据库表。支持指定表名、列、WHERE条件和返回行数限制。",
            func=self._query,
            args_schema=DatabaseQueryInput,
        )


class EmailTool:
    """
    邮件发送工具

    展示如何创建带有验证逻辑的工具。
    """

    @staticmethod
    def _validate_email(email: str) -> bool:
        """简单的邮箱格式验证"""
        return "@" in email and "." in email.split("@")[1]

    @staticmethod
    def _send(
        to: str,
        subject: str,
        body: str,
        cc: list[str] | None = None,
        priority: str = "normal",
    ) -> str:
        """
        发送邮件（模拟）

        Args:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            cc: 抄送列表
            priority: 优先级

        Returns:
            发送结果
        """
        # 验证邮箱格式
        if not EmailTool._validate_email(to):
            return f"错误：无效的收件人邮箱地址 '{to}'"

        # 模拟发送
        result = [
            "邮件发送成功！",
            f"收件人: {to}",
            f"主题: {subject}",
            f"优先级: {priority}",
        ]

        if cc:
            for cc_email in cc:
                if not EmailTool._validate_email(cc_email):
                    return f"错误：无效的抄送邮箱地址 '{cc_email}'"
            result.append(f"抄送: {', '.join(cc)}")

        result.append(f"\n正文:\n{body}")

        return "\n".join(result)

    @classmethod
    def create_tool(cls) -> StructuredTool:
        """
        创建 StructuredTool 实例

        Returns:
            StructuredTool 实例
        """
        return StructuredTool(
            name="send_email",
            description="发送电子邮件。支持设置收件人、主题、正文、抄送和优先级。",
            func=cls._send,
            args_schema=EmailInput,
        )


# ==================== 演示函数 ====================


def demo_structured_tools() -> None:
    """演示结构化工具"""
    print("=== StructuredTool 演示 ===\n")

    # 搜索工具
    print("1. 搜索工具：")
    search_tool = SearchTool(api_key="demo_key").create_tool()
    result = search_tool.invoke(
        {"query": "LangChain", "max_results": 3, "include_images": True}
    )
    print(result)

    # 数据库查询工具
    print("2. 数据库查询工具：")
    db_tool = DatabaseQueryTool().create_tool()

    result1 = db_tool.invoke(
        {"table_name": "users", "columns": ["name", "email"], "limit": 2}
    )
    print(f"查询用户表：\n{result1}\n")

    result2 = db_tool.invoke({"table_name": "products", "columns": ["*"], "limit": 5})
    print(f"查询产品表：\n{result2}\n")

    # 邮件工具
    print("3. 邮件工具：")
    email_tool = EmailTool.create_tool()
    result = email_tool.invoke(
        {
            "to": "user@example.com",
            "subject": "测试邮件",
            "body": "这是一封测试邮件。",
            "priority": "high",
        }
    )
    print(result)


if __name__ == "__main__":
    demo_structured_tools()
