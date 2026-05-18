//! Dataset 服务层

use sqlx::PgPool;
use uuid::Uuid;

use crate::common::error::{Error, Result};
use crate::db::Database;
use crate::models::Dataset;
use crate::schemas::{DatasetCreate, DatasetUpdate, DatasetVo, PageResponse};

/// 知识库服务
pub struct DatasetService {
    db: Database,
}

impl DatasetService {
    /// 创建新的服务实例
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    /// 获取知识库列表
    pub async fn list(
        &self,
        page: u32,
        page_size: u32,
    ) -> Result<PageResponse<DatasetVo>> {
        let pool = self.db.pool();
        let offset = (page.saturating_sub(1)) * page_size;

        // 查询总数
        let total: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM dataset")
            .fetch_one(pool)
            .await
            .map_err(Error::Database)?;

        // 查询列表
        let items: Vec<Dataset> = sqlx::query_as(
            "SELECT id, name, description, created_at, updated_at
             FROM dataset
             ORDER BY created_at DESC
             LIMIT $1 OFFSET $2",
        )
        .bind(page_size as i64)
        .bind(offset as i64)
        .fetch_all(pool)
        .await
        .map_err(Error::Database)?;

        Ok(PageResponse::new(
            items.into_iter().map(DatasetVo::from).collect(),
            total as u64,
            page,
            page_size,
        ))
    }

    /// 创建知识库
    pub async fn create(&self, data: DatasetCreate) -> Result<DatasetVo> {
        let pool = self.db.pool();
        let dataset = Dataset::new(data.name, data.description);

        let created: Dataset = sqlx::query_as(
            "INSERT INTO dataset (id, name, description, created_at, updated_at)
             VALUES ($1, $2, $3, $4, $5)
             RETURNING id, name, description, created_at, updated_at",
        )
        .bind(dataset.id)
        .bind(&dataset.name)
        .bind(&dataset.description)
        .bind(dataset.created_at)
        .bind(dataset.updated_at)
        .fetch_one(pool)
        .await
        .map_err(Error::Database)?;

        Ok(DatasetVo::from(created))
    }

    /// 获取知识库详情
    pub async fn get(&self, id: Uuid) -> Result<Option<DatasetVo>> {
        let pool = self.db.pool();

        let result: Option<Dataset> = sqlx::query_as(
            "SELECT id, name, description, created_at, updated_at
             FROM dataset
             WHERE id = $1",
        )
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(Error::Database)?;

        Ok(result.map(DatasetVo::from))
    }

    /// 更新知识库
    pub async fn update(&self, id: Uuid, data: DatasetUpdate) -> Result<Option<DatasetVo>> {
        let pool = self.db.pool();

        // 首先检查是否存在
        let existing = self.get(id).await?;
        if existing.is_none() {
            return Ok(None);
        }

        let existing = existing.unwrap();
        let name = data.name.unwrap_or(existing.name);
        let description = data.description.or(existing.description);

        let updated: Dataset = sqlx::query_as(
            "UPDATE dataset
             SET name = $1, description = $2, updated_at = NOW()
             WHERE id = $3
             RETURNING id, name, description, created_at, updated_at",
        )
        .bind(&name)
        .bind(&description)
        .bind(id)
        .fetch_one(pool)
        .await
        .map_err(Error::Database)?;

        Ok(Some(DatasetVo::from(updated)))
    }

    /// 删除知识库
    pub async fn delete(&self, id: Uuid) -> Result<bool> {
        let pool = self.db.pool();

        let result = sqlx::query("DELETE FROM dataset WHERE id = $1")
            .bind(id)
            .execute(pool)
            .await
            .map_err(Error::Database)?;

        Ok(result.rows_affected() > 0)
    }
}
