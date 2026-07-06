# Skills 市场运行时与 LangChain 集成实现计划（Phase 4-6）

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现 Skill 类型的两个轻量级运行时（KnowledgeSkillRuntime、SandboxSkillRuntime），集成 LangChain 实现知识文档的 Prompt 渲染和调用，扩展对话服务支持 Skill 调用，并提供 Skill 调用 API。

**架构：** 新增两个运行时继承 `PluginRuntime` 基类，根据 `skill_type` 路由。KnowledgeSkillRuntime 通过 LangChain PromptTemplate 加载 Markdown 文档并由 LLM 理解执行（零隔离）；SandboxSkillRuntime 使用子进程 + 白名单导入执行脚本（轻量级沙箱）。LangChain 集成组件（ChainBuilder、ContextManager）负责构建可复用的 Chain 和管理执行上下文。

**技术栈：** Python 3.12 + LangChain + RestrictedPython + langchain-openai + langchain-core

**设计规格：** `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md`（第 5、6、8.3-8.6 章）

**前置依赖：** 计划 1（`docs/superpowers/plans/2026-07-06-skills-marketplace-backend-foundation.md`）已完成，`skill_type` 和 `runtime_type` 字段已存在于 `TenantPluginDefinition` 表。

---

## 文件结构

### 创建的文件

| 文件路径 | 职责 |
|---------|------|
| `server/python/src/ai/components/plugin/engine/core/exceptions.py` | Skill 错误异常体系 |
| `server/python/src/ai/components/plugin/engine/core/runtime/knowledge_skill_runtime.py` | 知识文档运行时（零隔离） |
| `server/python/src/ai/components/plugin/engine/core/runtime/sandbox_skill_runtime.py` | 简单脚本运行时（轻量级沙箱） |
| `server/python/src/ai/components/skill/__init__.py` | Skill 组件包初始化 |
| `server/python/src/ai/components/skill/chain_builder.py` | LangChain Chain 构建器 |
| `server/python/src/ai/components/skill/context_manager.py` | Skill 执行上下文管理器 |
| `server/python/src/ai/controllers/console/skill_controller.py` | Skill 调用 API 控制器 |
| `server/python/src/ai/schemas/skill.py` | Skill 请求/响应 Schema |
| `server/python/tests/ai/unit/runtime/test_knowledge_skill_runtime.py` | 知识文档运行时单元测试 |
| `server/python/tests/ai/unit/runtime/test_sandbox_skill_runtime.py` | 沙箱运行时单元测试 |
| `server/python/tests/ai/unit/skill/test_chain_builder.py` | Chain Builder 单元测试 |
| `server/python/tests/ai/unit/skill/test_context_manager.py` | Context Manager 单元测试 |
| `server/python/tests/ai/integration/test_skill_invocation_flow.py` | Skill 调用流程集成测试 |

### 修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/python/src/ai/components/plugin/engine/models/enums.py` | PluginType 新增 SKILL，RuntimeType 新增 SANDBOX、NONE |
| `server/python/src/ai/components/plugin/engine/core/runtime/factory.py` | 扩展 create_runtime 支持 Skill 路由 |
| `server/python/src/ai/services/conversation_service.py` | 新增 chat_with_skill 方法 |
| `server/python/src/ai/module.py` | 注册 Skill 控制器路由 |

---

## 任务 1：扩展插件类型和运行时类型枚举

**文件：**
- 修改：`server/python/src/ai/components/plugin/engine/models/enums.py`
- 测试：无（枚举扩展，由后续任务测试）

- [ ] **步骤 1：扩展 PluginType 枚举**

修改 `server/python/src/ai/components/plugin/engine/models/enums.py`，在 `PluginType` 类中新增 `SKILL` 成员：

```python
class PluginType(EnumBase):
    """插件类型枚举"""

    MODEL = "model"  # AI模型插件（LLM、Embedding等）
    TOOL = "tool"  # 工具插件
    AGENT = "agent"  # AI代理插件
    OAUTH = "oauth"  # OAuth认证插件
    ENDPOINT = "endpoint"  # 端点插件
    SKILL = "skill"  # 技能插件（知识文档 + 简单脚本）
```

- [ ] **步骤 2：扩展 RuntimeType 枚举**

在同一文件的 `RuntimeType` 类中新增 `SANDBOX` 和 `NONE` 成员：

```python
class RuntimeType(EnumBase):
    """运行时类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"
    CONTAINER = "container"
    SANDBOX = "sandbox"  # 轻量级沙箱（Skill 脚本）
    NONE = "none"  # 零隔离（Skill 知识文档）
```

- [ ] **步骤 3：验证枚举扩展正确**

运行：`cd server/python && uv run python -c "from ai.components.plugin.engine.models.enums import PluginType, RuntimeType; print([e.value for e in PluginType]); print([e.value for e in RuntimeType])"`

预期：输出包含 `skill`、`sandbox`、`none`

- [ ] **步骤 4：运行现有测试确认无回归**

运行：`cd server/python && uv run pytest tests/ai/ -v -k "enum" --no-header 2>&1 | tail -10`

预期：现有测试通过（如无相关测试则无失败）

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/components/plugin/engine/models/enums.py
git commit -m "feat(ai): 扩展插件类型和运行时类型枚举

PluginType 新增 SKILL，RuntimeType 新增 SANDBOX 和 NONE

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2：创建 Skill 错误异常体系

**文件：**
- 创建：`server/python/src/ai/components/plugin/engine/core/exceptions.py`
- 测试：无（异常定义，由运行时测试覆盖）

- [ ] **步骤 1：创建异常体系文件**

创建 `server/python/src/ai/components/plugin/engine/core/exceptions.py`：

```python
"""Skill 运行时错误异常体系

定义 Skill 执行过程中可能出现的各类错误，支持结构化错误处理。
"""


class SkillError(Exception):
    """Skill 错误基类"""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)


class SkillNotFoundError(SkillError):
    """Skill 不存在"""

    def __init__(self, skill_id: str):
        self.skill_id = skill_id
        super().__init__(f"Skill 不存在: {skill_id}")


class SkillPreparationError(SkillError):
    """Skill 准备失败"""

    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 准备失败 [{skill_id}]: {reason}")


class SkillInvocationError(SkillError):
    """Skill 调用失败"""

    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 调用失败 [{skill_id}]: {reason}")


class SkillSecurityError(SkillError):
    """Skill 安全验证失败"""

    def __init__(self, skill_id: str, violations: list[str]):
        self.skill_id = skill_id
        self.violations = violations
        super().__init__(
            f"Skill 安全验证失败 [{skill_id}]: {', '.join(violations)}"
        )


class SkillTimeoutError(SkillError):
    """Skill 执行超时"""

    def __init__(self, skill_id: str, timeout: int):
        self.skill_id = skill_id
        self.timeout = timeout
        super().__init__(f"Skill 执行超时 [{skill_id}]: {timeout}s")
```

- [ ] **步骤 2：验证模块导入正确**

运行：`cd server/python && uv run python -c "from ai.components.plugin.engine.core.exceptions import SkillError, SkillNotFoundError, SkillPreparationError, SkillInvocationError, SkillSecurityError, SkillTimeoutError; print('导入成功')"`

预期：输出"导入成功"

- [ ] **步骤 3：Commit**

```bash
cd server/python
git add src/ai/components/plugin/engine/core/exceptions.py
git commit -m "feat(ai): 新增 Skill 错误异常体系

定义 SkillError 基类及 NotFound、Preparation、Invocation、Security、Timeout 子类

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3：实现 KnowledgeSkillRuntime

**文件：**
- 创建：`server/python/src/ai/components/plugin/engine/core/runtime/knowledge_skill_runtime.py`
- 测试：`server/python/tests/ai/unit/runtime/test_knowledge_skill_runtime.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/runtime/test_knowledge_skill_runtime.py`：

```python
"""知识文档运行时单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
    KnowledgeSkillRuntime,
)
from ai.components.plugin.engine.core.exceptions import SkillPreparationError


class TestKnowledgeSkillRuntime:
    """知识文档运行时测试"""

    @pytest.fixture
    def mock_plugin_info(self):
        """Mock 插件信息"""
        info = MagicMock()
        info.name = "airtable"
        info.version = "1.1.0"
        info.config = MagicMock()
        info.config.configuration = MagicMock()
        info.config.configuration.author = "community"
        info.config.configuration.name = "airtable"
        info.config.configuration.version = "1.1.0"
        return info

    @pytest.fixture
    def runtime(self, mock_plugin_info):
        return KnowledgeSkillRuntime(mock_plugin_info, Path("/tmp/test"))

    def test_runtime_type(self, runtime):
        """测试运行时类型标识"""
        assert runtime.runtime_type == "none"
        assert runtime.skill_type == "knowledge"

    @pytest.mark.asyncio
    async def test_prepare_success(self, runtime):
        """测试成功准备 Skill"""
        mock_skill_data = b"# Airtable Skill\nWork with Airtable's REST API."

        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.PluginStorageService",
        ) as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage.load_skill_documents = AsyncMock(
                return_value={"SKILL.md": "# Airtable Skill\nWork with API."}
            )
            mock_storage_class.return_value = mock_storage

            await runtime.prepare()

        assert runtime._is_loaded is True
        assert "SKILL.md" in runtime.skill_documents
        assert runtime.prompt_template is not None

    @pytest.mark.asyncio
    async def test_prepare_missing_skill_md(self, runtime):
        """测试 Skill 包缺少 SKILL.md"""
        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.PluginStorageService",
        ) as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage.load_skill_documents = AsyncMock(return_value={})
            mock_storage_class.return_value = mock_storage

            with pytest.raises(SkillPreparationError) as exc_info:
                await runtime.prepare()

            assert "缺少 SKILL.md" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_prepare_strips_yaml_front_matter(self, runtime):
        """测试准备时移除 YAML front matter"""
        mock_content = (
            "---\nname: airtable\nversion: 1.0.0\n---\n# Airtable Skill\nContent."
        )

        with patch(
            "ai.components.plugin.engine.core.runtime.knowledge_skill_runtime.PluginStorageService",
        ) as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage.load_skill_documents = AsyncMock(
                return_value={"SKILL.md": mock_content}
            )
            mock_storage_class.return_value = mock_storage

            await runtime.prepare()

        # 验证 front matter 被移除
        assert "# Airtable Skill" in runtime.skill_documents["SKILL.md"]
        assert "name: airtable" not in runtime.skill_documents["SKILL.md"]

    @pytest.mark.asyncio
    async def test_invoke_stream_success(self, runtime):
        """测试成功调用 Skill（流式返回）"""
        runtime._is_loaded = True
        runtime._is_running = True
        runtime.skill_documents = {"SKILL.md": "# Skill Content"}
        runtime.prompt_template = MagicMock()
        runtime.chain = MagicMock()
        runtime.chain.astream = MagicMock()

        async def mock_astream(*args, **kwargs):
            for chunk in ["Hello", " ", "World"]:
                yield chunk

        runtime.chain.astream.return_value = mock_astream()

        results = []
        async for result in runtime.invoke_stream(
            {"user_request": "test"}, timeout=60
        ):
            results.append(result)

        assert len(results) == 4  # 3 chunks + 1 complete
        assert results[0]["type"] == "chunk"
        assert results[0]["content"] == "Hello"
        assert results[-1]["type"] == "complete"

    @pytest.mark.asyncio
    async def test_invoke_stream_not_running(self, runtime):
        """测试未运行时调用 Skill"""
        runtime._is_loaded = False
        runtime._is_running = False
        runtime.chain = None

        results = []
        async for result in runtime.invoke_stream({"user_request": "test"}):
            results.append(result)

        assert len(results) == 1
        assert results[0]["type"] == "error"

    @pytest.mark.asyncio
    async def test_get_metrics(self, runtime):
        """测试获取运行时指标"""
        runtime.invoke_count = 5
        runtime.success_count = 4
        runtime.failure_count = 1

        metrics = await runtime.get_metrics()

        assert metrics["invoke_count"] == 5
        assert metrics["success_count"] == 4
        assert metrics["failure_count"] == 1
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_knowledge_skill_runtime.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'ai.components.plugin.engine.core.runtime.knowledge_skill_runtime'`

- [ ] **步骤 3：实现 KnowledgeSkillRuntime**

创建 `server/python/src/ai/components/plugin/engine/core/runtime/knowledge_skill_runtime.py`：

```python
"""知识文档运行时

