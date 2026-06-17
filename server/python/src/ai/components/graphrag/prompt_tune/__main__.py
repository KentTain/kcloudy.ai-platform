"""自动模板生成包的根模块。

The auto templating package root.
"""

import argparse
import asyncio

from ai.components.graphrag.prompt_tune.api import DocSelectionType
from ai.components.graphrag.prompt_tune.cli import prompt_tune
from ai.components.graphrag.prompt_tune.generator import MAX_TOKEN_COUNT
from ai.components.graphrag.prompt_tune.loader import MIN_CHUNK_SIZE


def run_prompt_tune():
    """
    运行提示词微调命令行工具。

    解析命令行参数并执行提示词自动生成流程。

    Run the prompt tuning command-line tool.
    """
    parser = argparse.ArgumentParser(
        prog="python -m graphrag.prompt_tune",
        description="The graphrag auto templating module.",
    )

    parser.add_argument(
        "--config",
        help="生成提示词时使用的配置 YAML 文件。Configuration yaml file to use when generating prompts",
        required=False,
        type=str,
    )

    parser.add_argument(
        "--root",
        help="数据项目根目录。默认：当前目录。Data project root. Default: current directory",
        required=False,
        type=str,
        default=".",
    )

    parser.add_argument(
        "--domain",
        help="输入数据相关的领域。例如 'space science'、'microbiology'、'environmental news'。如果未定义，将从输入数据推断领域。Domain your input data is related to. For example 'space science', 'microbiology', 'environmental news'. If not defined, the domain will be inferred from the input data.",
        required=False,
        default="",
        type=str,
    )

    parser.add_argument(
        "--selection-method",
        help=f"文档块选择方法。默认：{DocSelectionType.RANDOM}。Chunk selection method. Default: {DocSelectionType.RANDOM}",
        required=False,
        type=DocSelectionType,
        choices=list(DocSelectionType),
        default=DocSelectionType.RANDOM,
    )

    parser.add_argument(
        "--n_subset_max",
        help="使用自动选择方法时要嵌入的文本块数量。默认：300。Number of text chunks to embed when using auto selection method. Default: 300",
        required=False,
        type=int,
        default=300,
    )

    parser.add_argument(
        "--k",
        help="使用自动选择方法时从每个聚类中心选择的最大文档数。默认：15。Maximum number of documents to select from each centroid when using auto selection method. Default: 15",
        required=False,
        type=int,
        default=15,
    )

    parser.add_argument(
        "--limit",
        help="执行随机或排名选择时要加载的文档数量。默认：15。Number of documents to load when doing random or top selection. Default: 15",
        type=int,
        required=False,
        default=15,
    )

    parser.add_argument(
        "--max-tokens",
        help=f"提示词生成的最大 token 数。默认：{MAX_TOKEN_COUNT}。Max token count for prompt generation. Default: {MAX_TOKEN_COUNT}",
        type=int,
        required=False,
        default=MAX_TOKEN_COUNT,
    )

    parser.add_argument(
        "--min-examples-required",
        help="实体抽取提示词中所需的最小示例数。默认：2。Minimum number of examples required in the entity extraction prompt. Default: 2",
        type=int,
        required=False,
        default=2,
    )

    parser.add_argument(
        "--chunk-size",
        help=f"提示词生成的最大 token 数。默认：{MIN_CHUNK_SIZE}。Max token count for prompt generation. Default: {MIN_CHUNK_SIZE}",
        type=int,
        required=False,
        default=MIN_CHUNK_SIZE,
    )

    parser.add_argument(
        "--language",
        help="GraphRAG 输入和输出使用的主要语言。Primary language used for inputs and outputs on GraphRAG",
        type=str,
        required=False,
        default="",
    )

    parser.add_argument(
        "--no-entity-types",
        help="使用无类型的实体抽取生成。Use untyped entity extraction generation",
        action="store_true",
        required=False,
        default=False,
    )

    parser.add_argument(
        "--output",
        help="保存生成的提示词的目录。默认：'prompts'。Directory to save generated prompts to. Default: 'prompts'",
        type=str,
        required=False,
        default="prompts",
    )

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        prompt_tune(
            config=args.config,
            root=args.root,
            domain=args.domain,
            selection_method=args.selection_method,
            limit=args.limit,
            max_tokens=args.max_tokens,
            chunk_size=args.chunk_size,
            language=args.language,
            skip_entity_types=args.no_entity_types,
            output=args.output,
            n_subset_max=args.n_subset_max,
            k=args.k,
            min_examples_required=args.min_examples_required,
        )
    )


if __name__ == "__main__":
    run_prompt_tune()
