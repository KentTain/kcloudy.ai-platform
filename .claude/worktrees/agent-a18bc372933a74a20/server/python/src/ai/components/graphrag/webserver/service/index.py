"""GraphRAG 索引服务模块。

GraphRAG index service module.

此模块提供 GraphRAG 索引管道的执行功能,包括配置读取,工作流运行和进度报告。
This module provides execution functions for GraphRAG indexing pipeline, including configuration reading, workflow execution and progress reporting.
"""

import asyncio
import json
import logging
import platform
import sys
import time
import warnings
from pathlib import Path

from ai.components.graphrag.config import (
    create_graphrag_config,
)
from ai.components.graphrag.index import PipelineConfig, create_pipeline_config
from ai.components.graphrag.index.cache import NoopPipelineCache
from ai.components.graphrag.index.emit import TableEmitterType
from ai.components.graphrag.index.graph.extractors.claims.prompts import (
    CLAIM_EXTRACTION_PROMPT,
)
from ai.components.graphrag.index.graph.extractors.community_reports.prompts import (
    COMMUNITY_REPORT_PROMPT_ZH,
)
from ai.components.graphrag.index.graph.extractors.graph.prompts import (
    GRAPH_EXTRACTION_PROMPT,
)
from ai.components.graphrag.index.graph.extractors.summarize.prompts import (
    SUMMARIZE_PROMPT,
)
from ai.components.graphrag.index.init_content import INIT_DOTENV, INIT_YAML
from ai.components.graphrag.index.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from ai.components.graphrag.index.run import run_pipeline_with_config
from ai.components.graphrag.webserver.gtypes.chat_request import IndexParam
from ai.components.graphrag.webserver.task.progress_reporter import (
    TaskProgressReporter,
)
from ai.components.graphrag.webserver.task.task import Task
from ai.components.graphrag.webserver.utils.consts import RAGCONFIG_PATH
from ai.components.graphrag.webserver.utils.rag_util import build_root_path

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def run_index(request: IndexParam, task: Task):
    """
    运行索引构建。

    Run index construction.

    参数 Parameters
    ----------
    request : IndexParam
        索引参数。Index parameters.
    task : Task
        任务对象。Task object.
    """
    root_dir = build_root_path(request.namespace, request.code, request.filename)
    config_dir = RAGCONFIG_PATH

    index_cli(
        root=root_dir,
        verbose=False,
        resume=None,
        memprofile=False,
        nocache=False,
        reporter=None,
        config=config_dir,
        emit=None,
        dryrun=False,
        init=False,
        overlay_defaults=True,
        cli=False,
        task=task,
    )


def redact(input: dict) -> str:
    """
    清理配置 JSON 中的敏感信息。

    Sanitize the config json.

    参数 Parameters
    ----------
    input : dict
        输入配置字典。Input configuration dictionary.

    返回 Returns
    -------
    str
        清理后的 JSON 字符串。Sanitized JSON string.
    """

    # 清理任何敏感配置 / Redact any sensitive configuration
    def redact_dict(input: dict) -> dict:
        """
        处理redact_dict。

        Args:
            input (dict): input 参数。

        Returns:
            处理结果。
        """
        if not isinstance(input, dict):
            return input

        result = {}
        for key, value in input.items():
            if key in {
                "api_key",
                "connection_string",
                "container_name",
                "organization",
            }:
                if value is not None:
                    result[key] = f"REDACTED, length {len(value)}"
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [redact_dict(i) for i in value]
            else:
                result[key] = value
        return result

    redacted_dict = redact_dict(input)
    return json.dumps(redacted_dict, ensure_ascii=False, indent=4)