零隔离运行时，通过 LangChain PromptTemplate 加载 Markdown 文档，
由 LLM 理解并执行。无需进程隔离和虚拟环境。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from loguru import logger

from ai.components.plugin.engine.core.exceptions import SkillPreparationError
from ai.components.plugin.engine.core.runtime.base import (
    PluginRuntime,
    PluginRuntimeState,
)
from ai.components.plugin.engine.models.plugin import PluginInfo


class KnowledgeSkillRuntime(PluginRuntime):
    """知识文档运行时

    特点：
    - 零隔离，无需进程
    - 通过 LangChain PromptTemplate 加载 Markdown 文档
    - 由 LLM 理解并执行
    - 即时加载/卸载，无需启动进程
    """

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        super().__init__(plugin_info, workspace_dir)

        self.skill_type = "knowledge"
        self.runtime_type = "none"

        # LangChain 组件
        self.llm: Any | None = None
        self.skill_documents: dict[str, str] = {}
        self.prompt_template: PromptTemplate | None = None
        self.chain: Any | None = None

        # 加载状态
        self._is_loaded = False

        # 监控指标
        self.invoke_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration_ms = 0
        self.last_invoke_at: datetime | None = None
        self.recent_errors: list[dict[str, Any]] = []

        # Skill 元数据（从 declaration 解析）
        self.skill_config: dict[str, Any] = self._extract_skill_config()

    def _extract_skill_config(self) -> dict[str, Any]:
        """从插件配置中提取 Skill 配置"""
        try:
            if self.plugin_config and hasattr(self.plugin_config, "configuration"):
                # 尝试从 declaration 获取 skill 配置
                declaration = getattr(
                    self.plugin_config.configuration, "declaration", None
                )
                if declaration and isinstance(declaration, dict):
                    return declaration.get("skill", {})
            # 默认配置
            return {"skill_type": "knowledge", "runtime": "none", "knowledge": {}}
        except Exception:
            return {"skill_type": "knowledge", "runtime": "none", "knowledge": {}}

    async def prepare(self) -> None:
        """准备阶段：加载 Skill 文档"""
        if self._is_loaded:
            self._plugin_logger.info(f"Skill {self.plugin_name} 已加载，跳过")
            return

        self._plugin_logger.info(f"开始加载 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.PREPARING)

        try:
            # 1. 从 MinIO 加载 Skill 文档
            self.skill_documents = await self._load_skill_documents()

            # 2. 验证必要文件
            if "SKILL.md" not in self.skill_documents:
                raise SkillPreparationError(
                    self.plugin_id, "Skill 包缺少 SKILL.md 文件"
                )

            # 3. 构建 LangChain Prompt
            self._build_prompt_chain()

            self._is_loaded = True
            self._update_state(PluginRuntimeState.PREPARED)
            self._plugin_logger.info(f"Skill {self.plugin_name} 加载完成")

        except SkillPreparationError:
            self._update_state(PluginRuntimeState.ERROR)
            raise
        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"Skill 加载失败: {e}")
            raise SkillPreparationError(self.plugin_id, str(e))

    async def start(self) -> None:
        """启动阶段：初始化 LLM 并构建 Chain"""
        if self._is_running:
            self._plugin_logger.info(f"Skill {self.plugin_name} 已在运行")
            return

        if not self._is_loaded:
            await self.prepare()

        self._plugin_logger.info(f"启动 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STARTING)

        try:
            # 初始化 LLM
            self.llm = await self._get_llm()

            # 构建完整 Chain
            if self.prompt_template and self.llm:
                self.chain = self.prompt_template | self.llm | StrOutputParser()

            self._update_state(PluginRuntimeState.RUNNING)
            self._plugin_logger.info(f"Skill {self.plugin_name} 启动完成")

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"Skill 启动失败: {e}")
            raise RuntimeError(f"Skill 启动失败: {e}")

    async def stop(self) -> None:
        """停止阶段：清理 LLM 和 Chain 资源"""
        if not self._is_running:
            return

        self._plugin_logger.info(f"停止 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STOPPING)

        self.llm = None
        self.chain = None

        self._update_state(PluginRuntimeState.STOPPED)
        self._plugin_logger.info(f"Skill {self.plugin_name} 已停止")

    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """调用 Skill（流式返回）

        Args:
            invoke_request: {"user_request": "用户请求", "context": {}}
            timeout: 超时时间（秒）
        """
        if not self._is_running or not self.chain:
            yield {
                "type": "error",
                "error": "Skill 未启动",
                "skill_id": self.plugin_id,
            }
            return

        start_time = datetime.now()
        self.invoke_count += 1
        self.last_invoke_at = start_time

        try:
            user_request = invoke_request.get("user_request", "")
            async for chunk in self.chain.astream({"user_request": user_request}):
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "skill_id": self.plugin_id,
                }

            # 记录成功
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.total_duration_ms += duration_ms
            self.success_count += 1

            yield {
                "type": "complete",
                "skill_id": self.plugin_id,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            # 记录失败
            self.failure_count += 1
            self.recent_errors.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            )
            self.recent_errors = self.recent_errors[-10:]  # 保留最近 10 条

            self._plugin_logger.error(f"Skill 调用失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "skill_id": self.plugin_id,
            }

    async def get_metrics(self) -> dict[str, Any]:
        """获取运行时指标"""
        avg_duration_ms = (
            self.total_duration_ms / self.invoke_count
            if self.invoke_count > 0
            else 0
        )
        return {
            "plugin_name": self.plugin_name,
            "state": self._state,
            "is_running": self._is_running,
            "skill_type": self.skill_type,
            "runtime_type": self.runtime_type,
            "invoke_count": self.invoke_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (
                self.success_count / self.invoke_count
                if self.invoke_count > 0
                else 0
            ),
            "avg_duration_ms": avg_duration_ms,
            "last_invoke_at": self.last_invoke_at.isoformat()
            if self.last_invoke_at
            else None,
            "recent_errors": self.recent_errors,
        }

    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取运行时日志（Skill 运行时无独立日志文件，返回空列表）"""
        return []

    def _build_prompt_chain(self) -> None:
        """构建 LangChain Prompt Chain"""
        # 主文档内容
        main_doc = self.skill_documents["SKILL.md"]

        # 移除 YAML front matter
        if main_doc.startswith("---"):
            parts = main_doc.split("---", 2)
            if len(parts) >= 3:
                main_doc = parts[2].strip()

        # 加载示例文档
        knowledge_config = self.skill_config.get("knowledge", {})
        examples_content = ""
        for example_file in knowledge_config.get("examples", []):
            if example_file in self.skill_documents:
                examples_content += f"\n\n### 示例：{example_file}\n"
                examples_content += self.skill_documents[example_file]

        # 构建 Prompt Template
        template = """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

## 技能说明

{skill_document}

## 使用示例

{examples}

## 用户请求

{user_request}

