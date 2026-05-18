//! 测试数据夹具

use chrono::{DateTime, Utc};
use uuid::Uuid;

/// 测试知识库数据
pub struct TestDataset {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl TestDataset {
    /// 创建测试知识库
    pub fn new(name: &str, description: Option<&str>) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            name: name.to_string(),
            description: description.map(|s| s.to_string()),
            created_at: now,
            updated_at: now,
        }
    }

    /// 创建默认测试知识库
    pub fn default() -> Self {
        Self::new("测试知识库", Some("这是一个测试知识库"))
    }
}
