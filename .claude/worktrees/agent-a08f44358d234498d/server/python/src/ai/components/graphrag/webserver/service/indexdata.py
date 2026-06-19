"""GraphRAG 索引数据管理服务模块。

GraphRAG index data management service module.

此模块提供索引数据的 CRUD 操作,包括实体,关系,报告和声明的管理。
This module provides CRUD operations for index data, including management of entities, relationships, reports and claims.
"""

import math
import os
import shutil
import uuid
from io import BytesIO

import networkx as nx
import pandas as pd

from ai.components.graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from ai.components.graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from ai.components.graphrag.webserver.gtypes.chat_request import IndexData
from ai.components.graphrag.webserver.utils import consts


async def get_index_data(
    namespace: str, code: str, filename: str, datatype: str, row_id: str | None = None
):
    """
    获取索引数据。

    Get index data.

    参数 Parameters
    ----------
    namespace : str
        命名空间。Namespace.
    code : str
        代码标识。Code identifier.
    filename : str
        文件名。Filename.
    datatype : str
        数据类型:entities, claims, sources, reports, relationships。Data type.
    row_id : str | None, optional
        行 ID。Row ID.

    返回 Returns
    -------
    list
        索引数据列表。Index data list.
    """
    if datatype == "entities":
        return await get_entity(namespace, code, filename, row_id)
    if datatype == "claims":
        return await get_claim(namespace, code, filename, row_id)
    if datatype == "sources":
        return await get_source(namespace, code, filename, row_id)
    if datatype == "reports":
        return await get_report(namespace, code, filename, row_id)
    if datatype == "relationships":
        return await get_relationship(namespace, code, filename, row_id)
    raise ValueError(f"Unknown datatype: {datatype}")


async def get_entity(
    namespace: str, code: str, filename: str, row_id: str | None = None
) -> list[Entity]:
    """
    获取实体数据。

    Get entity data.

    参数 Parameters
    ----------
    namespace : str
        命名空间。Namespace.
    code : str
        代码标识。Code identifier.
    filename : str
        文件名。Filename.
    row_id : str | None, optional
        行 ID。Row ID.

    返回 Returns
    -------
    list[Entity]
        实体列表。Entity list.
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    entity_df = pd.read_parquet(
        BytesIO(storage.get(filename=f"{consts.ENTITY_TABLE}.parquet", as_bytes=True))
    )  # type: ignore
    entity_embedding_df = pd.read_parquet(
        BytesIO(
            storage.get(
                filename=f"{consts.ENTITY_EMBEDDING_TABLE}.parquet", as_bytes=True
            )
        )
    )  # type: ignore

    entities = read_indexer_entities(
        entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL
    )

    ignore_filed(
        ["description_embedding", "name_embedding", "graph_embedding"], entities
    )
    filter_ids(["community_ids", "text_unit_ids", "document_ids"], entities)

    if row_id is None:
        return entities

    results = []
    row_ids = row_id.split(",")

    for entity in entities:
        if entity.id in row_ids or entity.short_id in row_ids:
            results.append(entity)

    return results


def filter_ids(field: list[str], objs: list[any]):
    """
    过滤关联 ID,移除值为 "-1" 的 ID。

    Filter associated IDs, removing IDs with value "-1".

    有些关联的 IDs 是 "-1",需要过滤掉,不然前端统计不准确。
    Some associated IDs are "-1" and need to be filtered out, otherwise frontend statistics are inaccurate.

    参数 Parameters
    ----------
    field : list[str]
        字段名列表。Field name list.
    objs : list[any]
        对象列表。Object list.
    """
    for obj in objs:
        for f in field:
            ids = getattr(obj, f)
            if ids is not None and "-1" in ids:
                setattr(obj, f, [i for i in ids if i != "-1"])


def ignore_filed(field: list[str], obj: any):
    """
    忽略指定字段,用于减少索引数据的大小。

    Ignore specified fields to reduce index data size.

    参数 Parameters
    ----------
    field : list[str]
        要忽略的字段名列表。Field names to ignore.
    obj : any
        对象或对象列表。Object or object list.

    返回 Returns
    -------
    any
        处理后的对象。Processed object.
    """
    # 如果是数组 / If it's an array
    if isinstance(obj, list):
        result = []
        for e in obj:
            ignore_filed(field, e)
            result.append(e)

        return result
    for f in field:
        setattr(obj, f, None)
    return obj


async def get_claim(
    namespace: str, code: str, filename: str, row_id: str | None = None
) -> list[Covariate]:
    """
    获取claim。

    Args:
        namespace (str): namespace 参数。
        code (str): code 参数。
        filename (str): filename 参数。
        row_id (str | None): row_id 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    if storage.exists(filename=f"{consts.COVARIATE_TABLE}.parquet"):
        covariate_df = pd.read_parquet(
            BytesIO(
                storage.get(filename=f"{consts.COVARIATE_TABLE}.parquet", as_bytes=True)
            )
        )  # type: ignore
        claims = read_indexer_covariates(covariate_df)
    else:
        raise ValueError("No claims found")

    if row_id is None:
        return claims

    results = []
    row_ids = row_id.split(",")

    for claim in claims:
        if claim.id in row_ids or claim.short_id in row_ids:
            results.append(claim)

    return results