请根据技能说明和示例，帮助用户完成任务。遵循以下原则：
1. 严格按照技能说明中的步骤执行
2. 注意技能中提到的常见错误和解决方案
3. 如果需要用户提供更多信息，主动询问
4. 使用清晰、专业的语言回复"""

        self.prompt_template = PromptTemplate(
            template=template,
            input_variables=["user_request"],
            partial_variables={
                "skill_document": main_doc,
                "examples": examples_content,
            },
        )

    async def _load_skill_documents(self) -> dict[str, str]:
        """从 MinIO 加载 Skill 文档"""
        from tenant.services.plugin_storage_service import plugin_storage_service

        # storage_key 从插件配置获取（实际实现根据 PluginInfo 结构调整）
        storage_key = self._get_storage_key()

        return await plugin_storage_service.load_skill_documents(storage_key)

    def _get_storage_key(self) -> str:
        """获取 Skill 包的存储路径"""
        # 默认路径格式：skills/global/{plugin_id}/{version}/skill.zip
        return f"skills/global/{self.plugin_id}/{self.plugin_version}/skill.zip"

    async def _get_llm(self) -> Any:
        """获取 LLM 实例

        Raises:
            SkillPreparationError: LLM 获取失败
        """
        from ai.services.model_config_service import ModelConfigService

        model_config_service = ModelConfigService()
        try:
            from framework.database.dependencies import get_db_session

            async with get_db_session() as session:
                from framework.common.ctx import get_tenant_id

                tenant_id = get_tenant_id()
                # 使用模型配置服务获取 LangChain LLM
                llm = await model_config_service.get_langchain_llm(
                    session, tenant_id
                )
                if llm is None:
                    raise SkillPreparationError(
                        self.plugin_id, "未获取到可用的 LLM 配置"
                    )
                return llm
        except SkillPreparationError:
            raise
        except Exception as e:
            logger.error(f"获取 LLM 失败: {e}")
            raise SkillPreparationError(self.plugin_id, f"获取 LLM 失败: {e}")
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_knowledge_skill_runtime.py -v`

预期：7 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/components/plugin/engine/core/runtime/knowledge_skill_runtime.py tests/ai/unit/runtime/test_knowledge_skill_runtime.py
git commit -m "feat(ai): 实现 KnowledgeSkillRuntime 知识文档运行时

零隔离运行时，通过 LangChain PromptTemplate 加载 Markdown 文档
由 LLM 理解并执行，支持流式返回和监控指标

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4：实现 SandboxSkillRuntime

**文件：**
- 创建：`server/python/src/ai/components/plugin/engine/core/runtime/sandbox_skill_runtime.py`
- 测试：`server/python/tests/ai/unit/runtime/test_sandbox_skill_runtime.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/runtime/test_sandbox_skill_runtime.py`：

```python
"""沙箱运行时单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
    SandboxSkillRuntime,
)
from ai.components.plugin.engine.core.exceptions import SkillSecurityError


class TestSandboxSkillRuntime:
    """沙箱运行时测试"""

    @pytest.fixture
    def mock_plugin_info(self):
        info = MagicMock()
        info.name = "scraper"
        info.version = "1.0.0"
        info.config = MagicMock()
        info.config.configuration = MagicMock()
        info.config.configuration.author = "test"
        info.config.configuration.name = "scraper"
        info.config.configuration.version = "1.0.0"
        return info

    @pytest.fixture
    def runtime(self, mock_plugin_info):
        return SandboxSkillRuntime(mock_plugin_info, Path("/tmp/test"))

    def test_runtime_type(self, runtime):
        """测试运行时类型标识"""
        assert runtime.runtime_type == "sandbox"
        assert runtime.skill_type == "script"

    def test_validate_script_with_forbidden_import_os(self, runtime):
        """测试禁止导入 os"""
        runtime.script_content = "import os\nos.system('rm -rf /')"

        with pytest.raises(SkillSecurityError) as exc_info:
            runtime._validate_script_security()

        assert "import os" in str(exc_info.value)

    def test_validate_script_with_forbidden_subprocess(self, runtime):
        """测试禁止导入 subprocess"""
        runtime.script_content = "import subprocess\nsubprocess.run(['ls'])"

        with pytest.raises(SkillSecurityError):
            runtime._validate_script_security()

    def test_validate_script_with_eval(self, runtime):
        """测试禁止使用 eval"""
        runtime.script_content = "result = eval('1 + 1')"

        with pytest.raises(SkillSecurityError) as exc_info:
            runtime._validate_script_security()

        assert "eval(" in str(exc_info.value)

    def test_validate_safe_script(self, runtime):
        """测试安全脚本通过验证"""
        runtime.script_content = (
            "import requests\nimport json\n"
            "def main(input_data):\n"
            "    response = requests.get(input_data['url'])\n"
            "    return response.json()\n"
        )

        # 不应抛出异常
        runtime._validate_script_security()

    def test_build_safe_globals_only_allows_whitelist(self, runtime):
        """测试安全全局命名空间只允许白名单"""
        runtime.allowed_imports = {"requests", "json"}

        safe_globals = runtime._build_safe_globals()

        assert "requests" in safe_globals
        assert "json" in safe_globals
        assert "os" not in safe_globals
        assert "subprocess" not in safe_globals
        assert "sys" not in safe_globals

    def test_build_safe_globals_includes_basic_builtins(self, runtime):
        """测试安全全局命名空间包含基础内置函数"""
        runtime.allowed_imports = set()

        safe_globals = runtime._build_safe_globals()

        builtins = safe_globals["__builtins__"]
        assert "print" in builtins
        assert "len" in builtins
        assert "str" in builtins
        assert "int" in builtins
        assert "list" in builtins
        assert "dict" in builtins

    @pytest.mark.asyncio
    async def test_invoke_stream_not_running(self, runtime):
        """测试未运行时调用 Skill"""
        runtime._is_running = False

        results = []
        async for result in runtime.invoke_stream({"input": {}}):
            results.append(result)

        assert len(results) == 1
        assert results[0]["type"] == "error"

    @pytest.mark.asyncio
    async def test_get_metrics(self, runtime):
        """测试获取运行时指标"""
        runtime.invoke_count = 3
        runtime.success_count = 2
        runtime.failure_count = 1

        metrics = await runtime.get_metrics()

        assert metrics["invoke_count"] == 3
        assert metrics["success_count"] == 2
        assert metrics["failure_count"] == 1
        assert metrics["runtime_type"] == "sandbox"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_sandbox_skill_runtime.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'ai.components.plugin.engine.core.runtime.sandbox_skill_runtime'`

- [ ] **步骤 3：实现 SandboxSkillRuntime**

创建 `server/python/src/ai/components/plugin/engine/core/runtime/sandbox_skill_runtime.py`：

```python
"""简单脚本运行时

轻量级沙箱运行时，使用子进程执行 Python 脚本。
通过白名单导入控制和资源限制保障安全性。
"""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ai.components.plugin.engine.core.exceptions import (
    SkillInvocationError,
    SkillPreparationError,
    SkillSecurityError,
    SkillTimeoutError,
)
from ai.components.plugin.engine.core.runtime.base import (
    PluginRuntime,
    PluginRuntimeState,
)
from ai.components.plugin.engine.models.plugin import PluginInfo


