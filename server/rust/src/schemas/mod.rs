//! 数据校验模型模块

mod dataset;

pub use dataset::*;

use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// 分页请求参数
#[derive(Debug, Clone, Deserialize, ToSchema)]
pub struct PageRequest {
    /// 当前页码
    #[serde(default = "default_page")]
    pub page: u32,

    /// 每页数量
    #[serde(default = "default_page_size")]
    pub page_size: u32,
}

fn default_page() -> u32 {
    1
}

fn default_page_size() -> u32 {
    10
}

impl Default for PageRequest {
    fn default() -> Self {
        Self {
            page: default_page(),
            page_size: default_page_size(),
        }
    }
}

/// 分页响应
#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct PageResponse<T> {
    /// 数据列表
    pub items: Vec<T>,
    /// 总数
    pub total: u64,
    /// 当前页码
    pub page: u32,
    /// 每页数量
    pub page_size: u32,
}

impl<T> PageResponse<T> {
    /// 创建分页响应
    pub fn new(items: Vec<T>, total: u64, page: u32, page_size: u32) -> Self {
        Self {
            items,
            total,
            page,
            page_size,
        }
    }
}
