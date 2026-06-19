"""提供图谱检索增强生成工具相关功能。"""

import os
from datetime import datetime


def get_root_path() -> str:
    """
    获取项目根路径

    Returns:
        处理结果。
    """
    # 获取文件目录
    cur_path = os.path.abspath(os.path.dirname(__file__))

    # 获取项目根路径,内容为当前项目的名字
    root_path = os.path.abspath(os.path.join(cur_path, "../.."))
    return root_path


# 项目根路径
ROOT_PATH = get_root_path()
print(f"项目根路径:{ROOT_PATH}, {datetime.now()}, pid:{os.getpid()}")

# parquet files generated from indexing pipeline

COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"
ENTITY_EMBEDDING_TABLE = "create_final_entities"

# community level in the Leiden community hierarchy from which we will load the community reports
# higher value means we use reports from more fine-grained communities (at the cost of higher computation cost)
COMMUNITY_LEVEL = 2

RELATIONSHIP_TABLE = "create_final_relationships"
COVARIATE_TABLE = "create_final_covariates"
TEXT_UNIT_TABLE = "create_final_text_units"

LATEST_MODEL_LOCAL = "GraphRAG-latest-local"
LATEST_MODEL_GLOBAL = "GraphRAG-latest-global"

RAGDATA_DIR = ROOT_PATH + "/ragdata"
MINIO_BASE_DIR = "graphrag"
RAGCONFIG_PATH = ROOT_PATH + "/ragconfig/settings.yaml"

DOC_TYPE_DOC_LIST = (
    "doc_type:doclist"  # 该常量标识输入的文档类型为doclist，即传递过来的分片文档列表
)