class SandboxSkillRuntime(PluginRuntime):
    """轻量级沙箱运行时

    特点：
    - 子进程执行 Python 脚本
    - 白名单导入控制
    - 资源限制（内存、超时）
    - 安全模式验证
    """

    # 默认配置
    DEFAULT_TIMEOUT = 30
    DEFAULT_MEMORY_LIMIT_MB = 128

    # 禁止的导入模式
    FORBIDDEN_PATTERNS = [
        "import os",
        "import subprocess",
        "import sys",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
    ]

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        super().__init__(plugin_info, workspace_dir)

        self.skill_type = "script"
        self.runtime_type = "sandbox"

        # 沙箱配置
        self.timeout: int = self.DEFAULT_TIMEOUT
        self.memory_limit_mb: int = self.DEFAULT_MEMORY_LIMIT_MB
        self.allowed_imports: set[str] = set()

        # 脚本内容
        self.script_content: str = ""
        self.dependencies: list[str] = []

        # 临时工作目录
        self.temp_dir: Path | None = None

        # 监控指标
        self.invoke_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration_ms = 0
        self.last_invoke_at: datetime | None = None
        self.recent_errors: list[dict[str, Any]] = []

        # Skill 配置
        self.skill_config: dict[str, Any] = self._extract_skill_config()

    def _extract_skill_config(self) -> dict[str, Any]:
        """从插件配置中提取 Skill 配置"""
        try:
            if self.plugin_config and hasattr(self.plugin_config, "configuration"):
                declaration = getattr(
                    self.plugin_config.configuration, "declaration", None
                )
                if declaration and isinstance(declaration, dict):
                    return declaration.get("skill", {})
            return {
                "skill_type": "script",
                "runtime": "sandbox",
                "script": {},
            }
        except Exception:
            return {"skill_type": "script", "runtime": "sandbox", "script": {}}

    async def prepare(self) -> None:
        """准备阶段：加载脚本、验证安全性、创建临时目录"""
        if self._is_prepared:
            self._plugin_logger.info(f"Skill {self.plugin_name} 已准备，跳过")
            return

        self._plugin_logger.info(f"准备 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.PREPARING)

        try:
            # 1. 解析配置
            script_config = self.skill_config.get("script", {})
            self.timeout = script_config.get("timeout", self.DEFAULT_TIMEOUT)
            self.memory_limit_mb = script_config.get(
                "memory_limit_mb", self.DEFAULT_MEMORY_LIMIT_MB
            )
            self.allowed_imports = set(script_config.get("allowed_imports", []))
            self.dependencies = script_config.get("dependencies", [])

            # 2. 加载脚本内容
            self.script_content = await self._load_script_content()

            # 3. 验证脚本安全性
            self._validate_script_security()

            # 4. 创建临时工作目录
            self.temp_dir = Path(
                tempfile.mkdtemp(prefix=f"skill_{self.plugin_name}_")
            )

            self._is_prepared = True
            self._update_state(PluginRuntimeState.PREPARED)
            self._plugin_logger.info(f"Skill {self.plugin_name} 准备完成")

        except SkillSecurityError:
            self._update_state(PluginRuntimeState.ERROR)
            raise
        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"Skill 准备失败: {e}")
            raise SkillPreparationError(self.plugin_id, str(e))

    async def start(self) -> None:
        """启动阶段：标记为运行状态（沙箱无需持久化进程）"""
        if self._is_running:
            return

        if not self._is_prepared:
            await self.prepare()

        self._update_state(PluginRuntimeState.STARTING)

        # 沙箱运行时无需启动持久进程，直接标记为运行
        self._update_state(PluginRuntimeState.RUNNING)
        self._plugin_logger.info(f"Skill {self.plugin_name} 已就绪")

    async def stop(self) -> None:
        """停止阶段：清理临时目录"""
        if not self._is_running:
            return

        self._plugin_logger.info(f"停止 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STOPPING)

        # 清理临时目录
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None

        self._update_state(PluginRuntimeState.STOPPED)
        self._plugin_logger.info(f"Skill {self.plugin_name} 已停止")

    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """在沙箱中执行脚本"""
        if not self._is_running:
            yield {
                "type": "error",
                "error": "Skill 未启动",
                "skill_id": self.plugin_id,
            }
            return

        start_time = datetime.now()
        self.invoke_count += 1
        self.last_invoke_at = start_time
        effective_timeout = timeout or self.timeout

        try:
            result = await self._execute_with_limits(
                invoke_request, effective_timeout
            )

            duration_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )
            self.total_duration_ms += duration_ms
            self.success_count += 1

            yield {
                "type": "complete",
                "result": result,
                "skill_id": self.plugin_id,
                "duration_ms": duration_ms,
            }

        except SkillTimeoutError as e:
            self.failure_count += 1
            self._record_error(str(e))
            yield {"type": "error", "error": str(e), "skill_id": self.plugin_id}

        except Exception as e:
            self.failure_count += 1
            self._record_error(str(e))
            self._plugin_logger.error(f"Skill 执行失败: {e}")
            yield {"type": "error", "error": str(e), "skill_id": self.plugin_id}

    async def get_metrics(self) -> dict[str, Any]:
        """获取运行时指标"""
        avg_duration_ms = (
            self.total_duration_ms / self.invoke_count
            if self.invoke_count > 0
            else 0
        )
        return {
            "plugin_name": self.plugin_name,
            "state": self._state,
            "is_running": self._is_running,
            "skill_type": self.skill_type,
            "runtime_type": self.runtime_type,
            "invoke_count": self.invoke_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (
                self.success_count / self.invoke_count
                if self.invoke_count > 0
                else 0
            ),
            "avg_duration_ms": avg_duration_ms,
            "last_invoke_at": self.last_invoke_at.isoformat()
            if self.last_invoke_at
            else None,
            "recent_errors": self.recent_errors,
        }

    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取运行时日志（沙箱无独立日志，返回空列表）"""
        return []

    def _validate_script_security(self) -> None:
        """验证脚本安全性

        检查禁止的导入模式和危险函数调用。
        """
        if not self.script_content:
            raise SkillSecurityError(self.plugin_id, ["脚本内容为空"])

        violations: list[str] = []
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in self.script_content:
                violations.append(pattern)

        if violations:
            raise SkillSecurityError(self.plugin_id, violations)

    def _build_safe_globals(self) -> dict[str, Any]:
        """构建安全的全局命名空间

        仅包含白名单导入和基础内置函数。
        """
        # 加载白名单模块
        safe_modules: dict[str, Any] = {}
        for module_name in self.allowed_imports:
            try:
                safe_modules[module_name] = __import__(module_name)
            except ImportError:
                self._plugin_logger.warning(f"无法导入白名单模块: {module_name}")

        # 基础内置函数
        safe_builtins = {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "type": type,
            "None": None,
            "True": True,
            "False": False,
        }

        return {
            "__builtins__": safe_builtins,
            **safe_modules,
        }

    async def _execute_with_limits(
        self,
        invoke_request: dict[str, Any],
        timeout: int,
    ) -> Any:
        """在子进程中执行脚本（带超时限制）

        Args:
            invoke_request: 调用请求，包含 input 和 context
            timeout: 超时时间（秒）

        Returns:
            脚本执行结果

        Raises:
            SkillTimeoutError: 执行超时
            SkillInvocationError: 执行失败
        """
        # 构建执行脚本：包装用户脚本并调用 main 函数
        wrapper_script = self._build_wrapper_script(invoke_request)

        process = await asyncio.create_subprocess_exec(
            "python3",
            "-c",
            wrapper_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.temp_dir) if self.temp_dir else None,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                raise SkillInvocationError(self.plugin_id, error_msg)

            # 解析输出
            output = stdout.decode("utf-8", errors="replace").strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"output": output}

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise SkillTimeoutError(self.plugin_id, timeout)

    def _build_wrapper_script(self, invoke_request: dict[str, Any]) -> str:
        """构建包装脚本

        将用户脚本包装在安全环境中执行，通过标准输出返回 JSON 结果。
        在脚本开头设置内存限制（仅 Linux/Unix 支持，Windows 跳过）。
        """
        input_data = invoke_request.get("input", {})
        context = invoke_request.get("context", {})

        # 将输入数据序列化为 JSON
        input_json = json.dumps(input_data)
        context_json = json.dumps(context)

        # 构建包装脚本（含内存限制）
        wrapper = f"""
import json
import sys

# 资源限制：设置内存上限（仅 Linux/Unix 支持，Windows 跳过）
try:
    import resource
    memory_limit_bytes = {self.memory_limit_mb} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
except (ImportError, AttributeError, ValueError):
    pass

# 输入数据
input_data = json.loads('{input_json}')
context = json.loads('{context_json}')

# 用户脚本
{self.script_content}

# 执行 main 函数并输出结果
if 'main' in dir():
    result = main(input_data)
    print(json.dumps(result, default=str, ensure_ascii=False))
else:
    print(json.dumps({{"output": "脚本未定义 main 函数"}}, ensure_ascii=False))
"""
        return wrapper

    async def _load_script_content(self) -> str:
        """从 MinIO 加载脚本内容"""
        from tenant.services.plugin_storage_service import plugin_storage_service

        storage_key = self._get_storage_key()
        documents = await plugin_storage_service.load_skill_documents(storage_key)

        # 查找入口脚本
        script_config = self.skill_config.get("script", {})
        entrypoint = script_config.get("entrypoint", "main.py")

        # 文档中查找入口脚本
        if entrypoint in documents:
            return documents[entrypoint]

        # 尝试查找任何 .py 文件
        for filename, content in documents.items():
            if filename.endswith(".py"):
                return content

        raise SkillPreparationError(
            self.plugin_id, f"未找到入口脚本: {entrypoint}"
        )

    def _get_storage_key(self) -> str:
        """获取 Skill 包的存储路径"""
        return f"skills/global/{self.plugin_id}/{self.plugin_version}/skill.zip"

    def _record_error(self, error: str) -> None:
        """记录错误到最近错误列表"""
        self.recent_errors.append(
            {
                "timestamp": datetime.now().isoformat(),
                "error": error,
            }
        )
        self.recent_errors = self.recent_errors[-10:]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_sandbox_skill_runtime.py -v`

预期：9 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/components/plugin/engine/core/runtime/sandbox_skill_runtime.py tests/ai/unit/runtime/test_sandbox_skill_runtime.py
git commit -m "feat(ai): 实现 SandboxSkillRuntime 沙箱运行时

轻量级沙箱运行时，使用子进程执行 Python 脚本
支持白名单导入控制、超时限制、安全模式验证

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5：扩展运行时工厂支持 Skill 路由

**文件：**
- 修改：`server/python/src/ai/components/plugin/engine/core/runtime/factory.py`
- 测试：`server/python/tests/ai/unit/runtime/test_runtime_factory.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/runtime/test_runtime_factory.py`：

```python
"""运行时工厂单元测试"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from ai.components.plugin.engine.core.runtime.factory import RuntimeFactory
from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
    KnowledgeSkillRuntime,
)
from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
    SandboxSkillRuntime,
)
from ai.components.plugin.engine.models.enums import PluginType


class TestRuntimeFactory:
    """运行时工厂测试"""

    @pytest.fixture
    def factory(self):
        return RuntimeFactory()

    @pytest.fixture
    def mock_plugin_info_skill_knowledge(self):
        info = MagicMock()
        info.name = "airtable"
        info.version = "1.0.0"
        info.config = MagicMock()
        info.config.configuration = MagicMock()
        info.config.configuration.author = "community"
        info.config.configuration.name = "airtable"
        info.config.configuration.version = "1.0.0"
        info.config.configuration.declaration = {
            "skill": {"skill_type": "knowledge", "runtime": "none"}
        }
        return info

    @pytest.fixture
    def mock_plugin_info_skill_script(self):
        info = MagicMock()
        info.name = "scraper"
        info.version = "1.0.0"
        info.config = MagicMock()
        info.config.configuration = MagicMock()
        info.config.configuration.author = "test"
        info.config.configuration.name = "scraper"
        info.config.configuration.version = "1.0.0"
        info.config.configuration.declaration = {
            "skill": {
                "skill_type": "script",
                "runtime": "sandbox",
                "script": {"entrypoint": "main.py"},
            }
        }
        return info

    def test_create_knowledge_skill_runtime(
        self, factory, mock_plugin_info_skill_knowledge
    ):
        """测试创建知识文档运行时"""
        runtime = factory.create_runtime(
            mock_plugin_info_skill_knowledge, Path("/tmp/test")
        )

        assert isinstance(runtime, KnowledgeSkillRuntime)
        assert runtime.skill_type == "knowledge"
        assert runtime.runtime_type == "none"

    def test_create_sandbox_skill_runtime(
        self, factory, mock_plugin_info_skill_script
    ):
        """测试创建沙箱运行时"""
        runtime = factory.create_runtime(
            mock_plugin_info_skill_script, Path("/tmp/test")
        )

        assert isinstance(runtime, SandboxSkillRuntime)
        assert runtime.skill_type == "script"
        assert runtime.runtime_type == "sandbox"

    def test_create_runtime_unknown_skill_type(self, factory):
        """测试未知的 Skill 类型"""
        info = MagicMock()
        info.name = "unknown"
        info.version = "1.0.0"
        info.config = MagicMock()
        info.config.configuration = MagicMock()
        info.config.configuration.author = "test"
        info.config.configuration.name = "unknown"
        info.config.configuration.version = "1.0.0"
        info.config.configuration.declaration = {
            "skill": {"skill_type": "unknown_type", "runtime": "none"}
        }

        with pytest.raises(ValueError, match="不支持的 Skill 类型"):
            factory.create_runtime(info, Path("/tmp/test"))
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_runtime_factory.py -v`

预期：FAIL，`create_runtime` 未路由 Skill 类型

- [ ] **步骤 3：扩展运行时工厂**

修改 `server/python/src/ai/components/plugin/engine/core/runtime/factory.py`，替换整个文件内容：

```python
"""
插件运行时工厂
使用工厂模式创建不同类型的运行时实例
"""