def index_cli(
    root: str,
    init: bool,
    verbose: bool,
    resume: str | None,
    memprofile: bool,
    nocache: bool,
    reporter: str | None,
    config: str | None,
    emit: str | None,
    dryrun: bool,
    overlay_defaults: bool,
    cli: bool = False,
    task: Task = None,
):
    """
    使用给定配置运行索引管道。

    Run the pipeline with the given config.

    参数 Parameters
    ----------
    root : str
        根目录路径。Root directory path.
    init : bool
        是否初始化项目。Whether to initialize project.
    verbose : bool
        是否详细输出。Whether to output verbosely.
    resume : str | None
        恢复运行 ID。Resume run ID.
    memprofile : bool
        是否启用内存分析。Whether to enable memory profiling.
    nocache : bool
        是否禁用缓存。Whether to disable cache.
    reporter : str | None
        进度报告器类型。Progress reporter type.
    config : str | None
        配置文件路径。Configuration file path.
    emit : str | None
        输出类型。Output types.
    dryrun : bool
        是否空运行。Whether to dry run.
    overlay_defaults : bool
        是否覆盖默认值。Whether to overlay defaults.
    cli : bool, optional
        是否为 CLI 模式。Whether in CLI mode.
    task : Task, optional
        任务对象。Task object.
    """
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose)
    progress_reporter = _get_progress_reporter(reporter, task)
    if init:
        _initialize_project_at(root, progress_reporter)
        sys.exit(0)
    if overlay_defaults:
        pipeline_config: str | PipelineConfig = _create_default_config(
            root, config, verbose, dryrun or False, progress_reporter
        )
    else:
        pipeline_config: str | PipelineConfig = config or _create_default_config(
            root, None, verbose, dryrun or False, progress_reporter
        )
    cache = NoopPipelineCache() if nocache else None
    pipeline_emit = emit.split(",") if emit else None
    encountered_errors = False
    last_errors: list = None

    def _run_workflow_async() -> None:
        """执行workflow。"""

        async def execute():
            """执行execute。"""
            nonlocal encountered_errors
            nonlocal last_errors
            async for output in run_pipeline_with_config(
                pipeline_config,
                run_id=run_id,
                memory_profile=memprofile,
                cache=cache,
                progress_reporter=progress_reporter,
                emit=(
                    [TableEmitterType(e) for e in pipeline_emit]
                    if pipeline_emit
                    else None
                ),
                is_resume_run=bool(resume),
            ):
                if output.errors and len(output.errors) > 0:
                    encountered_errors = True
                    last_errors = output.errors
                    progress_reporter.error(output.workflow)
                else:
                    progress_reporter.success(output.workflow)

                progress_reporter.info(str(output.result))

        if platform.system() == "Windows":
            import nest_asyncio  # type: ignore Ignoring because out of windows this will cause an error

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(execute())
        else:
            import uvloop  # type: ignore Ignoring because on windows this will cause an error

            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:  # type: ignore Ignoring because minor versions this will throw an error
                runner.run(execute())

    _run_workflow_async()
    progress_reporter.stop()
    if encountered_errors:
        error_list = [str(error) for error in last_errors]
        error_str = "(-1)"
        if len(error_list) > 0:
            error_str = "\n".join(error_list)
            progress_reporter.error(f"{error_str}")

        if task.is_running():
            progress_reporter.error("执行任务发生异常")
            task.fail(f"任务失败：{error_str}")
        elif task.is_cancelling():
            progress_reporter.error("任务已取消")
            task.cancelled("任务已取消")
        else:
            progress_reporter.error("执行任务发生异常(2)")
            task.fail(f"任务失败(2)：{error_str}")
    else:
        progress_reporter.success("All workflows completed successfully.")
        task.done("任务已完成")

    if cli:
        sys.exit(1 if encountered_errors else 0)


def _initialize_project_at(path: str, reporter: ProgressReporter) -> None:
    """
    在指定路径初始化项目。

    Initialize the project at the given path.

    参数 Parameters
    ----------
    path : str
        项目路径。Project path.
    reporter : ProgressReporter
        进度报告器。Progress reporter.
    """
    reporter.info(f"Initializing project at {path}")
    root = Path(path)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    settings_yaml = root / "settings.yaml"
    if settings_yaml.exists():
        msg = f"Project already initialized at {root}"
        raise ValueError(msg)

    dotenv = root / ".env"
    if not dotenv.exists():
        with settings_yaml.open("wb") as file:
            file.write(INIT_YAML.encode(encoding="utf-8", errors="strict"))

    with dotenv.open("wb") as file:
        file.write(INIT_DOTENV.encode(encoding="utf-8", errors="strict"))

    prompts_dir = root / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)

    entity_extraction = prompts_dir / "entity_extraction.txt"
    if not entity_extraction.exists():
        with entity_extraction.open("wb") as file:
            file.write(
                GRAPH_EXTRACTION_PROMPT.encode(encoding="utf-8", errors="strict")
            )

    summarize_descriptions = prompts_dir / "summarize_descriptions.txt"
    if not summarize_descriptions.exists():
        with summarize_descriptions.open("wb") as file:
            file.write(SUMMARIZE_PROMPT.encode(encoding="utf-8", errors="strict"))

    claim_extraction = prompts_dir / "claim_extraction.txt"
    if not claim_extraction.exists():
        with claim_extraction.open("wb") as file:
            file.write(
                CLAIM_EXTRACTION_PROMPT.encode(encoding="utf-8", errors="strict")
            )

    community_report = prompts_dir / "community_report.txt"
    if not community_report.exists():
        with community_report.open("wb") as file:
            file.write(
                COMMUNITY_REPORT_PROMPT_ZH.encode(encoding="utf-8", errors="strict")
            )


