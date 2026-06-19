"""包含'CommunityReportsResult'和'CommunityReportsExtractor'模型的模块."""

import logging
import traceback
from dataclasses import dataclass
from typing import Any

import yaml

from ai.components.graphrag.index.graph.extractors.community_reports.prompts import (
    COMMUNITY_REPORT_PROMPT,
)
from ai.components.graphrag.index.typing import ErrorHandlerFn
from ai.components.graphrag.llm import CompletionLLM

log = logging.getLogger(__name__)


@dataclass
class CommunityReportsResult:
    """社区报告结果类定义."""

    output: str
    structured_output: dict


class CommunityReportsExtractor:
    """社区报告提取器类定义."""

    _llm: CompletionLLM
    _input_text_key: str
    _extraction_prompt: str
    _output_formatter_prompt: str
    _on_error: ErrorHandlerFn
    _max_report_length: int

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        input_text_key: str | None = None,
        extraction_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_report_length: int | None = None,
    ):
        """初始化方法定义."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._extraction_prompt = extraction_prompt or COMMUNITY_REPORT_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_report_length = max_report_length or 1500

    async def __call__(self, inputs: dict[str, Any]):
        """调用方法定义."""
        output = None
        try:
            response = (
                await self._llm(
                    self._extraction_prompt,
                    name="create_community_report",
                    variables={self._input_text_key: inputs[self._input_text_key]},
                    model_parameters={"max_tokens": self._max_report_length},
                )
                or {}
            )
            # 解析 YAML 格式的输出
            raw_output = response.output or ""
            output = self._parse_yaml_output(raw_output)
        except Exception as e:
            log.exception("error generating community report")
            self._on_error(e, traceback.format_exc(), None)
            output = {}

        text_output = self._get_text_output(output)
        return CommunityReportsResult(
            structured_output=output,
            output=text_output,
        )

    def _parse_yaml_output(self, raw_output: str) -> dict:
        """
        解析 YAML 格式的输出字符串。

        Args:
            raw_output: LLM 返回的原始 YAML 字符串

        Returns:
            解析后的字典，如果解析失败返回空字典
        """
        try:
            # 清理 markdown 代码块包裹
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```"):
                # 移除开头的 ```json 或 ```
                lines = cleaned_output.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 移除结尾的 ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_output = "\n".join(lines).strip()

            # 尝试解析 YAML
            parsed = yaml.safe_load(cleaned_output)
            if not isinstance(parsed, dict):
                log.warning(f"YAML 解析结果不是字典: {type(parsed)}")
                return {}

            # 验证必需字段
            required_fields = [
                "title",
                "summary",
                "findings",
                "rating",
                "rating_explanation",
            ]
            for field in required_fields:
                if field not in parsed:
                    log.warning(f"YAML 解析结果缺少必需字段: {field}")
                    return {}

            # 验证字段类型
            if not isinstance(parsed["title"], str):
                log.warning("title 字段类型不是 str")
                return {}
            if not isinstance(parsed["summary"], str):
                log.warning("summary 字段类型不是 str")
                return {}
            if not isinstance(parsed["findings"], list):
                log.warning("findings 字段类型不是 list")
                return {}
            if not isinstance(parsed["rating"], (float, int)):
                log.warning("rating 字段类型不是 float 或 int")
                return {}
            if not isinstance(parsed["rating_explanation"], str):
                log.warning("rating_explanation 字段类型不是 str")
                return {}

            # 确保 rating 是 float 类型
            parsed["rating"] = float(parsed["rating"])

            return parsed
        except yaml.YAMLError as e:
            log.warning(f"YAML 解析失败: {e}")
            return {}
        except Exception as e:
            log.warning(f"输出解析异常: {e}")
            return {}

    def _get_text_output(self, parsed_output: dict) -> str:
        """
        获取text_output。

        Args:
            parsed_output (dict): parsed_output 参数。

        Returns:
            处理结果。
        """
        title = parsed_output.get("title", "Report")
        summary = parsed_output.get("summary", "")
        findings = parsed_output.get("findings", [])

        def finding_summary(finding: dict):
            """
            处理finding_summary。

            Args:
                finding (dict): finding 参数。

            Returns:
                处理结果。
            """
            if isinstance(finding, str):
                return finding
            return finding.get("summary")

        def finding_explanation(finding: dict):
            """
            处理finding_explanation。

            Args:
                finding (dict): finding 参数。

            Returns:
                处理结果。
            """
            if isinstance(finding, str):
                return ""
            return finding.get("explanation")

        report_sections = "\n\n".join(
            f"## {finding_summary(f)}\n\n{finding_explanation(f)}" for f in findings
        )
        return f"# {title}\n\n{summary}\n\n{report_sections}"
