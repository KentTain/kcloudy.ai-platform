"""StartupTimer 单元测试"""

from io import StringIO
import sys
import time


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

        timer = StartupTimer()

        with timer.phase("配置加载"):
            time.sleep(0.01)

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

    def test_print_summary_orders_phases_by_order(self):
        """测试摘要按 order 输出阶段"""
        from contextlib import redirect_stdout
        from io import StringIO
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer(app_name="Demo API")
        with timer.phase("配置加载", order=1):
            pass
        with timer.phase("模块加载与路由注册", order=3):
            pass
        with timer.phase("基础组件初始化", order=2):
            pass

        captured_output = StringIO()
        with redirect_stdout(captured_output):
            timer.print_summary()

        output = captured_output.getvalue()
        config_index = output.index("阶段1 (配置加载)")
        base_index = output.index("阶段2 (基础组件初始化)")
        module_index = output.index("阶段3 (模块加载与路由注册)")
        assert config_index < base_index < module_index

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

        assert len(timer.phases) == 1
        assert timer.phases[0].name == "失败阶段"

    def test_nested_phases(self):
        """测试嵌套阶段"""
        from framework.utils.startup_timer import StartupTimer

        timer = StartupTimer()

        with timer.phase("外层"):
            with timer.phase("内层"):
                pass

        assert len(timer.phases) == 2
        assert [p.name for p in timer.phases] == ["内层", "外层"]
