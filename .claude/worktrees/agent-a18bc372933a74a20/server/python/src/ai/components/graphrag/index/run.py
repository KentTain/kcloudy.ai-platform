"""运行流水线的不同方法."""

import gc
import json
import logging
import time
import traceback
from collections.abc import AsyncIterable
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from string import Template
from typing import cast

import pandas as pd
from datashaper import (
    DEFAULT_INPUT_NAME,
    MemoryProfile,
    Workflow,
    WorkflowCallbacks,
    WorkflowCallbacksManager,
    WorkflowRunResult,
)

from ai.components.graphrag.index.cache import (
    InMemoryCache,
    PipelineCache,
    load_cache,
)
from ai.components.graphrag.index.config import (
    PipelineBlobCacheConfig,
    PipelineBlobReportingConfig,
    PipelineBlobStorageConfig,
    PipelineCacheConfigTypes,
    PipelineConfig,
    PipelineFileCacheConfig,
    PipelineFileReportingConfig,
    PipelineFileStorageConfig,
    PipelineInputConfigTypes,
    PipelineMemoryCacheConfig,
    PipelineReportingConfigTypes,
    PipelineStorageConfigTypes,
    PipelineWorkflowReference,
    PipelineWorkflowStep,
)
from ai.components.graphrag.index.config.cache import PipelineMinioCacheConfig
from ai.components.graphrag.index.config.reporting import PipelineMinioReportingConfig
from ai.components.graphrag.index.config.storage import PipelineMinioStorageConfig
from ai.components.graphrag.index.context import PipelineRunContext, PipelineRunStats
from ai.components.graphrag.index.emit import TableEmitterType, create_table_emitters
from ai.components.graphrag.index.input import load_input
from ai.components.graphrag.index.load_pipeline_config import load_pipeline_config
from ai.components.graphrag.index.progress import (
    NullProgressReporter,
    ProgressReporter,
)
from ai.components.graphrag.index.reporting import (
    ConsoleWorkflowCallbacks,
    ProgressWorkflowCallbacks,
    load_pipeline_reporter,
)
from ai.components.graphrag.index.storage import (
    MemoryPipelineStorage,
    PipelineStorage,
    load_storage,
)
from ai.components.graphrag.index.typing import PipelineRunResult

# 注册所有动词
from ai.components.graphrag.index.verbs import *  # noqa
from ai.components.graphrag.index.workflows import (
    VerbDefinitions,
    WorkflowDefinitions,
    create_workflow,
    load_workflows,
)

log = logging.getLogger(__name__)


