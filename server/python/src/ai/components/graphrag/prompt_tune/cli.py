"""提示词微调模块的命令行接口。

Command line interface for the fine_tune module.
"""

from pathlib import Path

from ai.components.graphrag.index.progress import PrintProgressReporter
from ai.components.graphrag.prompt_tune import api
from ai.components.graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from ai.components.graphrag.prompt_tune.loader import (
    MIN_CHUNK_SIZE,
    read_config_parameters,
)
from ai.components.graphrag.prompt_tune.types import DocSelectionType

from .generator.community_report_summarization import COMMUNITY_SUMMARIZATION_FILENAME
from .generator.entity_extraction_prompt import ENTITY_EXTRACTION_FILENAME
from .generator.entity_summarization_prompt import ENTITY_SUMMARIZATION_FILENAME


async def prompt_tune(
    config: str,
    root: str,
    domain: str,
    selection_method: DocSelectionType = DocSelectionType.RANDOM,
    limit: int = 15,
    max_tokens: int = MAX_TOKEN_COUNT,
    chunk_size: int = MIN_CHUNK_SIZE,
    language: str | None = None,
    skip_entity_types: bool = False,
    output: str = "prompts",
    n_subset_max: int = 300,
    k: int = 15,
    min_examples_required: int = 2,
):
    """
    执行提示词微调。

    读取配置和文档,生成三种类型的提示词,并将其保存到输出目录。

    Prompt tune the model.

    参数 Parameters
    ----------
    - config: 配置文件路径。The configuration file.
    - root: 根目录路径。The root directory.
    - domain: 输入文档映射到的领域。The domain to map the input documents to.
    - selection_method: 文档块选��方法。默认:RANDOM。The chunk selection method.
    - limit: 要加载的文档块数量限制。默认:15。The limit of chunks to load.
    - max_tokens: 实体抽取提示词的最大 token 数。默认:8000。The maximum number of tokens to use on entity extraction prompts.
    - chunk_size: 使用的分块 token 大小。默认:200。The chunk token size to use.
    - language: 提示词使用的语言。如果为 None,将自动检测。The language to use for the prompts.
    - skip_entity_types: 是否跳过生成实体类型。默认:False。Skip generating entity types.
    - output: 存储提示词的输出文件夹。默认:'prompts'。The output folder to store the prompts.
    - n_subset_max: 使用自动选择方法时要嵌入的文本块数量。默认:300。The number of text chunks to embed when using auto selection method.
    - k: 使用自动选择方法时要选择的文档数量。默认:15。The number of documents to select when using auto selection method.
    - min_examples_required: 实体抽取提示词所需的最小示例数。默认:2。The minimum number of examples required for entity extraction prompts.
    """
    reporter = PrintProgressReporter("")

    # 读取配置参数
    # Read configuration parameters
    graph_config = read_config_parameters(root, reporter, config)

    # 调用 API 生成提示词
    # Call API to generate prompts
    prompts = await api.generate_indexing_prompts(
        config=graph_config,
        root=root,
        chunk_size=chunk_size,
        limit=limit,
        selection_method=selection_method,
        domain=domain,
        language=language,
        max_tokens=max_tokens,
        skip_entity_types=skip_entity_types,
        min_examples_required=min_examples_required,
        n_subset_max=n_subset_max,
        k=k,
    )

    # 创建输出目录并写入提示词文件
    # Create output directory and write prompt files
    output_path = Path(root) / output
    if output_path:
        reporter.info(f"Writing prompts to {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)
        entity_extraction_prompt_path = output_path / ENTITY_EXTRACTION_FILENAME
        entity_summarization_prompt_path = output_path / ENTITY_SUMMARIZATION_FILENAME
        community_summarization_prompt_path = (
            output_path / COMMUNITY_SUMMARIZATION_FILENAME
        )
        # 写入文件到输出路径
        # Write files to output path
        with entity_extraction_prompt_path.open("wb") as file:
            file.write(prompts[0].encode(encoding="utf-8", errors="strict"))
        with entity_summarization_prompt_path.open("wb") as file:
            file.write(prompts[1].encode(encoding="utf-8", errors="strict"))
        with community_summarization_prompt_path.open("wb") as file:
            file.write(prompts[2].encode(encoding="utf-8", errors="strict"))
