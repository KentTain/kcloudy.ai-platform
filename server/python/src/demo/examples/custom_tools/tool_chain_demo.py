"""
工具链编排示例

演示如何将多个工具组合成工具链，实现复杂的任务流程。
包括顺序执行、条件分支和工具组合。

Day 3 讲义：AI 智能体应用实战 - 自定义工具开发
"""

from typing import Any

from langchain_core.tools import tool


# ==================== 基础工具定义 ====================


@tool
def fetch_user_info(user_id: str) -> dict[str, Any]:
    """
    获取用户信息

    Args:
        user_id: 用户ID

    Returns:
        用户信息字典
    """
    # 模拟用户数据
    users = {
        "001": {
            "id": "001",
            "name": "张三",
            "email": "zhangsan@example.com",
            "level": "gold",
        },
        "002": {
            "id": "002",
            "name": "李四",
            "email": "lisi@example.com",
            "level": "silver",
        },
        "003": {
            "id": "003",
            "name": "王五",
            "email": "wangwu@example.com",
            "level": "bronze",
        },
    }
    return users.get(user_id, {"error": f"用户 {user_id} 不存在"})


@tool
def calculate_discount(level: str) -> float:
    """
    根据会员等级计算折扣

    Args:
        level: 会员等级 (gold/silver/bronze)

    Returns:
        折扣率 (0-1)
    """
    discounts = {
        "gold": 0.8,  # 8折
        "silver": 0.9,  # 9折
        "bronze": 0.95,  # 95折
    }
    return discounts.get(level, 1.0)


@tool
def calculate_price(base_price: float, discount: float) -> dict[str, float]:
    """
    计算最终价格

    Args:
        base_price: 原价
        discount: 折扣率

    Returns:
        价格详情
    """
    final_price = base_price * discount
    savings = base_price - final_price
    return {
        "original_price": base_price,
        "discount_rate": discount,
        "final_price": final_price,
        "savings": savings,
    }


@tool
def send_notification(email: str, message: str) -> str:
    """
    发送通知邮件

    Args:
        email: 收件人邮箱
        message: 通知内容

    Returns:
        发送结果
    """
    return f"已发送通知到 {email}: {message}"


# ==================== 工具链类 ====================


class SimpleToolChain:
    """
    简单工具链

    按顺序执行多个工具，前一个工具的输出作为后一个工具的输入。
    """

    def __init__(self, tools: list) -> None:
        """
        初始化工具链

        Args:
            tools: 工具列表，按执行顺序排列
        """
        self.tools = tools
        self.execution_log: list[dict[str, Any]] = []

    def run(self, initial_input: dict[str, Any]) -> dict[str, Any]:
        """
        执行工具链

        Args:
            initial_input: 初始输入参数

        Returns:
            最终输出结果
        """
        current_input = initial_input
        self.execution_log = []

        for i, tool in enumerate(self.tools):
            step_name = f"Step {i + 1}: {tool.name}"
            print(f"\n执行 {step_name}...")
            print(f"  输入: {current_input}")

            try:
                result = tool.invoke(current_input)
                print(f"  输出: {result}")

                self.execution_log.append(
                    {
                        "step": step_name,
                        "tool": tool.name,
                        "input": current_input,
                        "output": result,
                        "status": "success",
                    }
                )

                # 更新下一次调用的输入
                current_input = self._prepare_next_input(
                    tool.name, result, current_input
                )

            except Exception as e:
                self.execution_log.append(
                    {
                        "step": step_name,
                        "tool": tool.name,
                        "input": current_input,
                        "error": str(e),
                        "status": "failed",
                    }
                )
                return {"error": f"工具链执行失败于 {step_name}: {e}"}

        return {
            "success": True,
            "final_result": current_input,
            "log": self.execution_log,
        }

    def _prepare_next_input(
        self,
        tool_name: str,
        result: Any,
        previous_input: dict[str, Any],
    ) -> dict[str, Any]:
        """
        准备下一个工具的输入

        根据当前工具的输出和上下文，准备下一个工具的输入参数。

        Args:
            tool_name: 当前工具名称
            result: 当前工具的输出
            previous_input: 之前的输入

        Returns:
            下一个工具的输入参数
        """
        # 这里可以根据工具名称定义不同的转换逻辑
        if tool_name == "fetch_user_info":
            return {"level": result.get("level", "bronze")}
        elif tool_name == "calculate_discount":
            return {
                "base_price": previous_input.get("base_price", 100),
                "discount": result,
            }
        elif tool_name == "calculate_price":
            return result
        return result


