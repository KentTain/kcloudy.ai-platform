//! Dataset 相关的数据校验模型

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;
use uuid::Uuid;
use validator::Validate;

/// 创建知识库请求
#[derive(Debug, Clone, Deserialize, Validate, ToSchema)]
pub struct DatasetCreate {
    /// 知识库名称
    #[validate(length(min = 1, max = 255, message = "名称长度必须在1-255之间"))]
    pub name: String,

    /// 知识库描述
    #[validate(length(max = 1000, message = "描述长度不能超过1000"))]
    pub description: Option<String>,
}

/// 更新知识库请求
#[derive(Debug, Clone, Deserialize, Validate, ToSchema)]
pub struct DatasetUpdate {
    /// 知识库名称
    #[validate(length(min = 1, max = 255, message = "名称长度必须在1-255之间"))]
    pub name: Option<String>,

    /// 知识库描述
    #[validate(length(max = 1000, message = "描述长度不能超过1000"))]
    pub description: Option<String>,
}

/// 知识库响应视图
#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct DatasetVo {
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

impl From<crate::models::Dataset> for DatasetVo {
    fn from(model: crate::models::Dataset) -> Self {
        Self {
            id: model.id,
            name: model.name,
            description: model.description,
            created_at: model.created_at,
            updated_at: model.updated_at,
        }
    }
}
