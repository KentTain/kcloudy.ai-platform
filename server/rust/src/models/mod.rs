//! 数据库模型模块

mod dataset;

pub use dataset::*;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

/// 基础模型特性
pub trait BaseModel: Sized + Clone + Send + Sync + 'static {
    /// 表名
    const TABLE_NAME: &'static str;

    /// 主键 ID
    fn id(&self) -> &str;
}

/// 时间戳 Mixin
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct TimestampMixin {
    /// 创建时间
    pub created_at: DateTime<Utc>,
    /// 更新时间
    pub updated_at: DateTime<Utc>,
}

/// UUID 主键 Mixin
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct UuidPrimaryKeyMixin {
    /// 主键 ID
    pub id: Uuid,
}

impl Default for UuidPrimaryKeyMixin {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4(),
        }
    }
}
