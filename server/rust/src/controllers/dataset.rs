//! Dataset 控制器

use axum::{
    extract::{Path, Query, State},
    Json,
};
use uuid::Uuid;
use validator::Validate;

use super::AppState;
use crate::common::error::{ApiResponse, Error, Result};
use crate::schemas::{DatasetCreate, DatasetUpdate, DatasetVo, PageRequest, PageResponse};

/// 获取知识库列表
#[utoipa::path(
    get,
    path = "/api/v1/datasets",
    params(PageRequest),
    responses(
        (status = 200, description = "获取成功", body = ApiResponse<PageResponse<DatasetVo>>)
    ),
    tag = "Dataset"
)]
pub async fn list_datasets(
    State(state): State<AppState>,
    Query(params): Query<PageRequest>,
) -> Result<Json<ApiResponse<PageResponse<DatasetVo>>>> {
    let result = state.dataset_service.list(params.page, params.page_size).await?;
    Ok(Json(ApiResponse::success(result)))
}

/// 创建知识库
#[utoipa::path(
    post,
    path = "/api/v1/datasets",
    request_body = DatasetCreate,
    responses(
        (status = 200, description = "创建成功", body = ApiResponse<DatasetVo>)
    ),
    tag = "Dataset"
)]
pub async fn create_dataset(
    State(state): State<AppState>,
    Json(data): Json<DatasetCreate>,
) -> Result<Json<ApiResponse<DatasetVo>>> {
    data.validate().map_err(|e| Error::Validation(e.to_string()))?;
    let result = state.dataset_service.create(data).await?;
    Ok(Json(ApiResponse::success(result)))
}

/// 获取知识库详情
#[utoipa::path(
    get,
    path = "/api/v1/datasets/{id}",
    params(
        ("id" = Uuid, Path, description = "知识库 ID")
    ),
    responses(
        (status = 200, description = "获取成功", body = ApiResponse<DatasetVo>),
        (status = 404, description = "知识库不存在")
    ),
    tag = "Dataset"
)]
pub async fn get_dataset(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<DatasetVo>>> {
    let result = state
        .dataset_service
        .get(id)
        .await?
        .ok_or_else(|| Error::NotFound("知识库不存在".to_string()))?;
    Ok(Json(ApiResponse::success(result)))
}

/// 更新知识库
#[utoipa::path(
    put,
    path = "/api/v1/datasets/{id}",
    params(
        ("id" = Uuid, Path, description = "知识库 ID")
    ),
    request_body = DatasetUpdate,
    responses(
        (status = 200, description = "更新成功", body = ApiResponse<DatasetVo>),
        (status = 404, description = "知识库不存在")
    ),
    tag = "Dataset"
)]
pub async fn update_dataset(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Json(data): Json<DatasetUpdate>,
) -> Result<Json<ApiResponse<DatasetVo>>> {
    if let Some(ref name) = data.name {
        if name.is_empty() || name.len() > 255 {
            return Err(Error::Validation("名称长度必须在1-255之间".to_string()));
        }
    }

    let result = state
        .dataset_service
        .update(id, data)
        .await?
        .ok_or_else(|| Error::NotFound("知识库不存在".to_string()))?;
    Ok(Json(ApiResponse::success(result)))
}

/// 删除知识库
#[utoipa::path(
    delete,
    path = "/api/v1/datasets/{id}",
    params(
        ("id" = Uuid, Path, description = "知识库 ID")
    ),
    responses(
        (status = 200, description = "删除成功", body = ApiResponse<()>),
        (status = 404, description = "知识库不存在")
    ),
    tag = "Dataset"
)]
pub async fn delete_dataset(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<()>>> {
    let success = state.dataset_service.delete(id).await?;
    if !success {
        return Err(Error::NotFound("知识库不存在".to_string()));
    }
    Ok(Json(ApiResponse::success_empty()))
}
