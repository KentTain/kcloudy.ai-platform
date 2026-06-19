import asyncio

import pytest


# 测试异步函数
async def say_hello():
    """
    模拟一个耗时操作，例如网络请求或文件读取
    """
    await asyncio.sleep(1)
    return "Hello, World!"


# 使用 pytest.mark.asyncio 标记异步测试
@pytest.mark.asyncio
async def test_say_hello():
    """
    测试 say_hello 函数是否正确返回预期的字符串
    """
    result = await say_hello()
    assert result == "Hello, World!"


@pytest.mark.asyncio
async def test_concurrent_execution():
    """
    测试多个异步任务的并发执行
    验证并发执行的任务能够正确完成并返回结果
    """
    # 创建一个任务列表
    tasks = [say_hello(), say_hello()]
    # 并发运行任务列表中的任务
    results = await asyncio.gather(*tasks)

    # 验证结果
    assert len(results) == 2
    assert all(result == "Hello, World!" for result in results)