async def get_source(
    namespace: str, code: str, filename: str, row_id: str | None = None
) -> list[TextUnit]:
    """
    获取source。

    Args:
        namespace (str): namespace 参数。
        code (str): code 参数。
        filename (str): filename 参数。
        row_id (str | None): row_id 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    text_unit_df = pd.read_parquet(
        BytesIO(
            storage.get(filename=f"{consts.TEXT_UNIT_TABLE}.parquet", as_bytes=True)
        )
    )  # type: ignore
    text_units = read_indexer_text_units(text_unit_df)

    ignore_filed(["text_embedding"], text_units)
    filter_ids(
        ["entity_ids", "relationship_ids", "covariate_ids", "document_ids"], text_units
    )

    if row_id is None:
        return text_units

    results = []
    row_ids = row_id.split(",")

    for text_unit in text_units:
        if text_unit.id in row_ids or text_unit.short_id in row_ids:
            results.append(text_unit)

    return results


async def get_report(
    namespace: str, code: str, filename: str, row_id: str | None = None
) -> list[CommunityReport]:
    """
    获取report。

    Args:
        namespace (str): namespace 参数。
        code (str): code 参数。
        filename (str): filename 参数。
        row_id (str | None): row_id 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    entity_df = pd.read_parquet(
        BytesIO(storage.get(filename=f"{consts.ENTITY_TABLE}.parquet", as_bytes=True))
    )  # type: ignore
    report_df = pd.read_parquet(
        BytesIO(
            storage.get(
                filename=f"{consts.COMMUNITY_REPORT_TABLE}.parquet", as_bytes=True
            )
        )
    )  # type: ignore
    reports = read_indexer_reports(report_df, entity_df, consts.COMMUNITY_LEVEL)

    ignore_filed(["summary_embedding", "full_content_embedding"], reports)

    if row_id is None:
        return reports

    results = []
    row_ids = row_id.split(",")

    for report in reports:
        if report.id in row_ids or report.short_id in row_ids:
            results.append(report)

    return results


