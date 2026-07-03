"""
InstallTaskService 单元测试

测试安装任务服务的核心功能：
- 创建安装任务
- 更新任务状态
- 更新任务步骤
- 获取任务列表
- 获取任务详情
- 检查超时任务
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin import PluginInstallTask
from ai.schemas.plugin import (
    InstallPluginRequest,
    InstallPluginResponse,
    InstallTaskDetailVo,
    InstallTaskListResponse,
)
from ai.services.install_task_service import INSTALL_STEPS, InstallTaskService
from framework.common.exceptions import BadRequestError, NotFoundError
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation


class TestCreateInstallTask:
    """测试创建安装任务"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        return mock_session

    @pytest.fixture
    def valid_definition(self):
        """有效的插件定义"""
        definition = MagicMock(spec=TenantPluginDefinition)
        definition.plugin_id = "test-author/test-plugin"
        definition.plugin_unique_identifier = "test-author/test-plugin:1.0.0@hash"
        definition.is_enabled = True
        return definition

    def _setup_context(self, tenant_id: str = "tenant-123", user_id: str = "user-456"):
        """设置租户和用户上下文"""

        def get_tenant_id():
            return tenant_id

        def get_user_id():
            return user_id

        return get_tenant_id, get_user_id

    @pytest.mark.asyncio
    async def test_create_install_task_success(self, session, valid_definition):
        """测试成功创建安装任务"""
        # 设置上下文
        get_tenant_id, get_user_id = self._setup_context()

        # 模拟数据库查询
        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = valid_definition

        installation_result = MagicMock()
        installation_result.scalar_one_or_none.return_value = None

        session.execute.side_effect = [def_result, installation_result]

        request = InstallPluginRequest(plugin_id="test-author/test-plugin")

        mock_provider = MagicMock()
        mock_provider.create_installation = AsyncMock()
        mock_provider.update_installation = AsyncMock()

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ), patch(
            "ai.services.install_task_service.get_user_id", side_effect=get_user_id
        ), patch(
            "ai.services.install_task_service.get_plugin_installation_provider",
            return_value=mock_provider,
        ), patch(
            "ai.services.install_task_service.RedisUtil.xadd", new_callable=AsyncMock
        ):

            result = await InstallTaskService.create_install_task(session, request)

        assert isinstance(result, InstallPluginResponse)
        assert result.plugin_id == "test-author/test-plugin"
        assert result.status == "pending"
        assert "安装任务已创建" in result.message

        # 验证添加了任务记录（安装记录通过 Provider 协议创建，不在此 session）
        assert session.add.call_count == 1
        # 验证通过 Provider 创建 PENDING 安装记录
        mock_provider.create_installation.assert_awaited_once()
        assert session.flush.await_count >= 1

    @pytest.mark.asyncio
    async def test_create_install_task_definition_not_found(self, session):
        """测试插件定义不存在"""
        get_tenant_id, _ = self._setup_context()

        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = None
        session.execute.return_value = def_result

        request = InstallPluginRequest(plugin_id="nonexistent/plugin")

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            with pytest.raises(NotFoundError) as exc_info:
                await InstallTaskService.create_install_task(session, request)

        assert "插件定义不存在" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_create_install_task_plugin_disabled(self, session):
        """测试插件已禁用"""
        get_tenant_id, _ = self._setup_context()

        # 模拟已禁用的插件定义
        disabled_definition = MagicMock(spec=TenantPluginDefinition)
        disabled_definition.plugin_id = "disabled/plugin"
        disabled_definition.is_enabled = False

        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = disabled_definition
        session.execute.return_value = def_result

        request = InstallPluginRequest(plugin_id="disabled/plugin")

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            with pytest.raises(BadRequestError) as exc_info:
                await InstallTaskService.create_install_task(session, request)

        assert "插件已禁用" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_create_install_task_already_installed(self, session, valid_definition):
        """测试插件已安装"""
        get_tenant_id, _ = self._setup_context()

        # 模拟已存在的安装记录
        existing_installation = MagicMock(spec=TenantPluginInstallation)

        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = valid_definition

        installation_result = MagicMock()
        installation_result.scalar_one_or_none.return_value = existing_installation

        session.execute.side_effect = [def_result, installation_result]

        request = InstallPluginRequest(plugin_id="test-author/test-plugin")

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            with pytest.raises(BadRequestError) as exc_info:
                await InstallTaskService.create_install_task(session, request)

        assert "插件已安装" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_create_install_task_no_tenant_id(self, session):
        """测试没有租户ID"""
        request = InstallPluginRequest(plugin_id="test/plugin")

        with patch(
            "ai.services.install_task_service.get_tenant_id", return_value=None
        ):
            with pytest.raises(ValueError) as exc_info:
                await InstallTaskService.create_install_task(session, request)

        assert "租户ID不能为空" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_install_task_enqueue_failure(self, session, valid_definition):
        """测试任务入队失败"""
        get_tenant_id, get_user_id = self._setup_context()

        def_result = MagicMock()
        def_result.scalar_one_or_none.return_value = valid_definition

        installation_result = MagicMock()
        installation_result.scalar_one_or_none.return_value = None

        session.execute.side_effect = [def_result, installation_result]

        request = InstallPluginRequest(plugin_id="test-author/test-plugin")

        mock_provider = MagicMock()
        mock_provider.create_installation = AsyncMock()
        mock_provider.update_installation = AsyncMock()

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ), patch(
            "ai.services.install_task_service.get_user_id", side_effect=get_user_id
        ), patch(
            "ai.services.install_task_service.get_plugin_installation_provider",
            return_value=mock_provider,
        ), patch(
            "ai.services.install_task_service.RedisUtil.xadd",
            new_callable=AsyncMock,
            side_effect=Exception("Redis connection failed"),
        ):

            result = await InstallTaskService.create_install_task(session, request)

        # 入队失败时仍然返回响应，但任务状态已更新为 failed
        assert isinstance(result, InstallPluginResponse)
        # 验证入队失败后通过 Provider 回滚安装记录为 FAILED
        mock_provider.update_installation.assert_awaited()


