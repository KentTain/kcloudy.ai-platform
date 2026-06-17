"""查询模块的命令行接口。

Command line interface for the query module.
"""

import asyncio
import re
from pathlib import Path
from typing import cast

import pandas as pd

from ai.components.graphrag.config import (
    GraphRagConfig,
    create_graphrag_config,
)
from ai.components.graphrag.index.progress import PrintProgressReporter
from ai.components.graphrag.query import api

# 进度报告器实例
# Progress reporter instance
reporter = PrintProgressReporter("")


def run_global_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """
    使用给定查询执行全局搜索。

    加载全局搜索所需的索引文件并调用查询 API。

    Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.

    参数 Parameters
    ----------
    - config_dir: 配置文件目录。Configuration file directory
    - data_dir: 数据目录。Data directory
    - root_dir: 项目根目录。Project root directory
    - community_level: 社区层级。Community level
    - response_type: 响应类型。Response type
    - query: 查询内容。Query content
    """
    # 配置路径和设置
    # Configure paths and settings
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    # 读取全局搜索所需的索引文件
    # Read index files required for global search
    final_nodes: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_nodes.parquet"
    )
    final_entities: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_entities.parquet"
    )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )

    # 调用全局搜索 API
    # Call global search API
    return asyncio.run(
        api.global_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    )


def _configure_vector_store_uri(config: GraphRagConfig, data_path: Path):
    """
    配置向量存储 URI。

    如果未配置向量存储 uri,则在数据目录中创建 lancedb 数据库。

    Configure vector store URI.
    If vector store uri is not configured, create lancedb database in data directory.

    参数 Parameters
    ----------
    - config: GraphRAG 配置对象。GraphRAG configuration object
    - data_path: 数据路径。Data path
    """
    # 获取向量存储配置参数
    # Get vector store configuration parameters
    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )
    config.embeddings.vector_store = vector_store_args

    # 如果未配置 db_uri,则设置默认值
    # If db_uri is not configured, set default value
    if vector_store_args.get("db_uri", None) is None:
        lancedb_store_path = data_path.parent
        vector_store_args.update(
            {
                "db_uri": f"{lancedb_store_path}/lancedb",
            }
        )


def run_local_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """
    使用给定查询执行本地搜索。

    加载本地搜索所需的索引文件并调用查询 API。

    Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.

    参数 Parameters
    ----------
    - config_dir: 配置文件目录。Configuration file directory
    - data_dir: 数据目录。Data directory
    - root_dir: 项目根目录。Project root directory
    - community_level: 社区层级。Community level
    - response_type: 响应类型。Response type
    - query: 查询内容。Query content
    """
    # 配置路径和设置
    # Configure paths and settings
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    # 配置向量存储 URI
    # Configure vector store URI
    _configure_vector_store_uri(config, data_path)

    # 读取本地搜索所需的索引文件
    # Read index files required for local search
    final_nodes = pd.read_parquet(data_path / "create_final_nodes.parquet")
    final_community_reports = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )
    final_text_units = pd.read_parquet(data_path / "create_final_text_units.parquet")
    final_relationships = pd.read_parquet(
        data_path / "create_final_relationships.parquet"
    )
    final_entities = pd.read_parquet(data_path / "create_final_entities.parquet")
    final_covariates_path = data_path / "create_final_covariates.parquet"
    # 读取协变量(如果文件存在)
    # Read covariates (if file exists)
    final_covariates = (
        pd.read_parquet(final_covariates_path)
        if final_covariates_path.exists()
        else None
    )

    # 调用本地搜索 API
    # Call local search API
    return asyncio.run(
        api.local_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    )


def _configure_paths_and_settings(
    data_dir: str | None,
    root_dir: str | None,
    config_dir: str | None,
) -> tuple[str, str | None, GraphRagConfig]:
    """
    配置路径和设置。

    Configure paths and settings.

    参数 Parameters
    ----------
    - data_dir: 数据目录。Data directory
    - root_dir: 项目根目录。Project root directory
    - config_dir: 配置文件目录。Configuration file directory

    返回 Returns
    -------
    - tuple[str, str | None, GraphRagConfig]: 数据目录,根目录和配置对象。Data directory, root directory and configuration object

    异常 Raises
    ------
    - ValueError: 如果 data_dir 和 root_dir 都未提供。If both data_dir and root_dir are not provided
    """
    # 检查必须提供 data_dir 或 root_dir 之一
    # Check that either data_dir or root_dir must be provided
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)

    # 如果未提供 data_dir,则从 root_dir 推断
    # If data_dir is not provided, infer from root_dir
    if data_dir is None:
        data_dir = _infer_data_dir(cast("str", root_dir))

    # 创建 GraphRAG 配置
    # Create GraphRAG configuration
    config = _create_graphrag_config(root_dir, config_dir)

    reporter.info(f"ROOT_DIR : {root_dir}")
    reporter.info(f"DATA_DIR : {data_dir}")

    return data_dir, root_dir, config


def _infer_data_dir(root: str) -> str:
    """
    从根目录推断数据目录。

    Infer data directory from root directory.

    参数 Parameters
    ----------
    - root: 项目根目录。Project root directory

    返回 Returns
    -------
    - str: 数据目录路径。Data directory path

    异常 Raises
    ------
    - ValueError: 如果无法推断数据目录。If data directory cannot be inferred
    """
    output = Path(root) / "output"
    # 使用最新的 data-run 文件夹
    # Use the latest data-run folder
    if output.exists():
        # 匹配日期时间格式的文件夹名称
        # Match folder names with datetime format
        expr = re.compile(r"\d{8}-\d{6}")
        filtered = [f for f in output.iterdir() if f.is_dir() and expr.match(f.name)]
        # 按名称倒序排序,获取最新的文件夹
        # Sort by name in descending order to get the latest folder
        folders = sorted(filtered, key=lambda f: f.name, reverse=True)
        if len(folders) > 0:
            folder = folders[0]
            return str((folder / "artifacts").absolute())

    msg = f"Could not infer data directory from root={root}"
    raise ValueError(msg)


def _create_graphrag_config(
    root: str | None,
    config_dir: str | None,
) -> GraphRagConfig:
    """
    创建 GraphRAG 配置。

    Create a GraphRag configuration.

    参数 Parameters
    ----------
    - root: 项目根目录。Project root directory
    - config_dir: 配置文件目录。Configuration file directory

    返回 Returns
    -------
    - GraphRagConfig: GraphRAG 配置对象。GraphRAG configuration object
    """
    return _read_config_parameters(root or "./", config_dir)


def _read_config_parameters(root: str, config: str | None):
    """
    读取配置参数。

    Read configuration parameters.

    参数 Parameters
    ----------
    - root: 项目根目录。Project root directory
    - config: 配置文件路径。Configuration file path

    返回 Returns
    -------
    - GraphRagConfig: GraphRAG 配置对象。GraphRAG configuration object
    """
    _root = Path(root)

    # 尝试读取 YAML 配置文件
    # Try to read YAML configuration file
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open(
            "rb",
        ) as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    # 尝试读取 JSON 配置文件
    # Try to read JSON configuration file
    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )
    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    # 如果没有配置文件,从环境变量读取配置
    # If no configuration file, read configuration from environment variables
    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
