"""GraphRAG 搜索服务模块。

GraphRAG search service module.

此模块提供本地搜索和全局搜索功能,用于在知识图谱中检索信息。
This module provides local and global search functionality for retrieving information from knowledge graphs.

Command line interface for the query module.
"""

import os
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
from ai.components.graphrag.webserver.utils.consts import RAGCONFIG_PATH
from ai.components.graphrag.webserver.utils.rag_util import build_root_path

reporter = PrintProgressReporter("")


async def run_global_search(
    namespace: str,
    code: str,
    filename: str,
    community_level: int,
    response_type: str,
    query: str,
):
    """
    执行全局搜索。

    Perform a global search with a given query.

    加载全局搜索所需的索引文件并调用查询 API。
    Loads index files required for global search and calls the Query API.

    参数 Parameters
    ----------
    namespace : str
        命名空间。Namespace.
    code : str
        代码标识。Code identifier.
    filename : str
        文件名。Filename.
    community_level : int
        社区层级。Community level.
    response_type : str
        响应类型。Response type.
    query : str
        查询问题。Query question.

    返回 Returns
    -------
    SearchResult
        搜索结果。Search result.
    """
    from io import BytesIO

    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    root_dir = build_root_path(namespace, code, filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")
    config_dir = RAGCONFIG_PATH

    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )

    final_nodes: pd.DataFrame = pd.read_parquet(
        BytesIO(storage.get("create_final_nodes.parquet", as_bytes=True))  # type: ignore
    )
    final_entities: pd.DataFrame = pd.read_parquet(
        BytesIO(storage.get("create_final_entities.parquet", as_bytes=True))  # type: ignore
    )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        BytesIO(storage.get("create_final_community_reports.parquet", as_bytes=True))  # type: ignore
    )

    return await api.global_search(
        config=config,
        nodes=final_nodes,
        entities=final_entities,
        community_reports=final_community_reports,
        community_level=community_level,
        response_type=response_type,
        query=query,
    )


def _configure_vector_store_uri(config: GraphRagConfig, data_path: Path):
    """
    配置向量存储 URI。

    Configure vector store URI.

    如果未配置向量存储 uri,则在数据目录中创建 lancedb 数据库。
    If vector store uri is not configured, create lancedb database in data directory.

    参数 Parameters
    ----------
    config : GraphRagConfig
        GraphRAG 配置对象。GraphRAG configuration object.
    data_path : Path
        数据路径。Data path.
    """
    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )
    config.embeddings.vector_store = vector_store_args

    if vector_store_args.get("db_uri", None) is None:
        lancedb_store_path = data_path.parent
        vector_store_args.update(
            {
                "db_uri": f"{lancedb_store_path}/lancedb",
            }
        )


async def run_local_search(
    namespace: str,
    code: str,
    filename: str,
    community_level: int,
    response_type: str,
    query: str,
    min_score: float,
):
    """
    执行本地搜索。

    Perform a local search with a given query.

    加载本地搜索所需的索引文件并调用查询 API。
    Loads index files required for local search and calls the Query API.

    参数 Parameters
    ----------
    namespace : str
        命名空间。Namespace.
    code : str
        代码标识。Code identifier.
    filename : str
        文件名。Filename.
    community_level : int
        社区层级。Community level.
    response_type : str
        响应类型。Response type.
    query : str
        查询问题。Query question.
    min_score : float
        最低相关性分数。Minimum relevance score.

    返回 Returns
    -------
    SearchResult
        搜索结果。Search result.
    """
    from io import BytesIO

    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    root_dir = build_root_path(namespace, code, filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")
    config_dir = RAGCONFIG_PATH

    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    # 配置向量存储 URI / Configure vector store URI
    _configure_vector_store_uri(config, data_path)

    final_nodes = pd.read_parquet(
        BytesIO(storage.get("create_final_nodes.parquet", as_bytes=True))  # type: ignore
    )

    final_community_reports = pd.read_parquet(
        BytesIO(storage.get("create_final_community_reports.parquet", as_bytes=True))  # type: ignore
    )
    final_text_units = pd.read_parquet(
        BytesIO(storage.get("create_final_text_units.parquet", as_bytes=True))  # type: ignore
    )
    final_relationships = pd.read_parquet(
        BytesIO(storage.get("create_final_relationships.parquet", as_bytes=True))  # type: ignore
    )
    final_entities = pd.read_parquet(
        BytesIO(storage.get("create_final_entities.parquet", as_bytes=True))  # type: ignore
    )

    if storage.exists("create_final_covariates.parquet"):
        final_covariates = pd.read_parquet(
            BytesIO(storage.get("create_final_covariates.parquet", as_bytes=True))  # type: ignore
        )
    else:
        final_covariates = None

    # 调用查询 API / Call the Query API
    return await api.local_search(
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
        min_score=min_score,
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
    data_dir : str | None
        数据目录路径。Data directory path.
    root_dir : str | None
        根目录路径。Root directory path.
    config_dir : str | None
        配置目录路径。Configuration directory path.

    返回 Returns
    -------
    tuple[str, str | None, GraphRagConfig]
        数据目录,根目录和配置对象。Data directory, root directory and configuration object.
    """
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)
    if data_dir is None:
        data_dir = _infer_data_dir(cast("str", root_dir))
    config = _create_graphrag_config(root_dir, config_dir)

    reporter.info(f"ROOT_DIR : {root_dir}")
    reporter.info(f"DATA_DIR : {data_dir}")

    return data_dir, root_dir, config


def _infer_data_dir(root: str) -> str:
    """
    从根目录推断数据目录路径。

    Infer data directory path from root directory.

    参数 Parameters
    ----------
    root : str
        根目录路径。Root directory path.

    返回 Returns
    -------
    str
        数据目录路径。Data directory path.
    """
    output = Path(root) / "output"
    # 使用最新的 data-run 文件夹 / Use the latest data-run folder
    if output.exists():
        expr = re.compile(r"\d{8}-\d{6}")
        filtered = [f for f in output.iterdir() if f.is_dir() and expr.match(f.name)]
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
    创建 GraphRAG 配置对象。

    Create a GraphRag configuration.

    参数 Parameters
    ----------
    root : str | None
        根目录路径。Root directory path.
    config_dir : str | None
        配置目录路径。Configuration directory path.

    返回 Returns
    -------
    GraphRagConfig
        GraphRAG 配置对象。GraphRAG configuration object.
    """
    return _read_config_parameters(root or "./", config_dir)


def _read_config_parameters(root: str, config: str | None):
    """
    读取配置参数。

    Read configuration parameters.

    参数 Parameters
    ----------
    root : str
        根目录路径。Root directory path.
    config : str | None
        配置文件路径。Configuration file path.

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

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open(
            "rb",
        ) as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

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

    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