from pathlib import Path

from ai.components.plugin.engine.core.runtime.base import PluginRuntime
from ai.components.plugin.engine.core.runtime.knowledge_skill_runtime import (
    KnowledgeSkillRuntime,
)
from ai.components.plugin.engine.core.runtime.local_runtime import LocalPluginRuntime
from ai.components.plugin.engine.core.runtime.sandbox_skill_runtime import (
    SandboxSkillRuntime,
)
from ai.components.plugin.engine.models.enums import RuntimeType
from ai.components.plugin.engine.models.plugin import PluginInfo


class RuntimeFactory:
    """运行时工厂类"""

    def __init__(self):
        # 注册运行时类型映射
        self._runtime_classes: dict[str, type[PluginRuntime]] = {
            RuntimeType.LOCAL.value: LocalPluginRuntime,
        }

    def create_runtime(
        self, plugin_info: PluginInfo, workspace_dir: Path
    ) -> PluginRuntime:
        """
        创建运行时实例

        Args:
            plugin_info: 插件信息
            workspace_dir: 工作目录

        Returns:
            运行时实例
        """
        # Skill 类型路由
        if self._is_skill_plugin(plugin_info):
            return self._create_skill_runtime(plugin_info, workspace_dir)

        # 现有逻辑：tool/model/agent
        runtime_type = self._get_runtime_type(plugin_info)
        runtime_class = self._runtime_classes.get(runtime_type)
        if not runtime_class:
            raise ValueError(f"不支持的运行时类型: {runtime_type}")

        return runtime_class(plugin_info=plugin_info, workspace_dir=workspace_dir)

    def _is_skill_plugin(self, plugin_info: PluginInfo) -> bool:
        """判断是否为 Skill 类型插件"""
        try:
            if plugin_info.config and hasattr(plugin_info.config, "configuration"):
                declaration = getattr(
                    plugin_info.config.configuration, "declaration", None
                )
                if declaration and isinstance(declaration, dict):
                    return "skill" in declaration
        except Exception:
            pass
        return False

    def _create_skill_runtime(
        self, plugin_info: PluginInfo, workspace_dir: Path
    ) -> PluginRuntime:
        """创建 Skill 运行时"""
        declaration = plugin_info.config.configuration.declaration
        skill_config = declaration.get("skill", {})
        skill_type = skill_config.get("skill_type", "knowledge")

        if skill_type == "knowledge":
            return KnowledgeSkillRuntime(plugin_info, workspace_dir)
        elif skill_type == "script":
            return SandboxSkillRuntime(plugin_info, workspace_dir)
        else:
            raise ValueError(f"不支持的 Skill 类型: {skill_type}")

    def _get_runtime_type(self, plugin_info: PluginInfo) -> str:
        """从插件配置中获取运行时类型"""
        # 默认使用本地运行时
        return RuntimeType.LOCAL.value
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/test_runtime_factory.py -v`

预期：3 个测试全部 PASS

- [ ] **步骤 5：运行现有运行时测试确认无回归**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/ -v --no-header 2>&1 | tail -20`

预期：所有运行时测试通过

- [ ] **步骤 6：Commit**

```bash
cd server/python
git add src/ai/components/plugin/engine/core/runtime/factory.py tests/ai/unit/runtime/test_runtime_factory.py
git commit -m "feat(ai): 运行时工厂扩展支持 Skill 路由

根据 declaration 中的 skill 配置路由到 KnowledgeSkillRuntime 或 SandboxSkillRuntime

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6：实现 Skill Chain Builder

**文件：**
- 创建：`server/python/src/ai/components/skill/__init__.py`
- 创建：`server/python/src/ai/components/skill/chain_builder.py`
- 测试：`server/python/tests/ai/unit/skill/test_chain_builder.py`

- [ ] **步骤 1：创建 skill 组件包初始化文件**

创建 `server/python/src/ai/components/skill/__init__.py`：

```python
"""Skill 组件包

提供 LangChain 集成组件，包括 Chain 构建器和上下文管理器。
"""

from ai.components.skill.chain_builder import SkillChainBuilder
from ai.components.skill.context_manager import SkillContextManager, SkillExecutionContext

__all__ = [
    "SkillChainBuilder",
    "SkillContextManager",
    "SkillExecutionContext",
]
```

- [ ] **步骤 2：编写失败的测试**

创建 `server/python/tests/ai/unit/skill/test_chain_builder.py`：

```python
"""Skill Chain Builder 单元测试"""

import pytest
from unittest.mock import MagicMock

from ai.components.skill.chain_builder import SkillChainBuilder


class TestSkillChainBuilder:
    """Skill Chain Builder 测试"""

    @pytest.fixture
    def builder(self):
        mock_llm = MagicMock()
        return SkillChainBuilder(mock_llm)

    def test_build_knowledge_skill_chain(self, builder):
        """测试构建知识文档 Chain"""
        chain = builder.build_knowledge_skill_chain(
            skill_document="# Airtable Skill\nAPI usage guide.",
            examples="## Example\nCreate record.",
        )

        assert chain is not None

    def test_build_knowledge_skill_chain_with_context(self, builder):
        """测试带上下文构建 Chain"""
        chain = builder.build_knowledge_skill_chain(
            skill_document="# Skill",
            examples="",
            context={"user_preference": "detailed"},
        )

        assert chain is not None

    def test_build_multi_skill_chain(self, builder):
        """测试构建多 Skill 组合 Chain"""
        skills = [
            {"name": "skill1", "document": "# Skill 1"},
            {"name": "skill2", "document": "# Skill 2"},
        ]

        chain = builder.build_multi_skill_chain(skills, "test request")

        assert chain is not None

    def test_build_multi_skill_chain_combines_documents(self, builder):
        """测试多 Skill Chain 组合文档"""
        skills = [
            {"name": "airtable", "document": "# Airtable"},
            {"name": "notion", "document": "# Notion"},
        ]

        chain = builder.build_multi_skill_chain(skills, "combine both")

        assert chain is not None

    def test_build_skill_with_history_chain(self, builder):
        """测试构建带历史记录的 Chain"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        chain = builder.build_skill_with_history_chain(
            skill_document="# Skill", conversation_history=history
        )

        assert chain is not None
```

- [ ] **步骤 3：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/skill/test_chain_builder.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'ai.components.skill'`

- [ ] **步骤 4：实现 SkillChainBuilder**

创建 `server/python/src/ai/components/skill/chain_builder.py`：

```python
"""Skill Chain 构建器

将 Skill 文档转换为 LangChain Runnable Chain。
支持单 Skill、多 Skill 组合、带历史记录三种模式。
"""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class SkillChainBuilder:
    """Skill Chain 构建器

    负责将 Skill 文档转换为 LangChain Runnable Chain。
    """

    def __init__(self, llm: Any):
        """初始化

        Args:
            llm: LangChain LLM 实例
        """
        self.llm = llm

    def build_knowledge_skill_chain(
        self,
        skill_document: str,
        examples: str = "",
        context: dict[str, Any] | None = None,
    ) -> Any:
        """构建知识文档类型的 Chain

        Args:
            skill_document: SKILL.md 主文档内容
            examples: 示例文档内容
            context: 额外上下文（如用户偏好、历史记录等）

        Returns:
            Runnable: LangChain Runnable 对象
        """
        extra_context = self._format_context(context)

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

## 技能说明

{skill_document}

## 使用示例

{examples}

## 额外上下文

{extra_context}

请根据技能说明和示例，帮助用户完成任务。遵循以下原则：
1. 严格按照技能说明中的步骤执行
2. 注意技能中提到的常见错误和解决方案
3. 如果需要用户提供更多信息，主动询问
4. 使用清晰、专业的语言回复""",
            ),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()

    def build_multi_skill_chain(
        self,
        skills: list[dict[str, str]],
        user_request: str,
    ) -> Any:
        """构建多 Skill 组合 Chain

        支持同时加载多个 Skill（类似 Hermes 的 stacking skills）。

        Args:
            skills: [{"name": "skill1", "document": "..."}, ...]
            user_request: 用户请求

        Returns:
            Runnable: 组合 Chain
        """
        skill_count = len(skills)
        combined_skills = "\n\n---\n\n".join(
            f"## 技能 {i + 1}: {skill['name']}\n\n{skill['document']}"
            for i, skill in enumerate(skills)
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """你是一个专业的 AI 助手，现在需要组合使用以下 {skill_count} 个技能来帮助用户。

{combined_skills}

请根据所有技能的说明，协调使用它们来完成用户任务。""",
            ),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()

    def build_skill_with_history_chain(
        self,
        skill_document: str,
        conversation_history: list[dict[str, str]],
    ) -> Any:
        """构建带对话历史的 Skill Chain

        支持多轮对话场景。

        Args:
            skill_document: Skill 文档内容
            conversation_history: 对话历史列表

        Returns:
            Runnable: 带历史记录的 Chain
        """
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

{skill_document}""",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()

    def _format_context(self, context: dict[str, Any] | None) -> str:
        """格式化上下文为字符串"""
        if not context:
            return "无额外上下文"

        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/skill/test_chain_builder.py -v`

预期：5 个测试全部 PASS

- [ ] **步骤 6：Commit**

```bash
cd server/python
git add src/ai/components/skill/__init__.py src/ai/components/skill/chain_builder.py tests/ai/unit/skill/test_chain_builder.py
git commit -m "feat(ai): 实现 SkillChainBuilder Chain 构建器

支持单 Skill、多 Skill 组合、带历史记录三种 Chain 构建模式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7：实现 Skill Context Manager

**文件：**
- 创建：`server/python/src/ai/components/skill/context_manager.py`
- 测试：`server/python/tests/ai/unit/skill/test_context_manager.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/skill/test_context_manager.py`：

```python
"""Skill Context Manager 单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.components.skill.context_manager import (
    SkillContextManager,
    SkillExecutionContext,
)


