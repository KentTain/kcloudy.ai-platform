"""查询引擎包的入口模块。

The Query Engine package root.
"""

import argparse
from enum import Enum

from ai.components.graphrag.query.cli import run_global_search, run_local_search

# 无效方法错误信息
# Invalid method error message
INVALID_METHOD_ERROR = "Invalid method"


class SearchType(Enum):
    """
    检索类型枚举。

    Search type enumeration.
    """

    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        """
        返回枚举值的字符串表示。

        Return the string representation of the enum value.
        """
        return self.value


def run_search():
    """
    运行查询搜索命令行入口。

    Run query search command line entry point.
    """
    # 创建命令行参数解析器
    # Create command line argument parser
    parser = argparse.ArgumentParser(
        prog="python -m graphrag.query",
        description="The graphrag query engine",
    )

    # 配置文件参数
    # Configuration file parameter
    parser.add_argument(
        "--config",
        help="The configuration yaml file to use when running the query",
        required=False,
        type=str,
    )

    # 数据目录参数
    # Data directory parameter
    parser.add_argument(
        "--data",
        help="The path with the output data from the pipeline",
        required=False,
        type=str,
    )

    # 项目根目录参数
    # Project root directory parameter
    parser.add_argument(
        "--root",
        help="The data project root. Default value: the current directory",
        required=False,
        default=".",
        type=str,
    )

    # 搜索方法参数(必填)
    # Search method parameter (required)
    parser.add_argument(
        "--method",
        help="The method to run",
        required=True,
        type=SearchType,
        choices=list(SearchType),
    )

    # 社区层级参数
    # Community level parameter
    parser.add_argument(
        "--community_level",
        help="Community level in the Leiden community hierarchy from which we will load the community reports higher value means we use reports on smaller communities. Default: 2",
        type=int,
        default=2,
    )

    # 响应类型参数
    # Response type parameter
    parser.add_argument(
        "--response_type",
        help="Free form text describing the response type and format, can be anything, e.g. 多段落，markdown格式, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. Default: Multiple Paragraphs",
        type=str,
        default="多段落，markdown格式",
    )

    # 查询内容参数(必填)
    # Query content parameter (required)
    parser.add_argument(
        "query",
        nargs=1,
        help="The query to run",
        type=str,
    )

    # 解析命令行参数
    # Parse command line arguments
    args = parser.parse_args()

    # 根据搜索方法类型执行相应的搜索
    # Execute corresponding search based on search method type
    match args.method:
        case SearchType.LOCAL:
            run_local_search(
                args.config,
                args.data,
                args.root,
                args.community_level,
                args.response_type,
                args.query[0],
            )
        case SearchType.GLOBAL:
            run_global_search(
                args.config,
                args.data,
                args.root,
                args.community_level,
                args.response_type,
                args.query[0],
            )
        case _:
            raise ValueError(INVALID_METHOD_ERROR)


if __name__ == "__main__":
    run_search()
