# 启动完成日志整理 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [x]`）语法来跟踪进度。

**目标：** 为 Python 后端的三个启动入口（runserver、runtask、runlistener）增加结构化启动完成日志，按阶段输出耗时、已加载模块和访问地址。

**架构：** 新增 `StartupTimer` 工具类，通过 `phase()` 上下文管理器包裹启动阶段逻辑，启动完成后调用 `print_summary()` 输出 Alon 风格的启动摘要。

**技术栈：** Python 3.12、FastAPI、loguru、pytest

---

## 文件结构

| 操作 | 文件 | 职责 |
| --- | --- | --- |
| 创建 | `src/framework/utils/startup_timer.py` | 启动计时工具类 |
| 创建 | `tests/framework/unit/utils/test_startup_timer.py` | StartupTimer 单元测试 |
| 修改 | `src/application_web.py` | Web 启动流程集成 |
| 修改 | `src/application_task.py` | 任务调度器启动流程集成 |
| 修改 | `src/application_listener.py` | 消息监听器启动流程集成 |

---

## 任务 1：StartupTimer 工具类与单元测试

**文件：**
- 创建：`src/framework/utils/startup_timer.py`
- 创建：`tests/framework/unit/utils/test_startup_timer.py`

- [x] **步骤 1：编写失败的测试 - PhaseInfo 数据类**

创建测试文件 `tests/framework/unit/utils/test_startup_timer.py`：

```python
"""StartupTimer 单元测试"""

import pytest
from io import StringIO
import sys


class TestPhaseInfo:
    """PhaseInfo 数据类测试"""

    def test_phase_info_creation(self):
        """测试 PhaseInfo 创建"""
        from framework.utils.startup_timer import PhaseInfo

        phase = PhaseInfo(name="配置加载")
        assert phase.name == "配置加载"
        assert phase.duration == 0.0
        assert phase.details == {}

    def test_phase_info_with_details(self):
        """测试 PhaseInfo 带明细"""
        from framework.utils.startup_timer import PhaseInfo

        phase = PhaseInfo(name="基础组件", details={"数据库": "PostgreSQL"})
        assert phase.name == "基础组件"
        assert phase.details == {"数据库": "PostgreSQL"}


class TestStartupTimer:
    """StartupTimer 测试"""

    def test_timer_creation(self):
        """测试计时器创建"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer(app_name="Test App")
        assert timer.app_name == "Test App"
        assert len(timer.phases) == 0

    def test_phase_context_manager(self):
        """测试阶段计时上下文管理器"""
        from framework.utils.startup_timer import StartupTimer
        import time

        timer = StartupTimer()

        with timer.phase("配置加载"):
            time.sleep(0.01)  # 10ms

        assert len(timer.phases) == 1
        assert timer.phases[0].name == "配置加载"
        assert timer.phases[0].duration >= 0.01

    def test_add_detail(self):
        """测试添加阶段明细"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer()

        with timer.phase("基础组件") as phase:
            phase.details["数据库"] = "PostgreSQL"
            phase.details["TenantProvider"] = "已注册"

        assert timer.phases[0].details == {
            "数据库": "PostgreSQL",
            "TenantProvider": "已注册",
        }

    def test_multiple_phases(self):
        """测试多个阶段"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer()

        with timer.phase("阶段1"):
            pass
        with timer.phase("阶段2"):
            pass
        with timer.phase("阶段3"):
            pass

        assert len(timer.phases) == 3
        assert [p.name for p in timer.phases] == ["阶段1", "阶段2", "阶段3"]

    def test_print_summary_output(self):
        """测试摘要输出格式"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer(app_name="Demo API")

        with timer.phase("配置加载"):
            pass
        with timer.phase("基础组件") as phase:
            phase.details["数据库"] = "PostgreSQL"

        # 捕获 stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            timer.print_summary(
                modules=["demo", "iam"],
                address="http://127.0.0.1:8000",
                docs_path="/docs",
            )
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        assert "Demo API 启动完成" in output
        assert "总启动耗时" in output
        assert "阶段1 (配置加载)" in output
        assert "阶段2 (基础组件)" in output
        assert "数据库: PostgreSQL" in output
        assert "已加载模块: 2 个" in output
        assert "- demo" in output
        assert "- iam" in output
        assert "http://127.0.0.1:8000" in output
        assert "http://127.0.0.1:8000/docs" in output

    def test_print_summary_without_modules(self):
        """测试无模块时的摘要输出"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer(app_name="Task Scheduler")

        with timer.phase("配置加载"):
            pass

        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            timer.print_summary()
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        assert "Task Scheduler 启动完成" in output
        assert "已加载模块" not in output
        assert "访问地址" not in output

    def test_phase_exception_handling(self):
        """测试阶段异常时仍记录耗时"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer()

        try:
            with timer.phase("失败阶段"):
                raise ValueError("测试异常")
        except ValueError:
            pass

        # 即使异常，阶段也应该被记录
        assert len(timer.phases) == 1
        assert timer.phases[0].name == "失败阶段"
```