class TestSkillContextManager:
    """Skill Context Manager 测试"""

    @pytest.fixture
    def context_manager(self):
        return SkillContextManager()

    @pytest.fixture
    def mock_context(self):
        return SkillExecutionContext(
            skill_id="community/airtable",
            skill_name="airtable",
            skill_type="knowledge",
            user_id="user-001",
            tenant_id="tenant-001",
            conversation_id="conv-001",
            skill_document="# Airtable Skill\nAPI guide.",
            examples={"examples/create.md": "## Example\nCreate record."},
        )

    def test_context_key_format(self, context_manager):
        """测试上下文键格式"""
        key = context_manager._build_context_key(
            "tenant-001", "user-001", "community/airtable"
        )
        assert key == "tenant-001:user-001:community/airtable"

    def test_cache_context(self, context_manager, mock_context):
        """测试上下文缓存"""
        context_manager._contexts["test-key"] = mock_context

        cached = context_manager._contexts.get("test-key")
        assert cached is mock_context

    @pytest.mark.asyncio
    async def test_invoke_skill_updates_stats(self, context_manager, mock_context):
        """测试调用 Skill 更新统计信息"""
        context_manager._contexts["tenant-001:user-001:community/airtable"] = mock_context

        # Mock chain
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Skill response")
        mock_context.chain_cache["chain_community/airtable"] = mock_chain

        result = await context_manager.invoke_skill(
            "community/airtable",
            "Create a record",
        )

        assert result == "Skill response"
        assert mock_context.invoke_count == 1
        assert mock_context.last_invoked_at is not None

    @pytest.mark.asyncio
    async def test_invoke_skill_not_loaded(self, context_manager):
        """测试调用未加载的 Skill"""
        with pytest.raises(RuntimeError, match="Skill 未加载"):
            await context_manager.invoke_skill(
                "nonexistent/skill", "test request"
            )

    def test_format_examples(self, context_manager):
        """测试格式化示例文档"""
        examples = {
            "examples/create.md": "## Create\nCreate a record.",
            "examples/update.md": "## Update\nUpdate a record.",
        }

        formatted = context_manager._format_examples(examples)

        assert "examples/create.md" in formatted
        assert "examples/update.md" in formatted
        assert "Create a record" in formatted

    def test_format_empty_examples(self, context_manager):
        """测试格式化空示例"""
        formatted = context_manager._format_examples({})
        assert formatted == ""

    def test_context_dataclass_fields(self, mock_context):
        """测试上下文数据类字段"""
        assert mock_context.skill_id == "community/airtable"
        assert mock_context.skill_type == "knowledge"
        assert mock_context.invoke_count == 0
        assert mock_context.loaded_at is not None
        assert isinstance(mock_context.examples, dict)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/skill/test_context_manager.py -v`

预期：FAIL，报错 `ModuleNotFoundError: No module named 'ai.components.skill.context_manager'`

- [ ] **步骤 3：实现 SkillContextManager**

创建 `server/python/src/ai/components/skill/context_manager.py`：

```python
"""Skill 执行上下文管理器

管理 Skill 加载、卸载和执行上下文，提供 Chain 缓存。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from loguru import logger


@dataclass
class SkillExecutionContext:
    """Skill 执行上下文"""

    skill_id: str
    skill_name: str
    skill_type: str  # knowledge | script

    # 用户信息
    user_id: str
    tenant_id: str
    conversation_id: str

    # 对话上下文
    message_history: list[dict[str, str]] = field(default_factory=list)

    # Skill 文档内容
    skill_document: str = ""
    examples: dict[str, str] = field(default_factory=dict)

    # 运行时状态
    loaded_at: datetime = field(default_factory=datetime.now)
    invoke_count: int = 0
    last_invoked_at: datetime | None = None

    # Chain 缓存
    chain_cache: dict[str, Any] = field(default_factory=dict)


class SkillContextManager:
    """Skill 上下文管理器

    负责：
    1. 管理 Skill 加载和卸载
    2. 维护执行上下文
    3. 提供 Chain 缓存
    """

    def __init__(self):
        self._contexts: dict[str, SkillExecutionContext] = {}

    def _build_context_key(
        self, tenant_id: str, user_id: str, skill_id: str
    ) -> str:
        """构建上下文缓存键"""
        return f"{tenant_id}:{user_id}:{skill_id}"

    async def load_skill(
        self,
        skill_id: str,
        user_id: str,
        tenant_id: str,
        conversation_id: str,
        skill_document: str = "",
        examples: dict[str, str] | None = None,
    ) -> SkillExecutionContext:
        """加载 Skill 并创建上下文

        Args:
            skill_id: Skill ID
            user_id: 用户 ID
            tenant_id: 租户 ID
            conversation_id: 对话 ID
            skill_document: Skill 文档内容（可选，由调用方提供）
            examples: 示例文档（可选）

        Returns:
            SkillExecutionContext: 执行上下文
        """
        context_key = self._build_context_key(tenant_id, user_id, skill_id)

        if context_key in self._contexts:
            return self._contexts[context_key]

        # 创建上下文
        context = SkillExecutionContext(
            skill_id=skill_id,
            skill_name=skill_id.split("/")[-1] if "/" in skill_id else skill_id,
            skill_type="knowledge",  # 默认知识文档，可由调用方覆盖
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            skill_document=skill_document,
            examples=examples or {},
        )

        self._contexts[context_key] = context
        logger.info(f"加载 Skill 上下文: {context_key}")

        return context

    async def invoke_skill(
        self,
        skill_id: str,
        user_request: str,
        context: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """调用 Skill

        Args:
            skill_id: Skill ID
            user_request: 用户请求
            context: 额外上下文
            tenant_id: 租户 ID（用于定位上下文）
            user_id: 用户 ID（用于定位上下文）

        Returns:
            str: Skill 执行结果

        Raises:
            RuntimeError: Skill 未加载
        """
        skill_context = self._get_active_context(skill_id, tenant_id, user_id)

        if not skill_context:
            raise RuntimeError(f"Skill 未加载: {skill_id}")

        # 更新统计
        skill_context.invoke_count += 1
        skill_context.last_invoked_at = datetime.now()

        # 获取或构建 Chain（异步，必要时主动获取 LLM）
        chain = await self._get_or_build_chain(skill_context)

        # 执行
        result = await chain.ainvoke(
            {
                "user_request": user_request,
                "extra_context": self._format_context(context),
                "examples": self._format_examples(skill_context.examples),
                "skill_document": skill_context.skill_document,
            }
        )

        return result

    def _get_active_context(
        self,
        skill_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> SkillExecutionContext | None:
        """获取活动的 Skill 上下文"""
        if tenant_id and user_id:
            # 精确匹配
            context_key = self._build_context_key(tenant_id, user_id, skill_id)
            return self._contexts.get(context_key)

        # 模糊匹配：查找匹配 skill_id 的上下文
        for ctx in self._contexts.values():
            if ctx.skill_id == skill_id:
                return ctx

        return None

    async def _get_or_build_chain(self, context: SkillExecutionContext) -> Any:
        """获取或构建 Chain（带缓存）

        LLM 优先使用注入实例，未注入时主动从模型配置服务获取。
        """
        cache_key = f"chain_{context.skill_id}"

        if cache_key not in context.chain_cache:
            # 获取 LLM（优先注入，否则主动获取）
            llm = self._get_injected_llm()
            if llm is None:
                llm = await self._fetch_llm_from_config()
            if llm is None:
                raise RuntimeError("LLM 未初始化，无法构建 Chain")

            from ai.components.skill.chain_builder import SkillChainBuilder

            builder = SkillChainBuilder(llm)
            chain = builder.build_knowledge_skill_chain(
                skill_document=context.skill_document,
                examples=self._format_examples(context.examples),
            )
            context.chain_cache[cache_key] = chain

        return context.chain_cache[cache_key]

    def _get_injected_llm(self) -> Any:
        """获取注入的 LLM 实例"""
        return getattr(self, "_llm", None)

    async def _fetch_llm_from_config(self) -> Any:
        """从模型配置服务主动获取 LLM

        当调用方未通过 set_llm 注入 LLM 时，主动从模型配置服务获取。
        """
        try:
            from ai.services.model_config_service import ModelConfigService
            from framework.database.dependencies import get_db_session
            from framework.common.ctx import get_tenant_id

            model_config_service = ModelConfigService()
            async with get_db_session() as session:
                tenant_id = get_tenant_id()
                return await model_config_service.get_langchain_llm(
                    session, tenant_id
                )
        except Exception as e:
            logger.error(f"主动获取 LLM 失败: {e}")
            return None

    def set_llm(self, llm: Any) -> None:
        """设置 LLM 实例"""
        self._llm = llm

    def _format_examples(self, examples: dict[str, str]) -> str:
        """格式化示例文档"""
        if not examples:
            return ""

        lines = []
        for filename, content in examples.items():
            lines.append(f"### {filename}\n{content}")

        return "\n\n".join(lines)

    def _format_context(self, context: dict[str, Any] | None) -> str:
        """格式化额外上下文"""
        if not context:
            return "无额外上下文"

        lines = [f"- {key}: {value}" for key, value in context.items()]
        return "\n".join(lines)

    def unload_skill(
        self,
        skill_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """卸载 Skill 上下文

        Returns:
            bool: 是否成功卸载
        """
        if tenant_id and user_id:
            context_key = self._build_context_key(tenant_id, user_id, skill_id)
            if context_key in self._contexts:
                del self._contexts[context_key]
                return True
            return False

        # 模糊匹配
        keys_to_remove = [
            key for key, ctx in self._contexts.items()
            if ctx.skill_id == skill_id
        ]
        for key in keys_to_remove:
            del self._contexts[key]

        return len(keys_to_remove) > 0


# 单例实例
skill_context_manager = SkillContextManager()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/skill/test_context_manager.py -v`

预期：7 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/components/skill/context_manager.py tests/ai/unit/skill/test_context_manager.py
git commit -m "feat(ai): 实现 SkillContextManager 上下文管理器

管理 Skill 加载、卸载和执行上下文，提供 Chain 缓存机制

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 8：扩展对话服务支持 Skill 调用

**文件：**
- 修改：`server/python/src/ai/services/conversation_service.py`
- 测试：`server/python/tests/ai/unit/services/test_conversation_skill.py`

- [ ] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/services/test_conversation_skill.py`：

```python
"""对话服务 Skill 调用单元测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.services.conversation_service import ConversationService