class ConditionalToolChain:
    """
    条件工具链

    支持根据中间结果选择不同的执行路径。
    """

    def __init__(self) -> None:
        """初始化条件工具链"""
        self.tools = {
            "fetch": fetch_user_info,
            "discount": calculate_discount,
            "price": calculate_price,
            "notify": send_notification,
        }

    def run_order_flow(self, user_id: str, base_price: float) -> dict[str, Any]:
        """
        执行订单流程

        根据用户等级走不同的优惠流程。

        Args:
            user_id: 用户ID
            base_price: 商品原价

        Returns:
            订单结果
        """
        results = {"user_id": user_id, "base_price": base_price}

        # Step 1: 获取用户信息
        user_info = self.tools["fetch"].invoke({"user_id": user_id})
        if "error" in user_info:
            return {"error": user_info["error"]}
        results["user_info"] = user_info

        # Step 2: 计算折扣
        discount = self.tools["discount"].invoke({"level": user_info["level"]})
        results["discount_rate"] = discount

        # Step 3: 计算价格
        price_info = self.tools["price"].invoke(
            {
                "base_price": base_price,
                "discount": discount,
            }
        )
        results["price_info"] = price_info

        # Step 4: 条件分支 - 只有 gold 会员发送通知
        if user_info["level"] == "gold":
            message = f"尊敬的 {user_info['name']}，您的订单已确认，最终价格：{price_info['final_price']:.2f}元"
            notification = self.tools["notify"].invoke(
                {
                    "email": user_info["email"],
                    "message": message,
                }
            )
            results["notification"] = notification

        return results


# ==================== 演示函数 ====================


def demo_tool_chain() -> None:
    """演示工具链"""
    print("=== 工具链演示 ===\n")

    # 简单工具链
    print("1. 简单顺序工具链：")
    print("-" * 50)

    chain = SimpleToolChain(
        [
            fetch_user_info,
            calculate_discount,
            calculate_price,
        ]
    )

    result = chain.run({"user_id": "001", "base_price": 1000})
    print(f"\n最终结果：{result}")

    print("\n" + "=" * 50 + "\n")

    # 条件工具链
    print("2. 条件工具链：")
    print("-" * 50)

    conditional_chain = ConditionalToolChain()

    # Gold 会员 - 会发送通知
    print("\nGold 会员订单：")
    result1 = conditional_chain.run_order_flow("001", 500)
    import json

    print(json.dumps(result1, ensure_ascii=False, indent=2))

    # Silver 会员 - 不会发送通知
    print("\nSilver 会员订单：")
    result2 = conditional_chain.run_order_flow("002", 500)
    print(json.dumps(result2, ensure_ascii=False, indent=2))


def demo_tool_composition() -> None:
    """演示工具组合"""
    print("\n=== 工具组合演示 ===\n")

    # 组合多个工具创建复杂功能
    @tool
    def process_order(user_id: str, product_name: str, base_price: float) -> str:
        """
        处理订单（组合工具）

        将多个步骤封装成一个工具。

        Args:
            user_id: 用户ID
            product_name: 商品名称
            base_price: 商品原价

        Returns:
            订单处理结果
        """
        # 获取用户信息
        user_info = fetch_user_info.invoke({"user_id": user_id})
        if "error" in user_info:
            return user_info["error"]

        # 计算折扣和价格
        discount = calculate_discount.invoke({"level": user_info["level"]})
        price_info = calculate_price.invoke(
            {"base_price": base_price, "discount": discount}
        )

        # 生成订单结果
        return f"""
订单确认
========
用户: {user_info["name"]} ({user_info["level"]} 会员)
商品: {product_name}
原价: ¥{price_info["original_price"]:.2f}
折扣: {(1 - discount) * 100:.0f}%
实付: ¥{price_info["final_price"]:.2f}
节省: ¥{price_info["savings"]:.2f}
"""

    # 使用组合工具
    result = process_order.invoke(
        {
            "user_id": "001",
            "product_name": "无线蓝牙耳机",
            "base_price": 299,
        }
    )
    print(result)


if __name__ == "__main__":
    demo_tool_chain()
    demo_tool_composition()
