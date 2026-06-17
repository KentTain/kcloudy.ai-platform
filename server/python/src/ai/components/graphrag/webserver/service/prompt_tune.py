"""GraphRAG 提示词调优服务模块。

GraphRAG prompt tuning service module.

此模块提供提示词自动调优功能,用于优化 GraphRAG 的提示词模板。
This module provides automatic prompt tuning functionality for optimizing GraphRAG prompt templates.
"""

import asyncio

from ai.components.graphrag.prompt_tune.cli import prompt_tune
from ai.components.graphrag.webserver.gtypes.chat_request import PromptTuneParam
from ai.components.graphrag.webserver.task.task import Task
from ai.components.graphrag.webserver.utils.consts import RAGCONFIG_PATH
from ai.components.graphrag.webserver.utils.rag_util import build_root_path


def run_prompt_tune(request: PromptTuneParam, task: Task):
    """
    运行提示词调优(同步版本)。

    Run prompt tuning (synchronous version).

    参数 Parameters
    ----------
    request : PromptTuneParam
        提示词调优参数。Prompt tuning parameters.
    task : Task
        任务对象。Task object.
    """
    task.add_log("运行提示词调优")

    root_dir = build_root_path(request.namespace, request.code, request.filename)
    config_dir = RAGCONFIG_PATH

    asyncio.run(
        prompt_tune(
            config=config_dir,
            root=root_dir,
            domain="",
            skip_entity_types=True,
            min_examples_required=1,
            language="chinese",
        )
    )

    task.set_progress(6)


async def async_run_prompt_tune(request: PromptTuneParam, task: Task):
    """
    运行提示词调优(异步版本)。

    Run prompt tuning (asynchronous version).

    参数 Parameters
    ----------
    request : PromptTuneParam
        提示词调优参数。Prompt tuning parameters.
    task : Task
        任务对象。Task object.
    """
    task.add_log("运行提示词调优")

    root_dir = build_root_path(request.namespace, request.code, request.filename)
    config_dir = RAGCONFIG_PATH

    await prompt_tune(
        config=config_dir,
        root=root_dir,
        domain="",
        skip_entity_types=True,
        min_examples_required=1,
        language="chinese",
    )

    task.set_progress(6)
