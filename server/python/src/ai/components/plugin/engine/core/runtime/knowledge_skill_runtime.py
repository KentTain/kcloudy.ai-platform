"""Knowledge Skill Runtime 实现

零隔离运行时，通过 LangChain PromptTemplate 加载 Markdown 文档，由 LLM 理解执行。
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from ai.components.plugin.engine.core.exceptions import SkillPreparationError
from ai.components.plugin.engine.core.runtime.base import (
    PluginRuntime,
    PluginRuntimeState,
)
from ai.components.plugin.engine.models.plugin import PluginInfo
from tenant.services.plugin.plugin_storage_service import plugin_storage_service


class KnowledgeSkillRuntime(PluginRuntime):
    """Knowledge Skill 运行时

    零隔离运行时，通过 LangChain PromptTemplate 加载 Markdown 文档，由 LLM 理解执行。
    """

    skill_type = "knowledge"
    runtime_type = "none"

    def __init__(self, plugin_info: PluginInfo, workspace_dir: Path):
        super().__init__(plugin_info, workspace_dir)

        # Skill 文档
        self._skill_documents: dict[str, str] = {}

        # LangChain 组件
        self._chain: Any = None
        self._llm: Any = None

        # 运行时指标
        self._invoke_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_duration_ms = 0
        self._recent_errors: list[dict[str, Any]] = []

    async def prepare(self) -> None:
        """从 MinIO 加载 Skill 文档，验证 SKILL.md 存在，构建 Prompt Chain"""
        if self.is_prepared:
            self._plugin_logger.info(f"Skill {self.plugin_name} 已完成预处理，跳过")
            return

        self._plugin_logger.info(f"开始预处理 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.PREPARING)

        try:
            # 1. 从 MinIO 加载文档
            storage_key = self._get_storage_key()
            self._skill_documents = await self._load_skill_documents(storage_key)

            # 2. 验证 SKILL.md 存在
            if "SKILL.md" not in self._skill_documents:
                raise SkillPreparationError(
                    self.plugin_id, "缺少 SKILL.md 文件"
                )

            # 3. 移除 YAML front matter
            self._strip_yaml_front_matter()

            # 4. 构建 Prompt Chain
            self._build_prompt_chain()

            self._update_state(PluginRuntimeState.PREPARED)
            self._plugin_logger.info(f"Skill {self.plugin_name} 预处理完成")

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"Skill {self.plugin_name} 预处理失败: {e}")
            raise

    async def start(self) -> None:
        """初始化 LLM，构建完整 Chain"""
        if self.is_running:
            self._plugin_logger.info(f"Skill {self.plugin_name} 已在运行")
            return

        if not self.is_prepared:
            raise RuntimeError(
                f"Skill {self.plugin_name} 未完成预处理，请先调用 prepare()"
            )

        self._plugin_logger.info(f"启动 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STARTING)

        try:
            # 获取 LLM 实例
            self._llm = self._get_llm()

            # 构建完整 Chain
            from langchain_core.output_parsers import StrOutputParser

            self._chain = self._prompt_chain | self._llm | StrOutputParser()

            self._update_state(PluginRuntimeState.RUNNING)
            self._plugin_logger.info(f"Skill {self.plugin_name} 启动成功")

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            self._plugin_logger.error(f"Skill {self.plugin_name} 启动失败: {e}")
            raise

    async def stop(self) -> None:
        """清理 LLM 和 Chain 资源"""
        if not self.is_running:
            return

        self._plugin_logger.info(f"停止 Skill: {self.plugin_name}")
        self._update_state(PluginRuntimeState.STOPPING)

        try:
            self._chain = None
            self._llm = None

            self._update_state(PluginRuntimeState.STOPPED)
            self._plugin_logger.info(f"Skill {self.plugin_name} 已停止")

        except Exception as e:
            self._plugin_logger.error(f"停止 Skill {self.plugin_name} 失败: {e}")
            raise

    async def invoke_stream(
        self,
        invoke_request: dict[str, Any],
        timeout: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """流式调用 Skill"""
        if not self.is_running:
            yield {
                "type": "error",
                "error": "Skill 未运行",
                "skill_id": self.plugin_id,
            }
            return

        import time

        start_time = time.time()
        self._invoke_count += 1

        try:
            user_request = invoke_request.get("user_request", "")

            # 流式调用
            async for chunk in self._chain.astream({"user_request": user_request}):
                yield {
                    "type": "chunk",
                    "content": chunk.content if hasattr(chunk, "content") else str(chunk),
                    "skill_id": self.plugin_id,
                }

            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            self._total_duration_ms += duration_ms
            self._success_count += 1

            # 返回完成事件
            yield {
                "type": "complete",
                "skill_id": self.plugin_id,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            self._failure_count += 1
            error_msg = str(e)
            self._recent_errors.append({
                "error": error_msg,
                "timestamp": time.time(),
            })

            # 保持最近 10 个错误
            if len(self._recent_errors) > 10:
                self._recent_errors = self._recent_errors[-10:]

            yield {
                "type": "error",
                "error": error_msg,
                "skill_id": self.plugin_id,
            }

    async def get_metrics(self) -> dict[str, Any]:
        """获取运行时指标"""
        return {
            "invoke_count": self._invoke_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "total_duration_ms": self._total_duration_ms,
            "recent_errors": self._recent_errors.copy(),
        }

    async def get_logs(
        self, limit: int = 100, level: str | None = None
    ) -> list[dict[str, Any]]:
        """获取运行时日志（空列表）"""
        return []

    def _build_prompt_chain(self) -> None:
        """构建 LangChain Prompt"""
        from langchain_core.prompts import PromptTemplate

        # 获取 Skill 文档
        skill_document = self._skill_documents.get("SKILL.md", "")
        examples = self._skill_documents.get("EXAMPLES.md", "")

        # 构建 Prompt 模板
        template = """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

## 技能说明
{skill_document}

## 使用示例
{examples}

## 用户请求
{user_request}

请根据技能说明和示例，帮助用户完成任务。"""

        self._prompt_chain = PromptTemplate(
            template=template,
            input_variables=["skill_document", "examples", "user_request"],
            partial_variables={
                "skill_document": skill_document,
                "examples": examples,
            },
        )

    async def _load_skill_documents(self, storage_key: str) -> dict[str, str]:
        """从 MinIO 加载文档"""
        return await plugin_storage_service.load_skill_documents(storage_key)

    def _get_storage_key(self) -> str:
        """返回存储路径"""
        return f"skills/global/{self.plugin_id}/{self.plugin_version}/skill.zip"

    def _get_llm(self) -> Any:
        """获取 LLM 实例"""
        # TODO: 从配置获取 LLM
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    def _strip_yaml_front_matter(self) -> None:
        """移除 YAML front matter"""
        import re

        for filename, content in self._skill_documents.items():
            # 移除 YAML front matter (--- ... ---)
            pattern = r"^---\n.*?\n---\n"
            self._skill_documents[filename] = re.sub(
                pattern, "", content, flags=re.DOTALL
            )
