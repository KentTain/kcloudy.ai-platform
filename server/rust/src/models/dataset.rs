//! Dataset 示例模型

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

use super::{BaseModel, TimestampBehavior};

/// 知识库模型
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Dataset {
    /// 主键 ID
    pub id: Uuid,
    /// 知识库名称
    pub name: String,
    /// 知识库描述
    pub description: Option<String>,
    /// 创建时间
    pub created_at: DateTime<Utc>,
    /// 更新时间
    pub updated_at: DateTime<Utc>,
}

impl Dataset {
    /// 创建新知识库
    pub fn new(name: String, description: Option<String>) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            name,
            description,
            created_at: now,
            updated_at: now,
        }
    }
}

impl BaseModel for Dataset {
    const TABLE_NAME: &'static str = "dataset";

    fn id(&self) -> &str {
        // UUID 转换为字符串引用
        // 注意：这是一个简化实现，实际使用时可能需要不同的方式
        Box::leak(self.id.to_string().into_boxed_str())
    }
}

impl TimestampBehavior for Dataset {
    fn created_at(&self) -> DateTime<Utc> {
        self.created_at
    }

    fn updated_at(&self) -> DateTime<Utc> {
        self.updated_at
    }
}
