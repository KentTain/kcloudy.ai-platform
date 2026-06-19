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

/// 时间戳 Mixin - 结构体，可嵌入其他模型
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct TimestampMixin {
    /// 创建时间
    pub created_at: DateTime<Utc>,
    /// 更新时间
    pub updated_at: DateTime<Utc>,
}

/// 时间戳特征 - 用于访问时间戳字段
pub trait TimestampBehavior {
    /// 获取创建时间
    fn created_at(&self) -> DateTime<Utc>;
    /// 获取更新时间
    fn updated_at(&self) -> DateTime<Utc>;
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
