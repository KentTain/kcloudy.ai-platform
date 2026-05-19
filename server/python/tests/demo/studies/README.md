# 代码预研目录

本目录用于存放代码预研和技术探索的示例，不是正式测试。

## 用途说明

此目录中的代码主要用于：

1. 技术可行性验证
2. 概念验证(POC)开发
3. 新技术学习和实验
4. 性能和功能测试原型

## 目录结构

```text
studies/
├── examples/           # 基础技术示例
│   ├── test_asyncio.py
│   ├── test_mysql_connection.py
│   ├── test_orjson.py
│   └── ...
│
├── langchain_study/    # LangChain 学习示例
│   └── test_summary.py # 文本总结策略（Stuff/Map-Reduce/Refine）
│
└── langgraph_study/    # LangGraph 状态图测试
    ├── test_langgraph_1.py  # 基础状态图
    ├── test_langgraph_2.py  # 条件路由
    ├── test_langgraph_3.py  # 汇聚点
    ├── test_langgraph_4.py  # 子图示例
    ├── test_langgraph_5.py  # 暂停恢复
    ├── test_langgraph_6.py  # 条件路由示例
    ├── test_langgraph_8.py  # 并行中断
    ├── test_langgraph_9.py  # 单节点多中断
    └── test_langgraph_10.py # 重试机制
```

## LangChain 示例

### 文本总结（test_summary.py）

演示三种文本总结策略：

- **Stuff**: 一次性处理所有内容
- **Map-Reduce**: 分块总结后合并
- **Refine**: 迭代优化总结

```bash
# 运行示例
uv run python tests/studies/langchain/summary.py
```

## LangGraph 测试

### 基础状态图（test_langgraph_1.py）

演示如何构建和执行简单的状态图：

- 节点定义和状态传递
- 边的连接和执行流程
- 同步/异步执行

### 条件路由（test_langgraph_2.py）

演示条件边的使用：

- `add_conditional_edges` 动态路由
- 路由函数和路径映射

### 汇聚点（test_langgraph_3.py）

演示多节点汇聚的正确处理：

- 多起点边语法 `["node_a", "node_b"]`
- 避免汇聚节点重复执行

### 子图示例（test_langgraph_4.py）

演示子图（Subgraph）的使用：

- 子图构建和独立执行
- 父图调用子图
- 状态共享与转换

### 暂停恢复（test_langgraph_5.py）

演示 LangGraph 的中断和恢复机制：

- `interrupt()` 暂停执行
- `Command(resume=value)` 恢复执行
- `InMemorySaver` 状态持久化

### 条件路由示例（test_langgraph_6.py）

演示基于状态的条件路由：

- 条件节点更新状态
- 路由函数根据状态值决策
- `add_conditional_edges` 定义分支

### 并行中断（test_langgraph_8.py）

演示并行节点的中断处理：

- 多个节点同时触发中断
- 使用 `resume_map` 批量恢复
- 流式模式处理中断

### 单节点多中断（test_langgraph_9.py）

演示同一节点内多次中断：

- 顺序中断和恢复
- 状态检查决定中断点

### 重试机制（test_langgraph_10.py）

演示 RetryPolicy 配置：

- `max_attempts` 最大重试次数
- `retry_on` 自定义重试条件
- `backoff_factor` 退避策略

```bash
# 运行所有 LangGraph 测试
uv run pytest tests/studies/langgraph_study/ -v -s
```

## 使用指南

预研代码不需要遵循严格的测试规范，但建议：

1. 为每个预研例子添加清晰的注释
2. 在每个目录中添加README说明用途和使用方法
3. 清理不再需要的预研代码
