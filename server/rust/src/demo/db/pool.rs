//! 数据库连接池管理

use sqlx::{PgPool, Postgres, postgres::PgPoolOptions};
use std::time::Duration;
use crate::config::DatabaseConfig;
use crate::common::error::{Error, Result};

/// 数据库连接池类型别名
pub type DbPool = PgPool;

/// 数据库连接管理器
#[derive(Clone)]
pub struct Database {
    pool: DbPool,
}

impl Database {
    /// 创建新的数据库连接池
    pub async fn new(config: &DatabaseConfig) -> Result<Self> {
        let pool = PgPoolOptions::new()
            .max_connections(config.max_connections)
            .min_connections(config.min_connections)
            .acquire_timeout(Duration::from_secs(config.connect_timeout))
            .idle_timeout(Some(Duration::from_secs(config.idle_timeout)))
            .connect(&config.url)
            .await
            .map_err(Error::Database)?;

        tracing::info!(
            "数据库连接池已创建 (max={}, min={})",
            config.max_connections,
            config.min_connections
        );

        Ok(Self { pool })
    }

    /// 获取连接池引用
    pub fn pool(&self) -> &DbPool {
        &self.pool
    }

    /// 执行健康检查
    pub async fn health_check(&self) -> Result<bool> {
        let result: Option<i32> = sqlx::query_scalar("SELECT 1")
            .fetch_optional(&self.pool)
            .await
            .map_err(Error::Database)?;

        Ok(result.is_some())
    }

    /// 关闭连接池
    pub async fn close(&self) {
        self.pool.close().await;
        tracing::info!("数据库连接池已关闭");
    }
}

/// 数据库事务封装
pub struct Transaction<'a>(pub sqlx::Transaction<'a, Postgres>);

impl<'a> Transaction<'a> {
    /// 开始新事务
    pub async fn begin(pool: &DbPool) -> Result<Self> {
        let tx = pool.begin().await.map_err(Error::Database)?;
        Ok(Self(tx))
    }

    /// 提交事务
    pub async fn commit(self) -> Result<()> {
        self.0.commit().await.map_err(Error::Database)
    }

    /// 回滚事务
    pub async fn rollback(self) -> Result<()> {
        self.0.rollback().await.map_err(Error::Database)
    }
}

impl<'a> AsRef<sqlx::Transaction<'a, Postgres>> for Transaction<'a> {
    fn as_ref(&self) -> &sqlx::Transaction<'a, Postgres> {
        &self.0
    }
}

impl<'a> std::ops::Deref for Transaction<'a> {
    type Target = sqlx::Transaction<'a, Postgres>;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
