"""包含 load_workflows,create_workflow,_get_steps_for_workflow 和 _remove_disabled_steps 方法定义的模块."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from datashaper import Workflow

from ai.components.graphrag.index.errors import (
    NoWorkflowsDefinedError,
    UndefinedWorkflowError,
    UnknownWorkflowError,
)
from ai.components.graphrag.index.utils import topological_sort
from ai.components.graphrag.index.workflows.default_workflows import (
    default_workflows as _default_workflows,
)
from ai.components.graphrag.index.workflows.typing import (
    VerbDefinitions,
    WorkflowDefinitions,
    WorkflowToRun,
)

if TYPE_CHECKING:
    from ai.components.graphrag.index.config import (
        PipelineWorkflowConfig,
        PipelineWorkflowReference,
        PipelineWorkflowStep,
    )

anonymous_workflow_count = 0

VerbFn = Callable[..., Any]
log = logging.getLogger(__name__)


class LoadWorkflowResult(NamedTuple):
    """workflow 加载结果对象."""

    workflows: list[WorkflowToRun]
    """已加载的 workflow 名称列表,按应该运行的顺序排列."""

    dependencies: dict[str, list[str]]
    """workflow 名称到其依赖项的字典映射."""


def load_workflows(
    workflows_to_load: list[PipelineWorkflowReference],
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    memory_profile: bool = False,
) -> LoadWorkflowResult:
    """
    加载给定的 workflows。

    Args:
        - workflows_to_load - 要加载的 workflows
        - additional_verbs - 可用于 workflows 的自定义 verbs 列表
        - additional_workflows - 自定义 workflows 列表
    Returns:
        - output[0] - 已加载的 workflow 名称列表,按应该运行的顺序排列
        - output[1] - workflow 名称到其依赖项的字典映射
    """
    workflow_graph: dict[str, WorkflowToRun] = {}

    global anonymous_workflow_count
    for reference in workflows_to_load:
        name = reference.name
        is_anonymous = name is None or name.strip() == ""
        if is_anonymous:
            name = f"Anonymous Workflow {anonymous_workflow_count}"
            anonymous_workflow_count += 1
        name = cast("str", name)

        config = reference.config
        workflow = create_workflow(
            name or "MISSING NAME!",
            reference.steps,
            config,
            additional_verbs,
            additional_workflows,
        )
        workflow_graph[name] = WorkflowToRun(workflow, config=config or {})

    # 回填任何缺失的 workflows
    for name in list(workflow_graph.keys()):
        workflow = workflow_graph[name]
        deps = [
            d.replace("workflow:", "")
            for d in workflow.workflow.dependencies
            if d.startswith("workflow:")
        ]
        for dependency in deps:
            if dependency not in workflow_graph:
                reference = {"name": dependency, **workflow.config}
                workflow_graph[dependency] = WorkflowToRun(
                    workflow=create_workflow(
                        dependency,
                        config=reference,
                        additional_verbs=additional_verbs,
                        additional_workflows=additional_workflows,
                        memory_profile=memory_profile,
                    ),
                    config=reference,
                )

    # 按依赖项顺序运行 workflows
    def filter_wf_dependencies(name: str) -> list[str]:
        """
        过滤filter_wf_dependencies。

        Args:
            name (str): name 参数。

        Returns:
            处理结果。
        """
        externals = [
            e.replace("workflow:", "")
            for e in workflow_graph[name].workflow.dependencies
        ]
        return [e for e in externals if e in workflow_graph]

    task_graph = {name: filter_wf_dependencies(name) for name in workflow_graph}
    workflow_run_order = topological_sort(task_graph)
    workflows = [workflow_graph[name] for name in workflow_run_order]
    log.info("Workflow Run Order: %s", workflow_run_order)
    return LoadWorkflowResult(workflows=workflows, dependencies=task_graph)


def create_workflow(
    name: str,
    steps: list[PipelineWorkflowStep] | None = None,
    config: PipelineWorkflowConfig | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    memory_profile: bool = False,
) -> Workflow:
    """从给定的配置创建一个 workflow."""
    additional_workflows = {
        **_default_workflows,
        **(additional_workflows or {}),
    }
    steps = steps or _get_steps_for_workflow(name, config, additional_workflows)
    steps = _remove_disabled_steps(steps)
    return Workflow(
        verbs=additional_verbs or {},
        schema={
            "name": name,
            "steps": steps,
        },
        validate=False,
        memory_profile=memory_profile,
    )


def _get_steps_for_workflow(
    name: str | None,
    config: PipelineWorkflowConfig | None,
    workflows: dict[str, Callable] | None,
) -> list[PipelineWorkflowStep]:
    """获取给定 workflow 配置的步骤."""
    if config is not None and "steps" in config:
        return config["steps"]

    if workflows is None:
        raise NoWorkflowsDefinedError

    if name is None:
        raise UndefinedWorkflowError

    if name not in workflows:
        raise UnknownWorkflowError(name)

    return workflows[name](config or {})


def _remove_disabled_steps(
    steps: list[PipelineWorkflowStep],
) -> list[PipelineWorkflowStep]:
    """
    移除disabled_steps。

    Args:
        steps (list[PipelineWorkflowStep]): steps 参数。

    Returns:
        处理结果。
    """
    return [step for step in steps if step.get("enabled", True)]
