# 模块系统开发指南

本文件为 Claude Code 在 `src/framework/module/` 模块系统中工作时提供指导。

## 模块定位

Framework 模块系统提供模块化单体架构的基础设施，支持：

- 模块声明与协议定义
- 模块动态扫描与发现
- 模块依赖解析与拓扑排序
- 模块注册中心

## 目录职责

| 文件 | 职责 |
| --- | --- |
| `descriptor.py` | `ModuleDescriptor` Protocol 定义，声明模块必须实现的接口 |
| `registry.py` | `ModuleRegistry` 单例注册中心，管理所有已加载模块 |
| `loader.py` | 模块扫描、过滤、依赖解析和加载器 |
| `__init__.py` | 导出核心类和函数 |

## 核心组件

### ModuleDescriptor Protocol

模块必须实现的协议，定义模块注册信息：

```python
class MyModule:
    @property
    def name(self) -> str:
        return "my_module"

    @property
    def schema(self) -> str:
        return "my_module"

    @property
    def dependencies(self) -> list[str]:
        return ["iam"]  # 依赖 IAM 模块

    def get_base(self) -> type:
        from my_module.models import Base
        return Base

    def get_routers(self) -> list[tuple]:
        return [(router, "/api/v1", ["MyModule"])]

    def get_seeds(self) -> dict[str, Callable]:
        return {"default": seed_func}

    def get_task_setup(self) -> tuple | None:
        return (setup_scheduler, cleanup_scheduler)

    def get_listener_setup(self) -> tuple | None:
        return (setup_listeners, cleanup_listeners)
```

### ModuleRegistry

模块注册中心，提供模块查找和遍历：

```python
from framework.module import get_registry

registry = get_registry()
module = registry.get_module("iam")
all_modules = registry.get_all_modules()
all_bases = registry.get_all_bases()
```

### 模块加载器

加载模块的完整流程：

```python
from framework.module import load_modules
from pathlib import Path

# 加载所有模块
modules = load_modules(Path("src"))

# 加载指定模块
modules = load_modules(Path("src"), module_names=["iam", "demo"])
```

## 开发新模块

### 1. 创建模块目录

在 `src/` 下创建模块目录：

```
src/my_module/
├── __init__.py
├── module.py        # 模块声明（必需）
├── app.py           # 独立应用工厂
├── models/
│   └── __init__.py  # 使用 create_module_base 创建 Base
├── controllers/
├── services/
├── migrations/
│   ├── env.py       # 配置 version_table_schema
│   └── versions/
└── ...
```

### 2. 创建模块 Base

在 `models/__init__.py` 中：

```python
from framework.database import create_module_base, create_base_model

Base = create_module_base("my_module")
BaseModel = create_base_model(Base)
```

### 3. 创建模块声明

在 `module.py` 中实现 `ModuleDescriptor`：

```python
class MyModule:
    @property
    def name(self) -> str:
        return "my_module"
    # ... 实现其他方法
```

### 4. 配置迁移

在 `migrations/env.py` 中：

```python
MODULE_SCHEMA = "my_module"

context.configure(
    connection=connection,
    target_metadata=Base.metadata,
    version_table_schema=MODULE_SCHEMA,
)
```

## 依赖管理

- 在 `dependencies` 属性中声明依赖
- 加载器自动进行拓扑排序
- 循环依赖会抛出 `CyclicDependencyError`

## 按需加载

通过 `--module` 参数按需加载：

```bash
python manage.py runserver --module iam,demo
python manage.py runtask --module demo
python manage.py db migrate --module iam
```

## 测试

模块系统单元测试位于 `tests/framework/unit/module/`。

```bash
uv run pytest tests/framework/unit/module/ -v
```
