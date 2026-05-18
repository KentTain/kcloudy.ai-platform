//! Redis 缓存管理

use redis::{AsyncCommands, Client as RedisClient};
use serde::{de::DeserializeOwned, Serialize};
use std::time::Duration;

use crate::common::error::{Error, Result};
use crate::config::RedisConfig;

/// Redis 缓存客户端
#[derive(Clone)]
pub struct Cache {
    client: RedisClient,
}

impl Cache {
    /// 创建新的缓存客户端
    pub fn new(config: &RedisConfig) -> Result<Self> {
        let client = RedisClient::open(config.url.as_str())
            .map_err(|e| Error::Internal(format!("Redis 连接失败: {}", e)))?;

        tracing::info!("Redis 客户端已创建");
        Ok(Self { client })
    }

    /// 获取异步连接
    pub async fn get_connection(&self) -> Result<redis::aio::Connection> {
        self.client
            .get_async_connection()
            .await
            .map_err(Error::Redis)
    }

    /// 设置缓存
    pub async fn set<K, V>(&self, key: K, value: &V, ttl: Option<Duration>) -> Result<()>
    where
        K: AsRef<str> + Send,
        V: Serialize + Send + Sync,
    {
        let mut conn = self.get_connection().await?;
        let serialized = serde_json::to_string(value)?;

        if let Some(ttl) = ttl {
            conn.set_ex(key.as_ref(), serialized, ttl.as_secs())
                .await
                .map_err(Error::Redis)?;
        } else {
            conn.set(key.as_ref(), serialized)
                .await
                .map_err(Error::Redis)?;
        }

        Ok(())
    }

    /// 获取缓存
    pub async fn get<K, V>(&self, key: K) -> Result<Option<V>>
    where
        K: AsRef<str> + Send,
        V: DeserializeOwned,
    {
        let mut conn = self.get_connection().await?;
        let result: Option<String> = conn.get(key.as_ref()).await.map_err(Error::Redis)?;

        match result {
            Some(json) => {
                let value = serde_json::from_str(&json)?;
                Ok(Some(value))
            }
            None => Ok(None),
        }
    }

    /// 删除缓存
    pub async fn delete<K>(&self, key: K) -> Result<bool>
    where
        K: AsRef<str> + Send,
    {
        let mut conn = self.get_connection().await?;
        let result: i64 = conn.del(key.as_ref()).await.map_err(Error::Redis)?;
        Ok(result > 0)
    }

    /// 检查键是否存在
    pub async fn exists<K>(&self, key: K) -> Result<bool>
    where
        K: AsRef<str> + Send,
    {
        let mut conn = self.get_connection().await?;
        let result: bool = conn.exists(key.as_ref()).await.map_err(Error::Redis)?;
        Ok(result)
    }

    /// 设置过期时间
    pub async fn expire<K>(&self, key: K, ttl: Duration) -> Result<bool>
    where
        K: AsRef<str> + Send,
    {
        let mut conn = self.get_connection().await?;
        let result: bool = conn
            .expire(key.as_ref(), ttl.as_secs() as i64)
            .await
            .map_err(Error::Redis)?;
        Ok(result)
    }

    /// 健康检查
    pub async fn health_check(&self) -> Result<bool> {
        let mut conn = self.get_connection().await?;
        let result: String = redis::cmd("PING")
            .query(&mut conn)
            .await
            .map_err(Error::Redis)?;
        Ok(result == "PONG")
    }
}