async def get_relationship(
    namespace: str, code: str, filename: str, row_id: str | None = None
) -> list[Relationship]:
    """
    获取relationship。

    Args:
        namespace (str): namespace 参数。
        code (str): code 参数。
        filename (str): filename 参数。
        row_id (str | None): row_id 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(namespace, code, filename, ConfigType.storage)

    relationship_df = pd.read_parquet(
        BytesIO(
            storage.get(filename=f"{consts.RELATIONSHIP_TABLE}.parquet", as_bytes=True)
        )
    )  # type: ignore
    relationships = read_indexer_relationships(relationship_df)

    ignore_filed(["description_embedding"], relationships)
    filter_ids(["text_unit_ids", "document_ids"], relationships)

    if row_id is None:
        return relationships

    results = []
    row_ids = row_id.split(",")

    for relationship in relationships:
        if relationship.id in row_ids or relationship.short_id in row_ids:
            results.append(relationship)

    return results


async def index_data_add(
    input_dir: str, datatype: str, indexdata: IndexData.Data
) -> str:
    """
    添加索引数据。

    Add index data.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    datatype : str
        数据类型。Data type.
    indexdata : IndexData.Data
        索引数据对象。Index data object.

    返回 Returns
    -------
    str
        操作结果。Operation result.
    """
    filename = ""
    if datatype == "entities":
        filename = consts.ENTITY_TABLE
    elif datatype == "reports":
        filename = consts.COMMUNITY_REPORT_TABLE
    elif datatype == "relationships":
        filename = consts.RELATIONSHIP_TABLE
    else:
        raise ValueError(f"Unknown datatype: {datatype}")

    return await save_entity(input_dir, indexdata, filename)


async def index_data_update(
    input_dir: str, datatype: str, indexdata: IndexData.Data
) -> str:
    """
    更新索引数据。

    Update index data.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    datatype : str
        数据类型。Data type.
    indexdata : IndexData.Data
        索引数据对象。Index data object.

    返回 Returns
    -------
    str
        操作结果。Operation result.
    """
    filename = ""
    if datatype == "entities":
        filename = consts.ENTITY_TABLE
    elif datatype == "reports":
        filename = consts.COMMUNITY_REPORT_TABLE
    elif datatype == "relationships":
        filename = consts.RELATIONSHIP_TABLE
    else:
        raise ValueError(f"Unknown datatype: {datatype}")

    return await update_entity(input_dir, indexdata, filename)


async def index_data_delete(
    input_dir: str, datatype: str, indexdata: IndexData.Data
) -> str:
    """
    删除索引数据。

    Delete index data.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    datatype : str
        数据类型。Data type.
    indexdata : IndexData.Data
        索引数据对象。Index data object.

    返回 Returns
    -------
    str
        操作结果。Operation result.
    """
    filename = ""
    if datatype == "entities":
        filename = consts.ENTITY_TABLE
    elif datatype == "reports":
        filename = consts.COMMUNITY_REPORT_TABLE
    elif datatype == "relationships":
        filename = consts.RELATIONSHIP_TABLE
    else:
        raise ValueError(f"Unknown datatype: {datatype}")

    return await delete_entity(input_dir, indexdata, filename)


async def index_data_get_by_id(
    input_dir: str, datatype: str, indexdata: IndexData.Data
) -> str:
    """
    处理index_data_id。

    Args:
        input_dir (str): input_dir 参数。
        datatype (str): datatype 参数。
        indexdata (IndexData.Data): indexdata 参数。

    Returns:
        处理结果。
    """
    filename = ""
    if datatype == "entities":
        filename = consts.ENTITY_TABLE
    elif datatype == "reports":
        filename = consts.COMMUNITY_REPORT_TABLE
    elif datatype == "relationships":
        filename = consts.RELATIONSHIP_TABLE
    else:
        raise ValueError(f"Unknown datatype: {datatype}")

    return await get_entity_by_id(input_dir, indexdata.id, filename)


async def save_entity(
    input_dir: str, indexdata: IndexData.Data, filename: str
) -> list[Entity]:
    """
    保存实体数据到 Parquet 文件。

    Save entity data to Parquet file.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    indexdata : IndexData.Data
        索引数据对象。Index data object.
    filename : str
        文件名。Filename.

    返回 Returns
    -------
    list[Entity]
        操作结果。Operation result.
    """
    # 生成 id / Generate id
    id = str(uuid.uuid4().hex)
    # 生成时间戳
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    entity_df = pd.read_parquet(f"{input_dir}/{filename}.parquet")
    # 新增 / Add new data
    # 生成 id / Generate id
    indexdata.id = id
    # custom_add 新增标识为 true / Set custom_add flag to true
    indexdata.custom_add = "true"
    indexdata_without_none = convert_to_dict_without_none(indexdata)
    # 转换数据,将每个字段值转为数组 / Convert data, turn each field value into an array
    indexdata = convert_to_single_element_arrays(indexdata_without_none)
    new_row = pd.DataFrame(indexdata)
    df = pd.concat([entity_df, new_row], ignore_index=True)
    # 将修改后的数据保存为新的 parquet 文件 / Save modified data as new parquet file
    df.to_parquet(f"{input_dir}/{filename}.parquet_temp")

    if filename == consts.ENTITY_TABLE:
        # 如果是实体,create_final_entities 也要新增,查询时候会关联 / If it's an entity, also add to create_final_entities for query association
        entity_df = pd.read_parquet(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet"
        )
        # 新增 / Add new data
        # 删除不需要的字段 / Remove unnecessary fields
        del indexdata["degree"]
        del indexdata["community"]
        # 将 "title" 键改为 "name"
        if "title" in indexdata:
            indexdata["name"] = indexdata.pop("title")
        new_row = pd.DataFrame(indexdata)
        df = pd.concat([entity_df, new_row], ignore_index=True)
        # 将修改后的数据保存为��的 parquet 文件 / Save modified data as new parquet file
        df.to_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp")
        # 将原文件移动到 backups 目录下 / Move original file to backups directory
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
            f"{input_dir}/backups",
            f"{input_dir}/backups/{consts.ENTITY_EMBEDDING_TABLE}.parquet_{timestamp}",
        )
        # 将新生成的文件变回原文件
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp",
            f"{input_dir}/backups",
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
        )
    # 将原文件移动到backups目录下
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet",
        f"{input_dir}/backups",
        f"{input_dir}/backups/{filename}.parquet_{timestamp}",
    )
    # 将新生成的文件变回原文件 / Rename new file to original filename
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet_temp",
        f"{input_dir}/backups",
        f"{input_dir}/{filename}.parquet",
    )
    # 对应图谱内容添加 / Add corresponding graph content
    graph_add(input_dir, indexdata_without_none, filename)

    return "ok"


async def update_entity(
    input_dir: str, indexdata: IndexData.Data, filename: str
) -> list[Entity]:
    # 通过id查出实体信息
    """
    更新entity。

    Args:
        input_dir (str): input_dir 参数。
        indexdata (IndexData.Data): indexdata 参数。
        filename (str): filename 参数。

    Returns:
        处理结果。
    """
    entity = await get_entity_by_id(input_dir, indexdata.id, filename)
    # 生成时间戳
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    entity_df = pd.read_parquet(f"{input_dir}/{filename}.parquet")
    # custom_update修改标识为true
    indexdata.custom_update = "true"
    indexdata_without_none = convert_to_dict_without_none(indexdata)
    indexdata = dict(indexdata_without_none)
    # 使用 loc 更新多个列
    entity_df.loc[entity_df["id"] == indexdata["id"], list(indexdata.keys())] = list(
        indexdata.values()
    )
    # 将修改后的数据保存为新的parquet文件
    entity_df.to_parquet(f"{input_dir}/{filename}.parquet_temp")

    if filename == consts.ENTITY_TABLE:
        # 如果是实体,create_final_entities也要更新,查询时候会关联
        entity_df = pd.read_parquet(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet"
        )

        # 删除不需要的字段
        del indexdata["degree"]
        del indexdata["community"]
        # 将 "title" 键改为 "name"
        if "title" in indexdata:
            indexdata["name"] = indexdata.pop("title")

        # 使用 loc 更新多个列
        entity_df.loc[entity_df["id"] == indexdata["id"], list(indexdata.keys())] = (
            list(indexdata.values())
        )
        # 将修改后的数据保存为新的parquet文件
        entity_df.to_parquet(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp"
        )
        # 将原文件移动到backups目录下
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
            f"{input_dir}/backups",
            f"{input_dir}/backups/{consts.ENTITY_EMBEDDING_TABLE}.parquet_{timestamp}",
        )
        # 将新生成的文件变回原文件
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp",
            f"{input_dir}/backups",
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
        )
    # 将原文件移动到backups目录下
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet",
        f"{input_dir}/backups",
        f"{input_dir}/backups/{filename}.parquet_{timestamp}",
    )
    # 将新生成的文件变回原文件
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet_temp",
        f"{input_dir}/backups",
        f"{input_dir}/{filename}.parquet",
    )
    # 对应图谱内容修改
    graph_update(input_dir, indexdata_without_none, filename, entity)

    return "ok"


async def delete_entity(
    input_dir: str, indexdata: IndexData.Data, filename: str
) -> list[Entity]:
    # 通过id查出实体信息
    """
    删除entity。

    Args:
        input_dir (str): input_dir 参数。
        indexdata (IndexData.Data): indexdata 参数。
        filename (str): filename 参数。

    Returns:
        处理结果。
    """
    entity = await get_entity_by_id(input_dir, indexdata.id, filename)
    # 生成时间戳
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    entity_df = pd.read_parquet(f"{input_dir}/{filename}.parquet")
    # 获取要删除的 ID
    id_to_delete = indexdata.id
    # 过滤除所有不为id_to_delete的数据,即为删除id_to_delete的数据
    entity_df = entity_df[entity_df["id"] != id_to_delete]
    # 将删除后的数据保存为新的parquet文件
    entity_df.to_parquet(f"{input_dir}/{filename}.parquet_temp")

    if filename == consts.ENTITY_TABLE:
        # 如果是实体,create_final_entities也要删除,查询时候会关联
        entity_df = pd.read_parquet(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet"
        )
        # 过滤除所有不为id_to_delete的数据,即为删除id_to_delete的数据
        entity_df = entity_df[entity_df["id"] != id_to_delete]
        # 将修改后的数据保存为新的parquet文件
        entity_df.to_parquet(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp"
        )
        # 将原文件移动到backups目录下
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
            f"{input_dir}/backups",
            f"{input_dir}/backups/{consts.ENTITY_EMBEDDING_TABLE}.parquet_{timestamp}",
        )
        # 将新生成的文件变回原文件
        move_file_with_timestamp(
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet_temp",
            f"{input_dir}/backups",
            f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet",
        )
    # 将原文件移动到backups目录下
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet",
        f"{input_dir}/backups",
        f"{input_dir}/backups/{filename}.parquet_{timestamp}",
    )
    # 将新生成的文件变回原文件
    move_file_with_timestamp(
        f"{input_dir}/{filename}.parquet_temp",
        f"{input_dir}/backups",
        f"{input_dir}/{filename}.parquet",
    )
    # 对应图谱内容删除
    graph_delete(input_dir, entity, filename)

    return "ok"


async def get_entity_by_id(input_dir: str, id: str, filename: str) -> list[Entity]:
    """
    获取entity_id。

    Args:
        input_dir (str): input_dir 参数。
        id (str): id 参数。
        filename (str): filename 参数。

    Returns:
        处理结果。
    """
    entity_df = pd.read_parquet(f"{input_dir}/{filename}.parquet")
    result = entity_df[entity_df["id"] == id]
    result = simplify_result(result.to_dict())
    result = clean_special_floats(result)
    result = preprocess_data(result)
    return result


def preprocess_data(data):
    """
    处理preprocess_data。

    Args:
        data: data 参数。

    Returns:
        处理结果。
    """
    import numpy as np

    if isinstance(data, dict):
        return {k: preprocess_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [preprocess_data(item) for item in data]
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (np.integer, np.floating)):
        return data.item()
    return data


def graph_add(input_dir: str, indexdata: dict, filename: str):
    """
    在图谱中添加节点或边。

    Add node or edge to graph.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    indexdata : dict
        索引数据字典。Index data dictionary.
    filename : str
        文件名。Filename.
    """
    # summarized_graph_path 路径 / Path to summarized_graph_path
    summarized_graph_path = f"{input_dir}/summarized_graph.graphml"
    # 读取 GraphML 文件 / Read GraphML file
    G = nx.read_graphml(summarized_graph_path)
    if filename == consts.ENTITY_TABLE:
        # ��体添加新节点 / Add new node for entity
        G.add_node(
            indexdata["title"],
            description=indexdata["description"],
            type=indexdata["type"],
        )
        # 保存修改后的图 / Save modified graph
        nx.write_graphml(G, summarized_graph_path)
    elif filename == consts.RELATIONSHIP_TABLE:
        # 实体关系添加新边 / Add new edge for relationship
        G.add_edge(
            indexdata["source"],
            indexdata["target"],
            description=indexdata["description"],
        )
        # 保存修改后的图 / Save modified graph
        nx.write_graphml(G, summarized_graph_path)


def graph_update(input_dir: str, indexdata: dict, filename: str, entity: dict):
    """
    在图谱中更新节点或边。

    Update node or edge in graph.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    indexdata : dict
        新的索引数据字典。New index data dictionary.
    filename : str
        文件名。Filename.
    entity : dict
        原实体数据字典。Original entity data dictionary.
    """
    # summarized_graph_path 路径 / Path to summarized_graph_path
    summarized_graph_path = f"{input_dir}/summarized_graph.graphml"
    # 读取 GraphML 文件 / Read GraphML file
    G = nx.read_graphml(summarized_graph_path)
    if filename == consts.ENTITY_TABLE:
        # 实体修改节点 / Update entity node
        # 创建一个映射字典,指定旧节点 id 到新节点 id 的映射 / Create mapping dictionary from old node id to new node id
        title = entity["title"]
        mapping = {title: indexdata["title"]}
        # 使用 relabel_nodes() 方法重命名节点 / Use relabel_nodes() method to rename node
        G = nx.relabel_nodes(G, mapping)
        G.nodes[indexdata["title"]]["description"] = indexdata["description"]
        G.nodes[indexdata["title"]]["type"] = indexdata["type"]
        # 保存修改后的图 / Save modified graph
        nx.write_graphml(G, summarized_graph_path)
    elif filename == consts.RELATIONSHIP_TABLE:
        source = entity["source"]
        target = entity["target"]

        old_edge = (source, target)
        # 如果边存在 / If edge exists
        if G.has_edge(*old_edge):
            # 获取边的属性 / Get edge attributes
            edge_data = G.get_edge_data(*old_edge)
            edge_data["description"] = indexdata["description"]
            # 移除旧的边 / Remove old edge
            G.remove_edge(*old_edge)
            # 添加新的边,并添加属性 / Add new edge with attributes
            G.add_edge(indexdata["source"], indexdata["target"], **edge_data)
            # 保存修改后的图 / Save modified graph
            nx.write_graphml(G, summarized_graph_path)


def graph_delete(input_dir: str, entity: dict, filename: str):
    """
    在图谱中删除节点或边。

    Delete node or edge from graph.

    参数 Parameters
    ----------
    input_dir : str
        输入目录。Input directory.
    entity : dict
        实体数据字典。Entity data dictionary.
    filename : str
        文件名。Filename.
    """
    # summarized_graph_path 路径 / Path to summarized_graph_path
    summarized_graph_path = f"{input_dir}/summarized_graph.graphml"
    # 读取 GraphML 文件 / Read GraphML file
    G = nx.read_graphml(summarized_graph_path)
    if filename == consts.ENTITY_TABLE:
        # 实体删除节点,会同时级联删除实体对应的关系 / Delete entity node, will cascade delete associated relationships
        G.remove_node(entity["title"])
        # 保存修改后的图 / Save modified graph
        nx.write_graphml(G, summarized_graph_path)
    elif filename == consts.RELATIONSHIP_TABLE:
        # 通过 id 查出实体关系信息 / Get relationship info by id
        source = entity["source"]
        target = entity["target"]
        # 实体关系删除 / Delete relationship
        old_edge = (source, target)
        # 如果边存在 / If edge exists
        if G.has_edge(*old_edge):
            G.remove_edge(source, target)
            # 保存修改后的图 / Save modified graph
            nx.write_graphml(G, summarized_graph_path)


def simplify_result(result):
    """
    简化嵌套字典的结构。

    Simplify nested dictionary structure.

    参数 Parameters
    ----------
    result : dict
        嵌套字典。Nested dictionary.

    返回 Returns
    -------
    dict
        简化后的字典。Simplified dictionary.
    """
    # 简化一个嵌套字典的结构 / Simplify nested dictionary structure
    simplified = {}
    for key, value in result.items():
        simplified[key] = next(iter(value.values()))
    return simplified


def clean_special_floats(data):
    """
    清理特殊浮点数值(NaN, Infinity)。

    Clean special float values (NaN, Infinity).

    参数 Parameters
    ----------
    data : dict
        数据字典。Data dictionary.

    返回 Returns
    -------
    dict
        清理后的字典。Cleaned dictionary.
    """

    def process_value(value):
        """
        处理process_value。

        Args:
            value: value 参数。

        Returns:
            处理结果。
        """
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        return value

    return {key: process_value(value) for key, value in data.items()}


def convert_to_dict_without_none(data: IndexData.Data) -> dict:
    """
    将对象转换为字典并移除值为 None 的键。

    Convert object to dictionary and remove keys with None values.

    参数 Parameters
    ----------
    data : IndexData.Data
        索引数据对象。Index data object.

    返回 Returns
    -------
    dict
        不含 None 值的字典。Dictionary without None values.
    """
    # 将对象转换为字典 / Convert object to dictionary
    data_dict = data.dict()

    # 移除值为 None 的键 / Remove keys with None values
    return {k: v for k, v in data_dict.items() if v is not None}


def convert_to_single_element_arrays(data):
    """
    将每个字段值转为数组。

    Convert each field value to an array.

    参数 Parameters
    ----------
    data : dict
        数据字典。Data dictionary.

    返回 Returns
    -------
    dict
        转换后的字典。Converted dictionary.
    """
    # 将每个字段值转为数组 / Convert each field value to an array
    return {key: [value] for key, value in data.items()}


def move_file_with_timestamp(source_path, destination_folder, destination_path):
    """
    移动文件并添加时间戳。

    Move file and add timestamp.

    参数 Parameters
    ----------
    source_path : str
        源文件路径。Source file path.
    destination_folder : str
        目标文件夹路径。Destination folder path.
    destination_path : str
        目标文件路径。Destination file path.
    """
    try:
        # 确保目标文件夹存在 / Ensure destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # 移动文件
        shutil.move(source_path, destination_path)

        print(f"文件已成功移动到: {destination_folder}")

    except FileNotFoundError:
        print(f"错误：源文件 '{source_path}' 不存在。")
    except PermissionError:
        print(f"错误：没有权限移动文件 '{source_path}'。")
    except shutil.Error as e:
        print(f"移动文件时发生错误: {e}")
    except Exception as e:
        print(f"发生未预期的错误: {e}")
