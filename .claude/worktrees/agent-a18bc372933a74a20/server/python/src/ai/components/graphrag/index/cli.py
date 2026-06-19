"""主定义."""

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
from ai.components.graphrag.index.init_content import INIT_DOTENV, INIT_YAML
from ai.components.graphrag.index.progress import (
    NullProgressReporter,
    PrintProgressReporter,
    ProgressReporter,
)
from ai.components.graphrag.index.progress.rich import RichProgressReporter
from ai.components.graphrag.index.run import run_pipeline_with_config
from ai.components.graphrag.index.validate_config import validate_config_names

from .graph.extractors.claims.prompts import CLAIM_EXTRACTION_PROMPT
from .graph.extractors.community_reports.prompts import COMMUNITY_REPORT_PROMPT_ZH
from .graph.extractors.graph.prompts import GRAPH_EXTRACTION_PROMPT
from .graph.extractors.summarize.prompts import SUMMARIZE_PROMPT

# 忽略来自numba的警告
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def redact(input: dict) -> str:
    """清理配置json中的敏感信息."""

    # 编辑任何敏感配置
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
):
    """使用给定的配置运行流水线."""
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    _enable_logging(root, run_id, verbose)
    progress_reporter = _get_progress_reporter(reporter)
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

    # 对配置模型值运行预检验证
    parameters = _read_config_parameters(root, config, progress_reporter)
    validate_config_names(progress_reporter, parameters)

    def _run_workflow_async() -> None:
        """执行workflow。"""
        import signal

        def handle_signal(signum, _):
            # 在这里处理信号
            """
            处理handle_signal。

            Args:
                signum: signum 参数。
                _: _ 参数。
            """
            progress_reporter.info(f"Received signal {signum}, exiting...")
            progress_reporter.dispose()
            for task in asyncio.all_tasks():
                task.cancel()
            progress_reporter.info("All tasks cancelled. Exiting...")

        # 为SIGINT和SIGHUP注册信号处理器
        signal.signal(signal.SIGINT, handle_signal)

        if sys.platform != "win32":
            signal.signal(signal.SIGHUP, handle_signal)

        async def execute():
            """执行execute。"""
            nonlocal encountered_errors
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
                    progress_reporter.error(output.workflow)
                else:
                    progress_reporter.success(output.workflow)

                progress_reporter.info(str(output.result))

        if platform.system() == "Windows":
            import nest_asyncio  # type: ignore 忽略，因为在Windows之外这会导致错误

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(execute())
        else:
            import uvloop  # type: ignore 忽略，因为在Windows上这会导致错误

            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:  # type: ignore 忽略，因为在次要版本中这会抛出错误
                runner.run(execute())

    _run_workflow_async()
    progress_reporter.stop()
    if encountered_errors:
        progress_reporter.error(
            "Errors occurred during the pipeline run, see logs for more details."
        )
    else:
        progress_reporter.success("All workflows completed successfully.")

    if cli:
        sys.exit(1 if encountered_errors else 0)


def _initialize_project_at(path: str, reporter: ProgressReporter) -> None:
    """在给定路径初始化项目."""
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
    """在现有配置上覆盖默认值,或者如果未提供配置则创建默认配置."""
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
    读取read_config_parameters。

    Args:
        root (str): root 参数。
        config (str | None): config 参数。
        reporter (ProgressReporter): reporter 参数。

    Returns:
        处理结果。
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


def _get_progress_reporter(reporter_type: str | None) -> ProgressReporter:
    """
    获取progress_reporter。

    Args:
        reporter_type (str | None): reporter_type 参数。

    Returns:
        处理结果。
    """
    if reporter_type is None or reporter_type == "rich":
        return RichProgressReporter("GraphRAG Indexer ")
    if reporter_type == "print":
        return PrintProgressReporter("GraphRAG Indexer ")
    if reporter_type == "none":
        return NullProgressReporter()

    msg = f"Invalid progress reporter type: {reporter_type}"
    raise ValueError(msg)


def _enable_logging(root_dir: str, run_id: str, verbose: bool) -> None:
    """
    处理enable_logging。

    Args:
        root_dir (str): root_dir 参数。
        run_id (str): run_id 参数。
        verbose (bool): verbose 参数。
    """
    logging_file = (
        Path(root_dir) / "output" / run_id / "reports" / "indexing-engine.log"
    )
    logging_file.parent.mkdir(parents=True, exist_ok=True)

    logging_file.touch(exist_ok=True)

    logging.basicConfig(
        filename=str(logging_file),
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )
