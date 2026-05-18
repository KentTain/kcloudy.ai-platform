//! 控制器模块

mod dataset;
mod health;

pub use dataset::*;
pub use health::*;

use axum::{
    routing::{delete, get, post, put},
    Router,
};
use std::sync::Arc;
use tower::ServiceBuilder;
use tower_http::{
    cors::CorsLayer,
    request_id::{SetRequestIdLayer, MakeRequestUuid},
    trace::TraceLayer,
    compression::CompressionLayer,
};

use crate::config::AppConfig;
use crate::db::Database;
use crate::services::DatasetService;
use crate::utils::Cache;

/// 应用状态
#[derive(Clone)]
pub struct AppState {
    pub config: Arc<AppConfig>,
    pub db: Database,
    pub cache: Cache,
    pub dataset_service: DatasetService,
}

/// 创建 Axum 应用
pub async fn create_app(config: &AppConfig) -> crate::Result<Router> {
    // 初始化数据库
    let db = Database::new(&config.database).await?;
    tracing::info!("数据库连接成功");

    // 初始化缓存
    let cache = Cache::new(&config.redis)?;
    if cache.health_check().await? {
        tracing::info!("Redis 连接成功");
    } else {
        tracing::warn!("Redis 健康检查失败");
    }

    // 创建服务
    let dataset_service = DatasetService::new(db.clone());

    // 创建应用状态
    let state = AppState {
        config: Arc::new(config.clone()),
        db,
        cache,
        dataset_service,
    };

    // 构建路由
    let app = Router::new()
        // 健康检查
        .route("/health", get(health_check))
        // Dataset API
        .route("/api/v1/datasets", get(list_datasets))
        .route("/api/v1/datasets", post(create_dataset))
        .route("/api/v1/datasets/{id}", get(get_dataset))
        .route("/api/v1/datasets/{id}", put(update_dataset))
        .route("/api/v1/datasets/{id}", delete(delete_dataset))
        .with_state(state)
        .layer(
            ServiceBuilder::new()
                .layer(SetRequestIdLayer::x_request_id(MakeRequestUuid))
                .layer(TraceLayer::new_for_http())
                .layer(CorsLayer::permissive())
                .layer(CompressionLayer::new()),
        );

    Ok(app)
}
