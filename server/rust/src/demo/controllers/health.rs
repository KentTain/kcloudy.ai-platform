//! 健康检查控制器

use axum::{extract::State, Json};
use serde_json::json;

use super::AppState;

/// 健康检查响应
#[derive(serde::Serialize, utoipa::ToSchema)]
pub struct HealthResponse {
    pub status: String,
    pub database: String,
    pub redis: String,
}

/// 健康检查端点
#[utoipa::path(
    get,
    path = "/health",
    responses(
        (status = 200, description = "服务健康", body = HealthResponse)
    ),
    tag = "Health"
)]
pub async fn health_check(State(state): State<AppState>) -> Json<serde_json::Value> {
    let db_ok = state.db.health_check().await.unwrap_or(false);
    let redis_ok = state.cache.health_check().await.unwrap_or(false);

    Json(json!({
        "code": 200,
        "msg": "success",
        "data": {
            "status": if db_ok && redis_ok { "healthy" } else { "degraded" },
            "database": if db_ok { "ok" } else { "error" },
            "redis": if redis_ok { "ok" } else { "error" },
        }
    }))
}