def _create_default_config(
    root: str,
    config: str | None,
    verbose: bool,
    dryrun: bool,
    reporter: ProgressReporter,
) -> PipelineConfig:
    """
    在现有配置上覆盖默认值,或在未提供配置时创建默认配置。

    Overlay default values on an existing config or create a default config if none is provided.

    参数 Parameters
    ----------
    root : str
        根目录路径。Root directory path.
    config : str | None
        配置文件路径。Configuration file path.
    verbose : bool
        是否详细输出。Whether to output verbosely.
    dryrun : bool
        是否空运行。Whether to dry run.
    reporter : ProgressReporter
        进度报告器。Progress reporter.

    返回 Returns
    -------
    PipelineConfig
        管道配置对象。Pipeline configuration object.
    """
    if config and not Path(config).exists():
        msg = f"Configuration file {config} does not exist"
        raise ValueError

    if not Path(root).exists():
        msg = f"Root directory {root} does not exist"
        raise ValueError(msg)

    parameters = _read_config_parameters(root, config, reporter)
    log.info(
        "using default configuration: %s",
        redact(parameters.model_dump()),
    )

    if verbose or dryrun:
        reporter.info(f"Using default configuration: {redact(parameters.model_dump())}")
    result = create_pipeline_config(parameters, verbose)
    if verbose or dryrun:
        reporter.info(f"Final Config: {redact(result.model_dump())}")

    if dryrun:
        reporter.info("dry run complete, exiting...")
        sys.exit(0)
    return result


def _read_config_parameters(root: str, config: str | None, reporter: ProgressReporter):
    """
    读取配置参数。

    Read configuration parameters.

    参数 Parameters
    ----------
    root : str
        根目录路径。Root directory path.
    config : str | None
        配置文件路径。Configuration file path.
    reporter : ProgressReporter
        进度报告器。Progress reporter.

    返回 Returns
    -------
    GraphRagConfig
        GraphRAG 配置对象。GraphRAG configuration object.
    """
    _root = Path(root)
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )

    if settings_yaml.exists():
        reporter.success(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("rb") as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.success(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    reporter.success("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)


def _get_progress_reporter(
    reporter_type: str | None,
    task: Task = None,
) -> ProgressReporter:
    """
    获取进度报告器实例。

    Get progress reporter instance.

    参数 Parameters
    ----------
    reporter_type : str | None
        报告器类型。Reporter type.
    task : Task, optional
        任务对象。Task object.

    返回 Returns
    -------
    ProgressReporter
        进度报告器实例。Progress reporter instance.
    """
    if reporter_type is None or reporter_type == "rich":
        return TaskProgressReporter("索引 ", task=task)
        # return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)


def _enable_logging(root_dir: str, run_id: str, verbose: bool) -> None:
    """
    启用日志记录。

    Enable logging.

    参数 Parameters
    ----------
    root_dir : str
        根目录路径。Root directory path.
    run_id : str
        运行 ID。Run ID.
    verbose : bool
        是否详细输出。Whether to output verbosely.
    """
    logging_file = Path(root_dir) / "output" / "reports" / "indexing-engine.log"
    logging_file.parent.mkdir(parents=True, exist_ok=True)

    logging_file.touch(exist_ok=True)

    logging.shutdown()

    logging.basicConfig(
        filename=str(logging_file),
        filemode="a",
        force=True,
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )
