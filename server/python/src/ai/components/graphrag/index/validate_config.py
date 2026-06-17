"""包含validate_config_names定义的模块."""

import asyncio
import sys

from datashaper import NoopVerbCallbacks

from ai.components.graphrag.config.models import GraphRagConfig
from ai.components.graphrag.index.llm import load_llm, load_llm_embeddings
from ai.components.graphrag.index.progress import (
    ProgressReporter,
)


def validate_config_names(
    reporter: ProgressReporter, parameters: GraphRagConfig
) -> None:
    """验证配置文件中LLM部署名称的拼写错误."""
    # 验证聊天LLM配置
    llm = load_llm(
        "test-llm",
        parameters.llm.type,
        NoopVerbCallbacks(),
        None,
        parameters.llm.model_dump(),
    )
    try:
        asyncio.run(llm("This is an LLM connectivity test. Say Hello World"))
        reporter.success("LLM Config Params Validated")
    except Exception as e:
        reporter.error(f"LLM configuration error detected. Exiting...\n{e}")
        sys.exit(1)

    # 验证嵌入LLM配置
    embed_llm = load_llm_embeddings(
        "test-embed-llm",
        parameters.embeddings.llm.type,
        NoopVerbCallbacks(),
        None,
        parameters.embeddings.llm.model_dump(),
    )
    try:
        asyncio.run(embed_llm(["This is an LLM Embedding Test String"]))
        reporter.success("Embedding LLM Config Params Validated")
    except Exception as e:
        reporter.error(f"Embedding LLM configuration error detected. Exiting...\n{e}")
        sys.exit(1)
