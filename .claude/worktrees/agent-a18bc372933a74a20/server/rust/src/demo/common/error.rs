//! 错误处理模块

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use thiserror::Error;

/// 应用错误类型
#[derive(Error, Debug)]
pub enum Error {
    #[error("配置错误: {0}")]
    Config(#[from] crate::config::ConfigError),

    #[error("数据库错误: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Redis 错误: {0}")]
    Redis(#[from] redis::RedisError),

    #[error("IO 错误: {0}")]
    Io(#[from] std::io::Error),

    #[error("序列化错误: {0}")]
    Serialize(#[from] serde_json::Error),

    #[error("资源未找到: {0}")]
    NotFound(String),

    #[error("验证错误: {0}")]
    Validation(String),

    #[error("内部错误: {0}")]
    Internal(String),

    #[error("请求错误: {0}")]
    BadRequest(String),

    #[error("未授权")]
    Unauthorized,

    #[error("禁止访问")]
    Forbidden,
}

/// 结果类型别名
pub type Result<T> = std::result::Result<T, Error>;

/// API 响应结构
#[derive(Debug, serde::Serialize, utoipa::ToSchema)]
pub struct ApiResponse<T> {
    pub code: u16,
    pub msg: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
}

impl<T> ApiResponse<T> {
    /// 成功响应
    pub fn success(data: T) -> Self {
        Self {
            code: 200,
            msg: "success".to_string(),
            data: Some(data),
        }
    }

    /// 成功响应（无数据）
    pub fn success_empty() -> ApiResponse<()> {
        ApiResponse {
            code: 200,
            msg: "success".to_string(),
            data: None,
        }
    }

    /// 错误响应
    pub fn error(code: u16, msg: String) -> ApiResponse<()> {
        ApiResponse {
            code,
            msg,
            data: None,
        }
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let (status, code, msg) = match self {
            Error::NotFound(msg) => (StatusCode::NOT_FOUND, 404, msg),
            Error::Validation(msg) => (StatusCode::BAD_REQUEST, 400, msg),
            Error::BadRequest(msg) => (StatusCode::BAD_REQUEST, 400, msg),
            Error::Unauthorized => (StatusCode::UNAUTHORIZED, 401, "未授权".to_string()),
            Error::Forbidden => (StatusCode::FORBIDDEN, 403, "禁止访问".to_string()),
            Error::Database(ref e) => {
                tracing::error!("数据库错误: {:?}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, 500, "数据库错误".to_string())
            }
            Error::Redis(ref e) => {
                tracing::error!("Redis 错误: {:?}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, 500, "缓存服务错误".to_string())
            }
            Error::Internal(msg) => {
                tracing::error!("内部错误: {}", msg);
                (StatusCode::INTERNAL_SERVER_ERROR, 500, msg)
            }
            _ => {
                tracing::error!("未知错误: {:?}", self);
                (StatusCode::INTERNAL_SERVER_ERROR, 500, "服务器内部错误".to_string())
            }
        };

        let body = Json(ApiResponse::<()>::error(code, msg));
        (status, body).into_response()
    }
}