class TestUpdateTaskStatus:
    """测试更新任务状态"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        return mock_session

    @pytest.fixture
    def mock_task(self):
        """模拟安装任务"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-123"
        task.status = "pending"
        task.progress = 0
        task.current_step = None
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.steps = [s.copy() for s in INSTALL_STEPS]

        async def mock_update(session, data):
            for key, value in data.items():
                setattr(task, key, value)

        task.update = mock_update
        return task

    @pytest.mark.asyncio
    async def test_update_task_status_to_running(self, session, mock_task):
        """测试更新任务状态为运行中"""
        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ):

            result = await InstallTaskService.update_task_status(
                session=session,
                task_id="task-123",
                status="running",
                progress=20,
                current_step="download",
            )

        assert result is not None
        assert result.status == "running"
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_update_task_status_to_completed(self, session, mock_task):
        """测试更新任务状态为完成"""
        mock_task.started_at = datetime.now() - timedelta(minutes=5)

        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ):

            result = await InstallTaskService.update_task_status(
                session=session,
                task_id="task-123",
                status="completed",
                progress=100,
                current_step="finalize",
            )

        assert result is not None
        assert result.status == "completed"
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_task_status_to_failed(self, session, mock_task):
        """测试更新任务状态为失败"""
        mock_task.started_at = datetime.now() - timedelta(minutes=2)

        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ):

            result = await InstallTaskService.update_task_status(
                session=session,
                task_id="task-123",
                status="failed",
                error_message="下载失败",
            )

        assert result is not None
        assert result.status == "failed"
        assert result.error_message == "下载失败"
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_task_status_not_found(self, session):
        """测试更新不存在的任务"""
        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=None
        ):

            result = await InstallTaskService.update_task_status(
                session=session,
                task_id="nonexistent-task",
                status="running",
            )

        assert result is None


class TestUpdateTaskStep:
    """测试更新任务步骤"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        return mock_session

    @pytest.fixture
    def mock_task(self):
        """模拟安装任务"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-123"
        task.steps = [
            {"step": "download", "name": "下载插件包", "status": "pending"},
            {"step": "validate", "name": "校验插件包", "status": "pending"},
            {"step": "install", "name": "安装插件", "status": "pending"},
            {"step": "configure", "name": "初始化配置", "status": "pending"},
            {"step": "finalize", "name": "完成安装", "status": "pending"},
        ]
        task.current_step = None

        async def mock_update(session, data):
            for key, value in data.items():
                setattr(task, key, value)

        task.update = mock_update
        return task

    @pytest.mark.asyncio
    async def test_update_task_step_success(self, session, mock_task):
        """测试成功更新任务步骤"""
        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ):

            result = await InstallTaskService.update_task_step(
                session=session,
                task_id="task-123",
                step_name="download",
                step_status="completed",
                progress=20,
            )

        assert result is not None
        assert result.current_step == "download"

        # 检查步骤状态已更新
        download_step = next(
            (s for s in result.steps if s["step"] == "download"), None
        )
        assert download_step is not None
        assert download_step["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_task_step_running(self, session, mock_task):
        """测试更新步骤状态为运行中"""
        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ):

            result = await InstallTaskService.update_task_step(
                session=session,
                task_id="task-123",
                step_name="validate",
                step_status="running",
                progress=35,
            )

        assert result is not None
        assert result.current_step == "validate"

    @pytest.mark.asyncio
    async def test_update_task_step_not_found(self, session):
        """测试更新不存在的任务步骤"""
        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=None
        ):

            result = await InstallTaskService.update_task_step(
                session=session,
                task_id="nonexistent-task",
                step_name="download",
                step_status="completed",
            )

        assert result is None