- [x] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/framework/unit/utils/test_startup_timer.py -v
```

预期：FAIL，报错 "No module named 'framework.utils.startup_timer'"

- [x] **步骤 3：创建 `src/framework/utils/__init__.py`（如不存在）**

```bash
touch src/framework/utils/__init__.py
```

- [x] **步骤 4：编写 StartupTimer 实现代码**

创建 `src/framework/utils/startup_timer.py`：

```python
"""启动计时器，用于记录和输出启动阶段耗时"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from time import time
from typing import Iterator


@dataclass
class PhaseInfo:
    """阶段信息"""

    name: str
    duration: float = 0.0
    details: dict[str, str] = field(default_factory=dict)


class StartupTimer:
    """启动计时器，用于记录和输出启动阶段耗时

    使用示例：
        timer = StartupTimer(app_name="Demo API")

        with timer.phase("配置加载"):
            # 加载配置
            pass

        with timer.phase("基础组件") as phase:
            # 初始化数据库
            phase.details["数据库"] = "PostgreSQL"

        timer.print_summary(modules=["demo", "iam"])
    """

    def __init__(self, app_name: str = "应用"):
        self.app_name = app_name
        self.start_time = time()
        self.phases: list[PhaseInfo] = []
        self._current_phase: PhaseInfo | None = None

    @contextmanager
    def phase(self, name: str) -> Iterator[PhaseInfo]:
        """阶段计时上下文管理器

        Args:
            name: 阶段名称

        Yields:
            PhaseInfo: 阶段信息对象，可添加 details
        """
        self._current_phase = PhaseInfo(name=name)
        phase_start = time()
        try:
            yield self._current_phase
        finally:
            self._current_phase.duration = time() - phase_start
            self.phases.append(self._current_phase)
            self._current_phase = None

    def print_summary(
        self,
        modules: list[str] | None = None,
        address: str | None = None,
        docs_path: str | None = None,
        extra_info: dict[str, str] | None = None,
    ) -> None:
        """打印启动完成摘要

        Args:
            modules: 已加载模块列表
            address: 访问地址
            docs_path: API 文档路径
            extra_info: 额外信息
        """
        total_duration = time() - self.start_time

        print("\n" + "=" * 60)
        print(f"{self.app_name} 启动完成！")
        print(f"总启动耗时: {total_duration:.3f} 秒")
        print("启动阶段耗时:")

        for i, phase in enumerate(self.phases, 1):
            print(f"  阶段{i} ({phase.name}): {phase.duration:.3f}秒")
            if phase.details:
                for key, value in phase.details.items():
                    print(f"    - {key}: {value}")

        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if modules:
            print(f"🔌 已加载模块: {len(modules)} 个")
            for name in modules:
                print(f"   - {name}")

        if extra_info:
            for key, value in extra_info.items():
                print(f"{key}: {value}")

        if address:
            print(f"\n访问地址: {address}")
            if docs_path:
                print(f"API 文档: {address}{docs_path}")

        print("=" * 60 + "\n")
```

- [x] **步骤 5：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/framework/unit/utils/test_startup_timer.py -v
```

预期：PASS

- [x] **步骤 6：Commit**

```bash
git add src/framework/utils/startup_timer.py tests/framework/unit/utils/test_startup_timer.py
git commit -m "feat(framework): 新增 StartupTimer 启动计时工具类

- 新增 PhaseInfo 数据类记录阶段信息
- 新增 StartupTimer 类支持阶段计时和摘要输出
- 使用上下文管理器包裹阶段逻辑
- 支持阶段明细和模块列表输出

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 任务 2：Web 启动流程集成

**文件：**
- 修改：`src/application_web.py`

- [x] **步骤 1：修改 application_web.py 导入部分**

在 `src/application_web.py` 文件顶部添加 `StartupTimer` 导入：

```python
# 在现有导入后添加
from framework.utils.startup_timer import StartupTimer
```

- [x] **步骤 2：在 create_app 函数中集成模块加载计时**

修改 `create_app` 函数，在模块加载前后添加计时：

找到 `create_app` 函数中加载模块的代码块，修改为：

```python
def create_app(module_names: list[str] | None = None) -> FastAPI:
    """
    创建 FastAPI 应用实例

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部

    Returns:
        FastAPI 应用实例
    """
    # 初始化启动计时器
    timer = StartupTimer(app_name="Demo API")

    # 阶段1: 配置加载（配置已在 import 时加载）
    with timer.phase("配置加载"):
        # 配置已在模块导入时加载
        pass

    # 如果未指定模块，尝试从配置文件读取
    if module_names is None:
        try:
            from config.modules import ENABLED_MODULES
            module_names = ENABLED_MODULES
            _logger.info(f"Loaded modules from config: {ENABLED_MODULES}")
        except ImportError:
            _logger.info("No modules config found, loading all modules")

    # 阶段3: 模块加载与路由注册
    with timer.phase("模块加载与路由注册"):
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)

        _logger.info(f"已加载模块: {[m.name for m in modules]}")

    # ... 后续代码保持不变，直到 app = FastAPI(...) ...

    app = FastAPI(
        title=APP_NAME,
        description="最小化 AI 助手平台",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # 注册异常处理器
    from demo.common.exception_handler import register_exception_handlers
    register_exception_handlers(app)

    # 注册租户中间件（解析 X-Tenant-Id 并注入上下文）
    app.add_middleware(TenantMiddleware)

    # 动态注册各模块路由
    for module in modules:
        for router, prefix, tags in module.get_routers():
            app.include_router(router, prefix=prefix, tags=tags)
            _logger.info(f"注册路由: {prefix} [{module.name}]")

    # 动态注册各模块中间件
    for module in modules:
        for middleware_class in module.get_middlewares():
            app.add_middleware(middleware_class)
            _logger.info(f"注册中间件: {middleware_class.__name__} [{module.name}]")

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": APP_NAME}

    # 将 timer 存储到 app.state，供 lifespan 使用
    app.state.startup_timer = timer

    return app
```

- [x] **步骤 3：修改 lifespan 函数集成基础组件和数据初始化计时**

修改 `lifespan` 函数：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    timer: StartupTimer = app.state.startup_timer

    _logger.info(
        f"\nDemo 应用开始启动... ({datetime.now(tz=ChinaTimeZone).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # 阶段2: 基础组件初始化
    with timer.phase("基础组件初始化") as phase:
        sqlalchemy_config = settings.sqlalchemy
        setup_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )
        phase.details["数据库"] = "PostgreSQL"

        # 注册 TenantProvider
        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"

    # 阶段4: 数据初始化
    with timer.phase("数据初始化"):
        await _run_seed_initialization()

    # 输出启动摘要
    registry = get_registry()
    module_names = [m.name for m in registry.get_all_modules()]
    display_host = "127.0.0.1" if settings.server.host == "0.0.0.0" else settings.server.host
    timer.print_summary(
        modules=module_names,
        address=f"http://{display_host}:{settings.server.port}",
        docs_path="/docs",
    )

    yield

    _logger.info("Demo 应用关闭")
```

- [x] **步骤 4：验证导入完整性**

确保所有需要的导入已添加：

```python
# application_web.py 顶部导入部分
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from framework.common.time import ChinaTimeZone
from framework.database.core.engine import setup_engine
from framework.module import load_modules, get_registry, ModuleDescriptor
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.protocols import register_tenant_provider
from framework.utils.startup_timer import StartupTimer
from demo.configs import settings
```

- [x] **步骤 5：运行框架测试确保无破坏**

```bash
cd server/python && uv run pytest tests/framework/ -v
```

预期：PASS

- [x] **步骤 6：Commit**

```bash
git add src/application_web.py
git commit -m "feat(web): 集成 StartupTimer 到 Web 启动流程

- 在 create_app 中记录配置加载和模块加载阶段
- 在 lifespan 中记录基础组件初始化和数据初始化阶段
- 启动完成后输出结构化启动摘要

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 任务 3：任务调度器启动流程集成

**文件：**
- 修改：`src/application_task.py`

- [x] **步骤 1：修改 application_task.py 导入部分**

在 `src/application_task.py` 文件顶部添加导入：

```python
# 在现有导入后添加
from framework.utils.startup_timer import StartupTimer
```

- [x] **步骤 2：修改 run_task 函数集成启动计时**

修改 `run_task` 函数：

```python
async def run_task(module_names: list[str] | None = None) -> None:
    """
    启动任务调度器

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部
    """
    timer = StartupTimer(app_name="任务调度器")

    # 阶段1: 配置加载
    with timer.phase("配置加载"):
        if module_names is None:
            try:
                from config.modules import ENABLED_MODULES
                module_names = ENABLED_MODULES
                _logger.info(f"Loaded modules from config: {ENABLED_MODULES}")
            except ImportError:
                _logger.info("No modules config found, loading all modules")

    # 阶段3: 模块加载
    with timer.phase("模块加载"):
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)
        _logger.info(f"已加载模块: {[m.name for m in modules]}")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop.set_result(None))

    # 阶段2: 基础组件初始化
    with timer.phase("基础组件初始化") as phase:
        try:
            from demo.configs import settings
            from framework.database.core.engine import setup_engine

            sqlalchemy_config = settings.sqlalchemy
            setup_engine(
                database_url=sqlalchemy_config.url,
                echo=sqlalchemy_config.echo,
                pool_size=sqlalchemy_config.pool.size,
                max_overflow=sqlalchemy_config.pool.max_overflow,
            )
            phase.details["数据库"] = "PostgreSQL"
        except Exception:
            _logger.exception("数据库引擎初始化失败")

        # 注册 TenantProvider
        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"

    # 阶段4: 任务调度器启动
    with timer.phase("任务调度器启动") as phase:
        setup_funcs = []
        cleanup_funcs = []

        registry = get_registry()
        for module in registry.get_all_modules():
            task_setup = module.get_task_setup()
            if task_setup is not None:
                setup_func, cleanup_func = task_setup
                setup_funcs.append(setup_func)
                cleanup_funcs.append(cleanup_func)
                _logger.info(f"注册任务调度器: {module.name}")

        for setup_func in setup_funcs:
            await setup_func()

        phase.details["已注册调度器"] = f"{len(setup_funcs)} 个"

    # 输出启动摘要
    registry = get_registry()
    module_names_list = [m.name for m in registry.get_all_modules()]
    timer.print_summary(
        modules=module_names_list,
        extra_info={"状态": "任务调度器正在运行，等待信号中断..."},
    )

    try:
        await stop
    finally:
        for cleanup_func in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception:
                _logger.exception("任务调度器清理失败")
        _logger.info("所有任务调度器已停止")
```

- [x] **步骤 3：运行框架测试确保无破坏**

```bash
cd server/python && uv run pytest tests/framework/ -v
```

预期：PASS

- [x] **步骤 4：Commit**

```bash
git add src/application_task.py
git commit -m "feat(task): 集成 StartupTimer 到任务调度器启动流程

- 记录配置加载、模块加载、基础组件初始化和任务调度器启动阶段
- 启动完成后输出结构化启动摘要

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 任务 4：消息监听器启动流程集成

**文件：**
- 修改：`src/application_listener.py`

- [x] **步骤 1：修改 application_listener.py 导入部分**

在 `src/application_listener.py` 文件顶部添加导入：

```python
# 在现有导入后添加
from framework.utils.startup_timer import StartupTimer
```

- [x] **步骤 2：修改 run_listener 函数集成启动计时**

修改 `run_listener` 函数：

```python
async def run_listener(module_names: list[str] | None = None) -> None:
    """
    启动消息监听器

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部
    """
    timer = StartupTimer(app_name="消息监听器")

    # 阶段1: 配置加载
    with timer.phase("配置加载"):
        if module_names is None:
            try:
                from config.modules import ENABLED_MODULES
                module_names = ENABLED_MODULES
                _logger.info(f"Loaded modules from config: {ENABLED_MODULES}")
            except ImportError:
                _logger.info("No modules config found, loading all modules")

    # 阶段3: 模块加载
    with timer.phase("模块加载"):
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)
        _logger.info(f"已加载模块: {[m.name for m in modules]}")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop.set_result(None))

    # 阶段2: 基础组件初始化
    with timer.phase("基础组件初始化") as phase:
        try:
            from demo.configs import settings
            from framework.database.core.engine import setup_engine

            sqlalchemy_config = settings.sqlalchemy
            setup_engine(
                database_url=sqlalchemy_config.url,
                echo=sqlalchemy_config.echo,
                pool_size=sqlalchemy_config.pool.size,
                max_overflow=sqlalchemy_config.pool.max_overflow,
            )
            phase.details["数据库"] = "PostgreSQL"
        except Exception:
            _logger.exception("数据库引擎初始化失败")

        # 注册 TenantProvider
        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"

    # 阶段4: 监听器启动
    with timer.phase("监听器启动") as phase:
        setup_funcs = []
        cleanup_funcs = []
        settings_obj = None

        try:
            from demo.configs import settings as demo_settings
            settings_obj = demo_settings
        except ImportError:
            from framework.configs import get_settings
            settings_obj = get_settings()

        registry = get_registry()
        for module in registry.get_all_modules():
            listener_setup = module.get_listener_setup()
            if listener_setup is not None:
                setup_func, cleanup_func = listener_setup
                setup_funcs.append((setup_func, module.name))
                cleanup_funcs.append((cleanup_func, module.name))
                _logger.info(f"注册监听器: {module.name}")

        started_count = 0
        for setup_func, module_name in setup_funcs:
            try:
                await setup_func(settings_obj)
                _logger.info(f"监听器已启动 [{module_name}]")
                started_count += 1
            except Exception:
                _logger.exception(f"监听器启动失败 [{module_name}]")

        phase.details["已启动监听器"] = f"{started_count} 个"

    # 输出启动摘要
    registry = get_registry()
    module_names_list = [m.name for m in registry.get_all_modules()]
    timer.print_summary(
        modules=module_names_list,
        extra_info={"状态": "监听器正在运行，等待消息..."},
    )

    try:
        await stop
    finally:
        for cleanup_func, module_name in cleanup_funcs:
            try:
                await cleanup_func()
            except Exception:
                _logger.exception(f"监听器清理失败 [{module_name}]")
        _logger.info("所有监听器已停止")
```

- [x] **步骤 3：运行框架测试确保无破坏**

```bash
cd server/python && uv run pytest tests/framework/ -v
```

预期：PASS

- [x] **步骤 4：Commit**

```bash
git add src/application_listener.py
git commit -m "feat(listener): 集成 StartupTimer 到消息监听器启动流程

- 记录配置加载、模块加载、基础组件初始化和监听器启动阶段
- 启动完成后输出结构化启动摘要

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 任务 5：最终验证

- [x] **步骤 1：运行全部测试**

```bash
cd server/python && uv run pytest -v
```

预期：PASS

- [x] **步骤 2：手动验证 Web 启动日志（可选，需依赖服务）**

```bash
cd server/python && uv run python manage.py runserver
```

预期输出包含：

```
============================================================
Demo API 启动完成！
总启动耗时: X.XXX 秒
启动阶段耗时:
  阶段1 (配置加载): X.XXX秒
  阶段2 (基础组件初始化): X.XXX秒
    - 数据库: PostgreSQL
  阶段3 (模块加载与路由注册): X.XXX秒
  阶段4 (数据初始化): X.XXX秒
完成时间: YYYY-MM-DD HH:MM:SS
🔌 已加载模块: X 个
   - ...
访问地址: http://127.0.0.1:8000
API 文档: http://127.0.0.1:8000/docs
============================================================
```

- [x] **步骤 3：最终 Commit（如有未提交变更）**

```bash
git status
# 如有未提交变更
git add -A
git commit -m "chore: 启动完成日志整理功能实现完成

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 自检清单

- [x] 规格覆盖度：StartupTimer 工具类（任务 1）、Web 集成（任务 2）、Task 集成（任务 3）、Listener 集成（任务 4）
- [x] 无占位符：所有步骤包含完整代码
- [x] 类型一致性：PhaseInfo、StartupTimer 方法签名在各任务中一致
