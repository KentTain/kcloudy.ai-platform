"""索引引擎包的根目录."""

import argparse

from ai.components.graphrag.index.cli import index_cli


def run_index():
    """执行index。"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        help="运行流水线时使用的配置yaml文件",
        required=False,
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="以详细日志模式运行流水线",
        action="store_true",
    )
    parser.add_argument(
        "--memprofile",
        help="以内存分析模式运行流水线",
        action="store_true",
    )
    parser.add_argument(
        "--root",
        help="如果未定义配置，用于输入数据和输出数据的根目录。默认值：当前目录",
        # 仅在未定义配置时需要
        required=False,
        default=".",
        type=str,
    )
    parser.add_argument(
        "--resume",
        help="利用Parquet输出文件恢复给定的数据运行。",
        # 仅在未定义配置时需要
        required=False,
        default=None,
        type=str,
    )
    parser.add_argument(
        "--reporter",
        help="要使用的进度报告器。有效值为'rich'、'print'或'none'",
        type=str,
    )
    parser.add_argument(
        "--emit",
        help="要输出的数据格式，逗号分隔。有效值为'parquet'和'csv'。默认值='parquet,csv'",
        type=str,
    )
    parser.add_argument(
        "--dryrun",
        help="运行流水线但不实际执行任何步骤，仅检查配置。",
        action="store_true",
    )
    parser.add_argument("--nocache", help="禁用LLM缓存。", action="store_true")
    parser.add_argument(
        "--init",
        help="在给定路径中创建初始配置。",
        action="store_true",
    )
    parser.add_argument(
        "--overlay-defaults",
        help="在提供的配置文件（--config）上覆盖默认配置值。",
        action="store_true",
    )
    args = parser.parse_args()

    if args.overlay_defaults and not args.config:
        parser.error("--overlay-defaults requires --config")

    index_cli(
        root=args.root,
        verbose=args.verbose or False,
        resume=args.resume,
        memprofile=args.memprofile or False,
        nocache=args.nocache or False,
        reporter=args.reporter,
        config=args.config,
        emit=args.emit,
        dryrun=args.dryrun or False,
        init=args.init or False,
        overlay_defaults=args.overlay_defaults or False,
        cli=True,
    )


if __name__ == "__main__":
    run_index()