class TestGetTaskList:
    """测试获取任务列表"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        return mock_session

    def _create_mock_task(self, task_id: str, status: str = "pending"):
        """创建模拟任务"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = task_id
        task.plugin_id = "author/plugin"
        task.status = status
        task.progress = 50
        task.current_step = "install"
        task.created_at = datetime.now()
        task.started_at = datetime.now() if status in ("running", "completed") else None
        task.completed_at = datetime.now() if status == "completed" else None
        return task

    @pytest.mark.asyncio
    async def test_get_task_list_basic(self, session):
        """测试基本列表查询"""
        get_tenant_id = lambda: "tenant-123"

        count_result = MagicMock()
        count_result.scalar.return_value = 2

        tasks = [
            self._create_mock_task("task-1"),
            self._create_mock_task("task-2"),
        ]
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = tasks

        session.execute.side_effect = [count_result, list_result]

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            result = await InstallTaskService.get_task_list(session)

        assert isinstance(result, InstallTaskListResponse)
        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_get_task_list_with_status_filter(self, session):
        """测试带状态筛选的列表查询"""
        get_tenant_id = lambda: "tenant-123"

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        tasks = [self._create_mock_task("task-1", "running")]
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = tasks

        session.execute.side_effect = [count_result, list_result]

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            result = await InstallTaskService.get_task_list(
                session, status="running"
            )

        assert result.total == 1
        assert result.items[0].status == "running"

    @pytest.mark.asyncio
    async def test_get_task_list_with_plugin_id_filter(self, session):
        """测试带插件ID筛选的列表查询"""
        get_tenant_id = lambda: "tenant-123"

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        task = self._create_mock_task("task-1")
        task.plugin_id = "specific/plugin"
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [task]

        session.execute.side_effect = [count_result, list_result]

        with patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            result = await InstallTaskService.get_task_list(
                session, plugin_id="specific"
            )

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_task_list_no_tenant_id(self, session):
        """测试没有租户ID"""
        with patch(
            "ai.services.install_task_service.get_tenant_id", return_value=None
        ):
            with pytest.raises(ValueError) as exc_info:
                await InstallTaskService.get_task_list(session)

        assert "租户ID不能为空" in str(exc_info.value)


class TestGetTaskDetail:
    """测试获取任务详情"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_task(self):
        """模拟安装任务"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-123"
        task.tenant_id = "tenant-123"
        task.plugin_id = "author/plugin"
        task.status = "running"
        task.progress = 50
        task.current_step = "install"
        task.plugin_unique_identifier = "author/plugin:1.0.0@hash"
        task.steps = INSTALL_STEPS
        task.error_message = None
        task.created_at = datetime.now()
        task.started_at = datetime.now()
        task.completed_at = None
        return task

    @pytest.mark.asyncio
    async def test_get_task_detail_success(self, session, mock_task):
        """测试成功获取任务详情"""
        get_tenant_id = lambda: "tenant-123"

        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ), patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            result = await InstallTaskService.get_task_detail(session, "task-123")

        assert isinstance(result, InstallTaskDetailVo)
        assert result.id == "task-123"
        assert result.plugin_id == "author/plugin"
        assert result.status == "running"
        assert result.steps is not None

    @pytest.mark.asyncio
    async def test_get_task_detail_not_found(self, session):
        """测试获取不存在的任务详情"""
        get_tenant_id = lambda: "tenant-123"

        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=None
        ), patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            with pytest.raises(NotFoundError) as exc_info:
                await InstallTaskService.get_task_detail(session, "nonexistent-task")

        assert "任务不存在" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_get_task_detail_wrong_tenant(self, session, mock_task):
        """测试获取其他租户的任务详情"""
        get_tenant_id = lambda: "other-tenant"

        with patch.object(
            PluginInstallTask, "one_by_id", new_callable=AsyncMock, return_value=mock_task
        ), patch(
            "ai.services.install_task_service.get_tenant_id", side_effect=get_tenant_id
        ):
            with pytest.raises(NotFoundError) as exc_info:
                await InstallTaskService.get_task_detail(session, "task-123")

        assert "任务不存在" in str(exc_info.value.message)