async def run_pipeline_with_config(
    config_or_path: PipelineConfig | str,
    workflows: list[PipelineWorkflowReference] | None = None,
    dataset: pd.DataFrame | None = None,
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    run_id: str | None = None,
    is_resume_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """
    执行pipeline_config。

    Args:
        config_or_path (PipelineConfig | str): config_or_path 参数。
        workflows (list[PipelineWorkflowReference] | None): workflows 参数。
        dataset (pd.DataFrame | None): dataset 参数。
        storage (PipelineStorage | None): storage 参数。
        cache (PipelineCache | None): cache 参数。
        callbacks (WorkflowCallbacks | None): callbacks 参数。
        progress_reporter (ProgressReporter | None): progress_reporter 参数。
        input_post_process_steps (list[PipelineWorkflowStep] | None): input_post_process_steps 参数。
        additional_verbs (VerbDefinitions | None): additional_verbs 参数。
        additional_workflows (WorkflowDefinitions | None): additional_workflows 参数。
        emit (list[TableEmitterType] | None): emit 参数。
        memory_profile (bool): memory_profile 参数。
        run_id (str | None): run_id 参数。
        is_resume_run (bool): is_resume_run 参数。
        _kwargs (dict): _kwargs 参数。

    Yields:
        迭代产生的结果。
    """
    if isinstance(config_or_path, str):
        log.info("Running pipeline with config %s", config_or_path)
    else:
        log.info("Running pipeline")

    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    config = load_pipeline_config(config_or_path)
    config = _apply_substitutions(config, run_id)
    root_dir = config.root_dir

    def _create_storage(config: PipelineStorageConfigTypes | None) -> PipelineStorage:
        """
        创建storage。

        Args:
            config (PipelineStorageConfigTypes | None): config 参数。

        Returns:
            处理结果。
        """
        return load_storage(
            config
            or PipelineFileStorageConfig(base_dir=str(Path(root_dir or "") / "output")),
            root_dir=root_dir,
        )

    def _create_cache(config: PipelineCacheConfigTypes | None) -> PipelineCache:
        """
        创建cache。

        Args:
            config (PipelineCacheConfigTypes | None): config 参数。

        Returns:
            处理结果。
        """
        return load_cache(config or PipelineMemoryCacheConfig(), root_dir=root_dir)

    def _create_reporter(
        config: PipelineReportingConfigTypes | None,
    ) -> WorkflowCallbacks | None:
        """
        创建reporter。

        Args:
            config (PipelineReportingConfigTypes | None): config 参数。

        Returns:
            处理结果。
        """
        return load_pipeline_reporter(config, root_dir) if config else None

    async def _create_input(
        config: PipelineInputConfigTypes | None,
    ) -> pd.DataFrame | None:
        """
        创建input。

        Args:
            config (PipelineInputConfigTypes | None): config 参数。

        Returns:
            处理结果。
        """
        if config is None:
            return None

        return await load_input(config, progress_reporter, root_dir)

    def _create_postprocess_steps(
        config: PipelineInputConfigTypes | None,
    ) -> list[PipelineWorkflowStep] | None:
        """
        创建postprocess_steps。

        Args:
            config (PipelineInputConfigTypes | None): config 参数。

        Returns:
            处理结果。
        """
        return config.post_process if config is not None else None

    progress_reporter = progress_reporter or NullProgressReporter()
    storage = storage or _create_storage(config.storage)
    cache = cache or _create_cache(config.cache)
    callbacks = callbacks or _create_reporter(config.reporting)
    dataset = dataset if dataset is not None else await _create_input(config.input)
    post_process_steps = input_post_process_steps or _create_postprocess_steps(
        config.input
    )
    workflows = workflows or config.workflows

    if dataset is None:
        msg = "No dataset provided!"
        raise ValueError(msg)

    async for table in run_pipeline(
        workflows=workflows,
        dataset=dataset,
        storage=storage,
        cache=cache,
        callbacks=callbacks,
        input_post_process_steps=post_process_steps,
        memory_profile=memory_profile,
        additional_verbs=additional_verbs,
        additional_workflows=additional_workflows,
        progress_reporter=progress_reporter,
        emit=emit,
        is_resume_run=is_resume_run,
    ):
        yield table


async def run_pipeline(
    workflows: list[PipelineWorkflowReference],
    dataset: pd.DataFrame,
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    is_resume_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """
    执行pipeline。

    Args:
        workflows (list[PipelineWorkflowReference]): workflows 参数。
        dataset (pd.DataFrame): dataset 参数。
        storage (PipelineStorage | None): storage 参数。
        cache (PipelineCache | None): cache 参数。
        callbacks (WorkflowCallbacks | None): callbacks 参数。
        progress_reporter (ProgressReporter | None): progress_reporter 参数。
        input_post_process_steps (list[PipelineWorkflowStep] | None): input_post_process_steps 参数。
        additional_verbs (VerbDefinitions | None): additional_verbs 参数。
        additional_workflows (WorkflowDefinitions | None): additional_workflows 参数。
        emit (list[TableEmitterType] | None): emit 参数。
        memory_profile (bool): memory_profile 参数。
        is_resume_run (bool): is_resume_run 参数。
        _kwargs (dict): _kwargs 参数。

    Yields:
        迭代产生的结果。
    """
    start_time = time.time()
    stats = PipelineRunStats()
    storage = storage or MemoryPipelineStorage()
    cache = cache or InMemoryCache()
    progress_reporter = progress_reporter or NullProgressReporter()
    callbacks = callbacks or ConsoleWorkflowCallbacks()
    callbacks = _create_callback_chain(callbacks, progress_reporter)
    emit = emit or [TableEmitterType.Parquet]
    emitters = create_table_emitters(
        emit,
        storage,
        lambda e, s, d: cast("WorkflowCallbacks", callbacks).on_error(
            "Error emitting table", e, s, d
        ),
    )
    loaded_workflows = load_workflows(
        workflows,
        additional_verbs=additional_verbs,
        additional_workflows=additional_workflows,
        memory_profile=memory_profile,
    )
    workflows_to_run = loaded_workflows.workflows
    workflow_dependencies = loaded_workflows.dependencies

    context = _create_run_context(storage, cache, stats)

    if len(emitters) == 0:
        log.info(
            "No emitters provided. No table outputs will be generated. This is probably not correct."
        )

    async def dump_stats() -> None:
        """处理dump_stats。"""
        await storage.set(
            "stats.json", json.dumps(asdict(stats), indent=4, ensure_ascii=False)
        )
        import threading

        from ai.components.graphrag.webserver.task.task import task_factory

        task = task_factory.get_task(threading.current_thread())
        if task:
            await storage.set(
                "task_info.json",
                json.dumps(
                    task.to_task_result().model_dump(), indent=4, ensure_ascii=False
                ),
            )

    async def load_table_from_storage(name: str) -> pd.DataFrame:
        """
        加载load_table_storage。

        Args:
            name (str): name 参数。

        Returns:
            处理结果。
        """
        if not await storage.has(name):
            msg = f"Could not find {name} in storage!"
            raise ValueError(msg)
        try:
            log.info("read table from storage: %s", name)
            return pd.read_parquet(BytesIO(await storage.get(name, as_bytes=True)))
        except Exception:
            log.exception("error loading table from storage: %s", name)
            raise

    async def inject_workflow_data_dependencies(workflow: Workflow) -> None:
        """
        处理inject_workflow_data_dependencies。

        Args:
            workflow (Workflow): workflow 参数。
        """
        workflow.add_table(DEFAULT_INPUT_NAME, dataset)
        deps = workflow_dependencies[workflow.name]
        log.info("dependencies for %s: %s", workflow.name, deps)
        for id in deps:
            workflow_id = f"workflow:{id}"
            table = await load_table_from_storage(f"{id}.parquet")
            workflow.add_table(workflow_id, table)

    async def write_workflow_stats(
        workflow: Workflow,
        workflow_result: WorkflowRunResult,
        workflow_start_time: float,
    ) -> None:
        """
        写入write_workflow_stats。

        Args:
            workflow (Workflow): workflow 参数。
            workflow_result (WorkflowRunResult): workflow_result 参数。
            workflow_start_time (float): workflow_start_time 参数。
        """
        for vt in workflow_result.verb_timings:
            stats.workflows[workflow.name][f"{vt.index}_{vt.verb}"] = vt.timing

        workflow_end_time = time.time()
        stats.workflows[workflow.name]["overall"] = (
            workflow_end_time - workflow_start_time
        )
        stats.total_runtime = time.time() - start_time
        await dump_stats()

        if workflow_result.memory_profile is not None:
            await _save_profiler_stats(
                storage, workflow.name, workflow_result.memory_profile
            )

        log.debug(
            "first row of %s => %s",
            workflow_name,
            workflow.output().iloc[0].to_json(force_ascii=False),
        )

    async def emit_workflow_output(workflow: Workflow) -> pd.DataFrame:
        """
        处理emit_workflow_output。

        Args:
            workflow (Workflow): workflow 参数。

        Returns:
            处理结果。
        """
        output = cast("pd.DataFrame", workflow.output())
        for emitter in emitters:
            await emitter.emit(workflow.name, output)
        return output

    dataset = await _run_post_process_steps(
        input_post_process_steps, dataset, context, callbacks
    )

    # 确保传入的数据有效
    _validate_dataset(dataset)

    log.info("Final # of rows loaded: %s", len(dataset))
    stats.num_documents = len(dataset)
    last_workflow = "input"

    try:
        await dump_stats()

        for workflow_to_run in workflows_to_run:
            # 尝试清除任何中间数据框
            gc.collect()

            workflow = workflow_to_run.workflow
            workflow_name: str = workflow.name
            last_workflow = workflow_name

            log.info("Running workflow: %s...", workflow_name)

            if is_resume_run and await storage.has(
                f"{workflow_to_run.workflow.name}.parquet"
            ):
                log.info("跳过 %s，因为它已经存在", workflow_name)
                continue

            stats.workflows[workflow_name] = {"overall": 0.0}
            await inject_workflow_data_dependencies(workflow)

            workflow_start_time = time.time()
            print(f"workflow.run: {workflow_name}")
            result = await workflow.run(context, callbacks)
            await write_workflow_stats(workflow, result, workflow_start_time)

            # 保存工作流的输出
            output = await emit_workflow_output(workflow)
            yield PipelineRunResult(workflow_name, output, None)
            output = None
            workflow.dispose()
            workflow = None

        stats.total_runtime = time.time() - start_time
        await dump_stats()
    except Exception as e:
        try:
            await dump_stats()
        except Exception as e2:
            print(f"dump_stats Exception :{e2}")

        log.exception("error running workflow %s", last_workflow)
        cast("WorkflowCallbacks", callbacks).on_error(
            "Error running pipeline!", e, traceback.format_exc()
        )
        yield PipelineRunResult(last_workflow, None, [e])


def _create_callback_chain(
    callbacks: WorkflowCallbacks | None, progress: ProgressReporter | None
) -> WorkflowCallbacks:
    """创建回调管理器."""
    manager = WorkflowCallbacksManager()
    if callbacks is not None:
        manager.register(callbacks)
    if progress is not None:
        manager.register(ProgressWorkflowCallbacks(progress))
    return manager


async def _save_profiler_stats(
    storage: PipelineStorage, workflow_name: str, profile: MemoryProfile
):
    """将分析器统计信息保存到存储."""
    await storage.set(
        f"{workflow_name}_profiling.peak_stats.csv",
        profile.peak_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.snapshot_stats.csv",
        profile.snapshot_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.time_stats.csv",
        profile.time_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.detailed_view.csv",
        profile.detailed_view.to_csv(index=True),
    )


async def _run_post_process_steps(
    post_process: list[PipelineWorkflowStep] | None,
    dataset: pd.DataFrame,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame:
    """
    执行post_process_steps。

    Args:
        post_process (list[PipelineWorkflowStep] | None): post_process 参数。
        dataset (pd.DataFrame): dataset 参数。
        context (PipelineRunContext): context 参数。
        callbacks (WorkflowCallbacks): callbacks 参数。

    Returns:
        处理结果。
    """
    if post_process is not None and len(post_process) > 0:
        input_workflow = create_workflow(
            "Input Post Process",
            post_process,
        )
        input_workflow.add_table(DEFAULT_INPUT_NAME, dataset)
        await input_workflow.run(
            context=context,
            callbacks=callbacks,
        )
        dataset = cast("pd.DataFrame", input_workflow.output())
    return dataset


def _validate_dataset(dataset: pd.DataFrame):
    """
    校验validate_dataset。

    Args:
        dataset (pd.DataFrame): dataset 参数。
    """
    if not isinstance(dataset, pd.DataFrame):
        msg = "Dataset must be a pandas dataframe!"
        raise TypeError(msg)


def _apply_substitutions(config: PipelineConfig, run_id: str) -> PipelineConfig:
    """
    处理apply_substitutions。

    Args:
        config (PipelineConfig): config 参数。
        run_id (str): run_id 参数。

    Returns:
        处理结果。
    """
    substitutions = {"timestamp": run_id}

    if (
        isinstance(
            config.storage,
            PipelineFileStorageConfig
            | PipelineBlobStorageConfig
            | PipelineMinioStorageConfig,
        )
        and config.storage.base_dir
    ):
        config.storage.base_dir = Template(config.storage.base_dir).substitute(
            substitutions
        )
    if (
        isinstance(
            config.cache,
            PipelineFileCacheConfig
            | PipelineBlobCacheConfig
            | PipelineMinioCacheConfig,
        )
        and config.cache.base_dir
    ):
        config.cache.base_dir = Template(config.cache.base_dir).substitute(
            substitutions
        )

    if (
        isinstance(
            config.reporting,
            PipelineFileReportingConfig
            | PipelineBlobReportingConfig
            | PipelineMinioReportingConfig,
        )
        and config.reporting.base_dir
    ):
        config.reporting.base_dir = Template(config.reporting.base_dir).substitute(
            substitutions
        )

    return config


def _create_run_context(
    storage: PipelineStorage,
    cache: PipelineCache,
    stats: PipelineRunStats,
) -> PipelineRunContext:
    """为流水线创建运行上下文."""
    return PipelineRunContext(
        stats=stats,
        cache=cache,
        storage=storage,
    )
