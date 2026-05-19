# 测试夹具（Fixtures）目录

本目录包含项目测试使用的共享夹具和测试数据。

## 目录结构

- `data/`: 测试数据文件
- `helpers.py`: 测试辅助函数

## 用途说明

此目录中的内容主要用于：

1. 提供可重用的测试夹具
2. 存放测试数据文件（JSON、CSV等）
3. 提供测试辅助函数

## 使用方法

在测试文件中导入所需的夹具：

```python
import pytest
from tests.fixtures.helpers import setup_test_data

@pytest.fixture
def test_data():
    return setup_test_data()
```

或直接在conftest.py中导入这些夹具，使其全局可用：

```python
# tests/conftest.py
from tests.fixtures.helpers import *
```

## 最佳实践

1. 保持夹具简单，专注于一个特定功能
2. 使用参数化夹具处理多种测试情景
3. 确保夹具适当清理创建的资源
4. 对复杂夹具添加详细文档
