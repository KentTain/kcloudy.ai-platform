//! 测试数据

use serde_json::json;

/// 生成测试用的 Dataset JSON 数据
pub fn sample_dataset_json() -> serde_json::Value {
    json!({
        "name": "测试知识库",
        "description": "这是一个测试知识库描述"
    })
}

/// 生成测试用的 Dataset 列表 JSON 数据
pub fn sample_dataset_list_json() -> serde_json::Value {
    json!([
        {
            "name": "知识库1",
            "description": "描述1"
        },
        {
            "name": "知识库2",
            "description": "描述2"
        }
    ])
}