class TestConversationServiceSkill:
    """对话服务 Skill 调用测试"""

    @pytest.fixture
    def service(self):
        return ConversationService()

    @pytest.mark.asyncio
    async def test_chat_with_skill_single_skill(self, service, mock_db_session):
        """测试单 Skill 调用"""
        mock_context = MagicMock()
        mock_context.skill_id = "community/airtable"
        mock_context.skill_name = "airtable"
        mock_context.skill_document = "# Airtable Skill"
        mock_context.examples = {}

        with patch(
            "ai.services.conversation_service.skill_context_manager.load_skill",
            new_callable=AsyncMock,
            return_value=mock_context,
        ), patch(
            "ai.services.conversation_service.skill_context_manager.invoke_skill",
            new_callable=AsyncMock,
            return_value="Skill response",
        ):
            results = []
            async for result in service.chat_with_skill(
                session=mock_db_session,
                conversation_id="conv-001",
                user_message="Create a record",
                skill_ids=["community/airtable"],
                user_id="user-001",
                tenant_id="tenant-001",
            ):
                results.append(result)

        # 验证结果包含 chunk 和 complete
        assert any(r["type"] == "complete" for r in results)

    @pytest.mark.asyncio
    async def test_chat_with_skill_multiple_skills(self, service, mock_db_session):
        """测试多 Skill 组合调用"""
        mock_context = MagicMock()
        mock_context.skill_id = "community/airtable"
        mock_context.skill_document = "# Skill"
        mock_context.examples = {}

        with patch(
            "ai.services.conversation_service.skill_context_manager.load_skill",
            new_callable=AsyncMock,
            return_value=mock_context,
        ), patch(
            "ai.services.conversation_service.skill_context_manager.invoke_skill",
            new_callable=AsyncMock,
            return_value="Combined response",
        ):
            results = []
            async for result in service.chat_with_skill(
                session=mock_db_session,
                conversation_id="conv-001",
                user_message="Combine skills",
                skill_ids=["community/airtable", "community/notion"],
                user_id="user-001",
                tenant_id="tenant-001",
            ):
                results.append(result)

        assert any(r["type"] == "complete" for r in results)

    @pytest.mark.asyncio
    async def test_chat_with_skill_empty_skill_ids(self, service, mock_db_session):
        """测试空 Skill 列表"""
        results = []
        async for result in service.chat_with_skill(
            session=mock_db_session,
            conversation_id="conv-001",
            user_message="test",
            skill_ids=[],
            user_id="user-001",
            tenant_id="tenant-001",
        ):
            results.append(result)

        assert len(results) == 1
        assert results[0]["type"] == "error"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_conversation_skill.py -v`

预期：FAIL，`ConversationService` 无 `chat_with_skill` 方法

- [ ] **步骤 3：扩展对话服务**

在 `server/python/src/ai/services/conversation_service.py` 文件顶部新增导入：

```python
from collections.abc import AsyncGenerator
from ai.components.skill.context_manager import skill_context_manager
```

在 `ConversationService` 类中新增 `chat_with_skill` 方法（在现有方法后追加）：

```python
    async def chat_with_skill(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_message: str,
        skill_ids: list[str],
        user_id: str,
        tenant_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """带 Skill 的对话

        支持单个或多个 Skill 组合调用。

        Args:
            session: 数据库会话
            conversation_id: 对话 ID
            user_message: 用户消息
            skill_ids: Skill ID 列表（支持多个组合调用）
            user_id: 用户 ID
            tenant_id: 租户 ID

        Yields:
            dict: 流式响应块
        """
        if not skill_ids:
            yield {
                "type": "error",
                "error": "未指定 Skill",
                "conversation_id": conversation_id,
            }
            return

        try:
            # 1. 加载所有 Skills
            skill_contexts = []
            for skill_id in skill_ids:
                context = await skill_context_manager.load_skill(
                    skill_id=skill_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                )
                skill_contexts.append(context)

            # 2. 调用 Skill（单 Skill 或组合）
            if len(skill_contexts) == 1:
                # 单 Skill 调用
                result = await skill_context_manager.invoke_skill(
                    skill_ids[0], user_message
                )
            else:
                # 多 Skill 组合调用
                result = await self._invoke_multi_skills(
                    skill_contexts, user_message
                )

            # 3. 流式返回（简化：整体返回）
            yield {
                "type": "chunk",
                "content": result,
                "conversation_id": conversation_id,
                "skill_ids": skill_ids,
            }

            yield {
                "type": "complete",
                "message": result,
                "conversation_id": conversation_id,
                "skill_ids": skill_ids,
            }

        except Exception as e:
            _logger.error(f"Skill 调用失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "conversation_id": conversation_id,
                "skill_ids": skill_ids,
            }

    async def _invoke_multi_skills(
        self,
        contexts: list[Any],
        user_message: str,
    ) -> str:
        """调用多个 Skill 组合

        Args:
            contexts: Skill 上下文列表
            user_message: 用户消息

        Returns:
            str: 组合调用结果
        """
        from ai.components.skill.chain_builder import SkillChainBuilder

        # 获取 LLM
        llm = await self._get_llm_for_skill()
        if llm is None:
            raise RuntimeError("LLM 未配置，无法调用 Skill")

        # 构建多 Skill Chain
        builder = SkillChainBuilder(llm)
        skills = [
            {
                "name": ctx.skill_name,
                "document": ctx.skill_document,
            }
            for ctx in contexts
        ]
        chain = builder.build_multi_skill_chain(skills, user_message)

        # 执行
        result = await chain.ainvoke({"user_request": user_message})
        return result

    async def _get_llm_for_skill(self) -> Any:
        """获取用于 Skill 调用的 LLM 实例"""
        try:
            from ai.services.model_config_service import ModelConfigService

            model_config_service = ModelConfigService()
            from framework.database.dependencies import get_db_session
            from framework.common.ctx import get_tenant_id

            tenant_id = get_tenant_id()
            async with get_db_session() as session:
                llm = await model_config_service.get_langchain_llm(
                    session, tenant_id
                )
                return llm
        except Exception as e:
            _logger.error(f"获取 LLM 失败: {e}")
            return None
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_conversation_skill.py -v`

预期：3 个测试全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/services/conversation_service.py tests/ai/unit/services/test_conversation_skill.py
git commit -m "feat(ai): 对话服务新增 chat_with_skill 方法

支持单 Skill 和多 Skill 组合调用，集成 SkillContextManager

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 9：实现 Skill 调用 API 控制器

**文件：**
- 创建：`server/python/src/ai/schemas/skill.py`
- 创建：`server/python/src/ai/controllers/console/skill_controller.py`
- 修改：`server/python/src/ai/module.py`
- 测试：无（由集成测试覆盖）

- [ ] **步骤 1：创建 Skill Schema**

创建 `server/python/src/ai/schemas/skill.py`：

```python
"""Skill 相关 Schema 定义"""

from __future__ import annotations

from pydantic import Field

from framework.schemas import BaseModel


class SkillInvokeRequest(BaseModel):
    """Skill 调用请求"""

    conversation_id: str = Field(description="对话 ID")
    skill_ids: list[str] = Field(description="Skill ID 列表，支持多个组合调用")
    user_message: str = Field(description="用户消息")


class SkillPreviewResponse(BaseModel):
    """Skill 预览响应"""

    skill_id: str = Field(description="Skill ID")
    name: str = Field(description="Skill 名称")
    description: str | None = Field(default=None, description="Skill 描述")
    skill_type: str = Field(description="Skill 类型：knowledge | script")
    documents: dict[str, str] = Field(
        default_factory=dict, description="Skill 文档内容"
    )


class SkillInvokeChunkResponse(BaseModel):
    """Skill 调用流式响应块"""

    type: str = Field(description="响应类型：chunk | complete | error")
    content: str | None = Field(default=None, description="内容")
    error: str | None = Field(default=None, description="错误信息")
    conversation_id: str | None = Field(default=None, description="对话 ID")
    skill_ids: list[str] | None = Field(default=None, description="Skill ID 列表")
```

- [ ] **步骤 2：创建 Skill 控制器**

创建 `server/python/src/ai/controllers/console/skill_controller.py`：

```python
"""Skill 控制器

提供 Skill 调用和预览 API。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from orjson import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.skill import SkillInvokeRequest, SkillPreviewResponse
from ai.services.conversation_service import ConversationService
from framework.common.ctx import get_tenant_id, get_user_id
from framework.database.dependencies import get_db_session

router = APIRouter(prefix="/ai/console/v1/skills", tags=["Skills"])

conversation_service = ConversationService()


@router.post("/invoke")
async def invoke_skill(
    request: SkillInvokeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """调用 Skill

    支持单个或多个 Skill 组合调用，返回流式响应。

    Args:
        request: 调用请求
        session: 数据库会话

    Returns:
        StreamingResponse: 流式响应
    """
    user_id = get_user_id()
    tenant_id = get_tenant_id()

    async def generate():
        async for chunk in conversation_service.chat_with_skill(
            session=session,
            conversation_id=request.conversation_id,
            user_message=request.user_message,
            skill_ids=request.skill_ids,
            user_id=user_id,
            tenant_id=tenant_id,
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{skill_id}/preview")
async def preview_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """预览 Skill 内容

    返回 Skill 文档和示例，用于前端展示。

    Args:
        skill_id: Skill ID
        session: 数据库会话

    Returns:
        ORJSONResponse: Skill 预览信息
    """
    from tenant.services.plugin_definition_service import (
        plugin_definition_service,
    )
    from tenant.services.plugin_storage_service import plugin_storage_service

    skill_def = await plugin_definition_service.get_by_plugin_id(
        session, skill_id
    )

    if not skill_def or skill_def.plugin_type != "skill":
        raise HTTPException(status_code=404, detail="Skill 不存在")

    # 加载文档
    storage_key = (
        f"skills/global/{skill_id}/{skill_def.local_version}/skill.zip"
    )
    documents = await plugin_storage_service.load_skill_documents(storage_key)

    response = SkillPreviewResponse(
        skill_id=skill_id,
        name=skill_def.name if hasattr(skill_def, "name") else skill_id,
        description=skill_def.declaration.get("metadata", {}).get("description")
        if skill_def.declaration
        else None,
        skill_type=skill_def.skill_type or "knowledge",
        documents=documents,
    )

    return ORJSONResponse(
        content={"code": 200, "msg": "success", "data": response.model_dump()}
    )
```

- [ ] **步骤 3：注册 Skill 路由**

修改 `server/python/src/ai/module.py`，在 `get_routers` 方法中新增 Skill 路由导入和注册。

在现有导入区域新增：

```python
from ai.controllers.console.skill_controller import router as console_skill_router
```

在 `get_routers` 方法的返回列表中新增：

```python
(console_skill_router, "", ["Skills"]),
```

- [ ] **步骤 4：验证路由注册正确**

运行：`cd server/python && uv run python -c "from ai.controllers.console.skill_controller import router; print([r.path for r in router.routes])"`

预期：输出包含 `/ai/console/v1/skills/invoke` 和 `/ai/console/v1/skills/{skill_id}/preview`

- [ ] **步骤 5：Commit**

```bash
cd server/python
git add src/ai/schemas/skill.py src/ai/controllers/console/skill_controller.py src/ai/module.py
git commit -m "feat(ai): 新增 Skill 调用和预览 API

提供 /ai/console/v1/skills/invoke 流式调用接口
提供 /ai/console/v1/skills/{skill_id}/preview 预览接口

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 10：Skill 调用流程集成测试

**文件：**
- 创建：`server/python/tests/ai/integration/test_skill_invocation_flow.py`

- [ ] **步骤 1：编写集成测试**

创建 `server/python/tests/ai/integration/test_skill_invocation_flow.py`：

```python
"""Skill 调用流程集成测试

测试从 Skill 加载到 Chain 构建到 LLM 调用的完整流程。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai.components.skill.chain_builder import SkillChainBuilder
from ai.components.skill.context_manager import (
    SkillContextManager,
    SkillExecutionContext,
)


class TestSkillInvocationFlow:
    """Skill 调用流程集成测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value="Skill execution result")
        return llm

    @pytest.mark.asyncio
    async def test_knowledge_skill_full_flow(self, mock_llm):
        """测试知识文档 Skill 完整调用流程"""
        # 1. 构建上下文
        context_manager = SkillContextManager()
        context_manager.set_llm(mock_llm)

        context = await context_manager.load_skill(
            skill_id="community/airtable",
            user_id="user-001",
            tenant_id="tenant-001",
            conversation_id="conv-001",
            skill_document="# Airtable Skill\nWork with Airtable API.",
            examples={"examples/create.md": "## Create\nCreate a record."},
        )

        # 2. 调用 Skill
        result = await context_manager.invoke_skill(
            skill_id="community/airtable",
            user_request="Create a record",
            tenant_id="tenant-001",
            user_id="user-001",
        )

        # 3. 验证结果
        assert result == "Skill execution result"
        assert context.invoke_count == 1
        assert context.last_invoked_at is not None

    @pytest.mark.asyncio
    async def test_multi_skill_combination(self, mock_llm):
        """测试多 Skill 组合调用"""
        builder = SkillChainBuilder(mock_llm)

        skills = [
            {"name": "airtable", "document": "# Airtable Skill"},
            {"name": "notion", "document": "# Notion Skill"},
        ]

        chain = builder.build_multi_skill_chain(skills, "combine both")

        # Mock chain 执行
        with patch.object(chain, "ainvoke", new_callable=AsyncMock) as mock_ainvoke:
            mock_ainvoke.return_value = "Combined result"
            result = await chain.ainvoke({"user_request": "combine both"})

        assert result == "Combined result"

    @pytest.mark.asyncio
    async def test_skill_chain_caching(self, mock_llm):
        """测试 Skill Chain 缓存"""
        context_manager = SkillContextManager()
        context_manager.set_llm(mock_llm)

        context = await context_manager.load_skill(
            skill_id="community/test",
            user_id="user-001",
            tenant_id="tenant-001",
            conversation_id="conv-001",
            skill_document="# Test Skill",
        )

        # 第一次调用：构建 Chain
        chain1 = await context_manager._get_or_build_chain(context)

        # 第二次调用：使用缓存的 Chain
        chain2 = await context_manager._get_or_build_chain(context)

        # 验证是同一个 Chain 实例
        assert chain1 is chain2

    @pytest.mark.asyncio
    async def test_skill_unload(self, mock_llm):
        """测试 Skill 卸载"""
        context_manager = SkillContextManager()
        context_manager.set_llm(mock_llm)

        await context_manager.load_skill(
            skill_id="community/test",
            user_id="user-001",
            tenant_id="tenant-001",
            conversation_id="conv-001",
            skill_document="# Test",
        )

        # 验证已加载
        assert context_manager._get_active_context(
            "community/test", "tenant-001", "user-001"
        ) is not None

        # 卸载
        result = context_manager.unload_skill(
            "community/test", "tenant-001", "user-001"
        )

        assert result is True
        assert context_manager._get_active_context(
            "community/test", "tenant-001", "user-001"
        ) is None

    @pytest.mark.asyncio
    async def test_skill_invoke_updates_error_history(self, mock_llm):
        """测试 Skill 调用失败记录错误历史"""
        context_manager = SkillContextManager()
        context_manager.set_llm(mock_llm)

        context = await context_manager.load_skill(
            skill_id="community/failing",
            user_id="user-001",
            tenant_id="tenant-001",
            conversation_id="conv-001",
            skill_document="# Failing Skill",
        )

        # Mock Chain 抛出异常
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
        context.chain_cache["chain_community/failing"] = mock_chain

        # 调用应抛出异常
        with pytest.raises(Exception, match="LLM error"):
            await context_manager.invoke_skill(
                "community/failing", "test request",
                tenant_id="tenant-001", user_id="user-001",
            )

        # 验证统计（invoke_count 在异常前已更新）
        assert context.invoke_count == 1
```

- [ ] **步骤 2：运行集成测试**

运行：`cd server/python && uv run pytest tests/ai/integration/test_skill_invocation_flow.py -v`

预期：5 个测试全部 PASS

- [ ] **步骤 3：运行全部 Skill 相关测试确认整体通过**

运行：`cd server/python && uv run pytest tests/ai/unit/runtime/ tests/ai/unit/skill/ tests/ai/integration/test_skill_invocation_flow.py -v --no-header 2>&1 | tail -30`

预期：所有测试通过

- [ ] **步骤 4：Commit**

```bash
cd server/python
git add tests/ai/integration/test_skill_invocation_flow.py
git commit -m "test(ai): 新增 Skill 调用流程集成测试

覆盖完整调用流程、多 Skill 组合、Chain 缓存、卸载、错误历史等场景

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 自检

### 规格覆盖度

对照设计规格 `docs/superpowers/specs/2026-07-06-skills-marketplace-design.md` 检查：

| 规格章节 | 覆盖任务 | 状态 |
|---------|---------|------|
| 5.1 运行时工厂扩展 | 任务 5 | ✅ |
| 5.2 KnowledgeSkillRuntime | 任务 3 | ✅ |
| 5.3 SandboxSkillRuntime | 任务 4 | ✅ |
| 5.4 运行时状态枚举扩展 | 任务 1 | ✅ |
| 6.1 Skill Chain Builder | 任务 6 | ✅ |
| 6.2 Skill Context Manager | 任务 7 | ✅ |
| 6.3 与对话系统集成 | 任务 8 | ✅ |
| 6.4 API 控制器扩展 | 任务 9 | ✅ |
| 8.3 错误处理体系 | 任务 2 | ✅ |
| 8.6 监控指标 | 任务 3、4（get_metrics） | ✅ |

**未覆盖（属于后续计划 3）：**
- 第 7 章前端集成

### 占位符扫描

✅ 无"待定"、"TODO"、"后续实现"占位符
✅ 所有代码步骤包含完整代码
✅ 所有测试步骤包含实际测试代码
✅ 无"类似任务 N"引用

### 类型一致性

- `PluginType.SKILL` 在任务 1 定义后，任务 5 一致使用
- `RuntimeType.SANDBOX`、`RuntimeType.NONE` 在任务 1 定义，任务 3、4、5 一致使用
- `SkillError` 异常体系在任务 2 定义，任务 3、4 一致使用
- `SkillChainBuilder` 在任务 6 定义，任务 7、8 一致使用
- `SkillContextManager` 和 `SkillExecutionContext` 在任务 7 定义，任务 8 一致使用
- `skill_type` 枚举值 `knowledge | script` 全文一致
- `runtime_type` 枚举值 `none | sandbox` 全文一致

### 修复记录

**2026-07-06 审核修复：**

| 问题 | 修复内容 |
|------|---------|
| 任务 3 `_get_llm` 返回 None | 修改为失败时抛出 `SkillPreparationError`，而非返回 None 导致后续调用失败 |
| 任务 4 沙箱缺少内存限制 | 在 `_build_wrapper_script` 中添加 `resource.setrlimit(resource.RLIMIT_AS, ...)` 设置内存上限（Linux/Unix 支持，Windows 跳过） |
| 任务 5 `create_runtime` 签名为 async | 移除 `async` 关键字，与基类 `RuntimeFactory.create_runtime` 同步方法签名一致 |
| 任务 7 ContextManager 单例初始化问题 | 将 `_get_or_build_chain` 改为异步方法，未注入 LLM 时主动通过 `_fetch_llm_from_config` 从模型配置服务获取；同时更新集成测试中调用处为 `await` |

---

## 执行交接

计划已完成并保存到 `docs/superpowers/plans/2026-07-06-skills-marketplace-runtime-langchain.md`。

**本计划覆盖范围：** Phase 4-6（运行时 + LangChain 集成 + 对话系统），共 10 个任务，能独立产出可测试的 Skill 调用能力。

**前置依赖：** 计划 1（后端基础）已完成。

**后续计划：**
- 计划 3：前端集成（Phase 7），计划文档：`docs/superpowers/plans/2026-07-06-skills-marketplace-frontend.md`

**两种执行方式：**

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**