class TestCheckTimeoutTasks:
    """测试检查超时任务"""

    @pytest.fixture
    def session(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()
        return mock_session

    def _create_running_task(self, task_id: str, started_minutes_ago: int):
        """创建运行中的任务"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = task_id
        task.status = "running"
        task.started_at = datetime.now() - timedelta(minutes=started_minutes_ago)
        task.error_message = None
        task.completed_at = None
        return task

    @pytest.mark.asyncio
    async def test_check_timeout_tasks_with_timeout(self, session):
        """测试检测到超时任务"""
        from framework.configs import get_settings

        # 创建一个 35 分钟前开始的任务（超过默认 30 分钟超时）
        timeout_task = self._create_running_task("task-timeout", 35)

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [timeout_task]
        session.execute.return_value = result_mock

        # 直接使用真实的 get_settings，它会从配置文件读取
        timeout_count = await InstallTaskService.check_timeout_tasks(session)

        assert timeout_count == 1
        assert timeout_task.status == "timeout"
        assert timeout_task.error_message == "安装任务超时"
        assert timeout_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_check_timeout_tasks_no_timeout(self, session):
        """测试没有超时任务"""
        # 创建一个 10 分钟前开始的任务
        running_task = self._create_running_task("task-running", 10)

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [running_task]
        session.execute.return_value = result_mock

        timeout_count = await InstallTaskService.check_timeout_tasks(session)

        assert timeout_count == 0
        assert running_task.status == "running"

    @pytest.mark.asyncio
    async def test_check_timeout_tasks_empty(self, session):
        """测试没有运行中的任务"""
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        timeout_count = await InstallTaskService.check_timeout_tasks(session)

        assert timeout_count == 0


class TestToTaskVo:
    """测试任务 VO 转换"""

    def test_to_task_vo(self):
        """测试转换为任务 VO"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-123"
        task.plugin_id = "author/plugin"
        task.status = "completed"
        task.progress = 100
        task.current_step = "finalize"
        task.created_at = datetime(2024, 1, 1, 12, 0, 0)
        task.started_at = datetime(2024, 1, 1, 12, 1, 0)
        task.completed_at = datetime(2024, 1, 1, 12, 5, 0)

        result = InstallTaskService._to_task_vo(task)

        assert result.id == "task-123"
        assert result.plugin_id == "author/plugin"
        assert result.status == "completed"
        assert result.progress == 100
        assert result.current_step == "finalize"
        assert result.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert result.started_at == datetime(2024, 1, 1, 12, 1, 0)
        assert result.completed_at == datetime(2024, 1, 1, 12, 5, 0)


class TestToTaskDetailVo:
    """测试任务详情 VO 转换"""

    def test_to_task_detail_vo(self):
        """测试转换为任务详情 VO"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-123"
        task.plugin_id = "author/plugin"
        task.status = "running"
        task.progress = 60
        task.current_step = "configure"
        task.plugin_unique_identifier = "author/plugin:1.0.0@hash"
        task.steps = INSTALL_STEPS
        task.error_message = None
        task.created_at = datetime(2024, 1, 1, 12, 0, 0)
        task.started_at = datetime(2024, 1, 1, 12, 1, 0)
        task.completed_at = None

        result = InstallTaskService._to_task_detail_vo(task)

        assert result.id == "task-123"
        assert result.plugin_unique_identifier == "author/plugin:1.0.0@hash"
        assert result.steps == INSTALL_STEPS
        assert result.error_message is None
        assert result.logs is None  # 日志功能后续实现

    def test_to_task_detail_vo_with_error(self):
        """测试转换带错误信息的任务详情 VO"""
        task = MagicMock(spec=PluginInstallTask)
        task.id = "task-failed"
        task.plugin_id = "author/plugin"
        task.status = "failed"
        task.progress = 30
        task.current_step = "validate"
        task.plugin_unique_identifier = "author/plugin:1.0.0@hash"
        task.steps = INSTALL_STEPS
        task.error_message = "校验失败：manifest 格式错误"
        task.created_at = datetime(2024, 1, 1, 12, 0, 0)
        task.started_at = datetime(2024, 1, 1, 12, 1, 0)
        task.completed_at = datetime(2024, 1, 1, 12, 2, 0)

        result = InstallTaskService._to_task_detail_vo(task)

        assert result.status == "failed"
        assert result.error_message == "校验失败：manifest 格式错误"


class TestInstallSteps:
    """测试安装步骤定义"""

    def test_install_steps_structure(self):
        """测试安装步骤结构"""
        assert len(INSTALL_STEPS) == 5

        step_names = [s["step"] for s in INSTALL_STEPS]
        assert step_names == [
            "download",
            "validate",
            "install",
            "configure",
            "finalize",
        ]

        # 每个步骤都应该有待执行状态
        for step in INSTALL_STEPS:
            assert "step" in step
            assert "name" in step
            assert "status" in step
            assert step["status"] == "pending"
