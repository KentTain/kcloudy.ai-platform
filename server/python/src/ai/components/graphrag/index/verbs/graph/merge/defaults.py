"""提供组件图谱检索增强生成相关功能。"""

from ai.components.graphrag.index.verbs.graph.merge.typing import BasicMergeOperation

DEFAULT_NODE_OPERATIONS = {
    "*": {
        "operation": BasicMergeOperation.Replace,
    }
}

DEFAULT_EDGE_OPERATIONS = {
    "*": {
        "operation": BasicMergeOperation.Replace,
    },
    "weight": "sum",
}

DEFAULT_CONCAT_SEPARATOR = ","
