//! 应用配置定义

use serde::Deserialize;
use std::net::SocketAddr;
use std::path::PathBuf;

use super::{load_config, ConfigError};

/// 主应用配置
#[derive(Debug, Clone, Deserialize)]
pub struct AppConfig {
    /// 应用名称
    #[serde(default = "default_app_name")]
    pub name: String,

    /// 服务器配置
    #[serde(default)]
    pub server: ServerConfig,

    /// 日志配置
    #[serde(default)]
    pub logging: LoggingConfig,

    /// 数据库配置
    #[serde(default)]
    pub database: DatabaseConfig,

    /// Redis 配置
    #[serde(default)]
    pub redis: RedisConfig,

    /// AI 配置
    #[serde(default)]
    pub ai: AiConfig,
}

fn default_app_name() -> String {
    "demo".to_string()
}

impl AppConfig {
    /// 从文件加载配置
    pub fn from_file<P: Into<PathBuf>>(path: P) -> Result<Self, ConfigError> {
        let config = load_config(path.into())?;
        let app_config: AppConfig = config.try_deserialize()?;
        Ok(app_config)
    }

    /// 获取服务器监听地址
    pub fn listen_addr(&self) -> SocketAddr {
        format!("{}:{}", self.server.host, self.server.port)
            .parse()
            .expect("无效的监听地址")
    }
}

/// 服务器配置
#[derive(Debug, Clone, Deserialize)]
pub struct ServerConfig {
    /// 监听主机
    #[serde(default = "default_host")]
    pub host: String,

    /// 监听端口
    #[serde(default = "default_port")]
    pub port: u16,

    /// 调试模式
    #[serde(default)]
    pub debug: bool,

    /// 请求超时（秒）
    #[serde(default = "default_timeout")]
    pub timeout: u64,

    /// 请求体大小限制（字节）
    #[serde(default = "default_body_limit")]
    pub body_limit: usize,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: default_host(),
            port: default_port(),
            debug: false,
            timeout: default_timeout(),
            body_limit: default_body_limit(),
        }
    }
}

fn default_host() -> String {
    "0.0.0.0".to_string()
}

fn default_port() -> u16 {
    8000
}

fn default_timeout() -> u64 {
    30
}

fn default_body_limit() -> usize {
    1024 * 1024 * 10 // 10MB
}

/// 日志配置
#[derive(Debug, Clone, Deserialize)]
pub struct LoggingConfig {
    /// 日志级别
    #[serde(default = "default_log_level")]
    pub level: String,

    /// 日志格式
    #[serde(default = "default_log_format")]
    pub format: String,

    /// 是否输出到文件
    #[serde(default)]
    pub file: Option<PathBuf>,
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            level: default_log_level(),
            format: default_log_format(),
            file: None,
        }
    }
}

fn default_log_level() -> String {
    "INFO".to_string()
}

fn default_log_format() -> String {
    "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}".to_string()
}

/// 数据库配置
#[derive(Debug, Clone, Deserialize)]
pub struct DatabaseConfig {
    /// 数据库连接 URL
    #[serde(default = "default_database_url")]
    pub url: String,

    /// 最大连接数
    #[serde(default = "default_max_connections")]
    pub max_connections: u32,

    /// 最小连接数
    #[serde(default)]
    pub min_connections: u32,

    /// 连接超时（秒）
    #[serde(default = "default_connect_timeout")]
    pub connect_timeout: u64,

    /// 空闲超时（秒）
    #[serde(default = "default_idle_timeout")]
    pub idle_timeout: u64,

    /// 是否打印 SQL
    #[serde(default)]
    pub echo: bool,
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            url: default_database_url(),
            max_connections: default_max_connections(),
            min_connections: 0,
            connect_timeout: default_connect_timeout(),
            idle_timeout: default_idle_timeout(),
            echo: false,
        }
    }
}

fn default_database_url() -> String {
    "postgresql://postgres:postgres@localhost:5432/demo".to_string()
}

fn default_max_connections() -> u32 {
    10
}

fn default_connect_timeout() -> u64 {
    30
}

fn default_idle_timeout() -> u64 {
    600
}

/// Redis 配置
#[derive(Debug, Clone, Deserialize)]
pub struct RedisConfig {
    /// Redis 连接 URL
    #[serde(default = "default_redis_url")]
    pub url: String,

    /// 连接池大小
    #[serde(default = "default_redis_pool_size")]
    pub pool_size: usize,

    /// 连接超时（毫秒）
    #[serde(default = "default_redis_timeout")]
    pub timeout_ms: u64,
}

impl Default for RedisConfig {
    fn default() -> Self {
        Self {
            url: default_redis_url(),
            pool_size: default_redis_pool_size(),
            timeout_ms: default_redis_timeout(),
        }
    }
}

fn default_redis_url() -> String {
    "redis://localhost:6379/0".to_string()
}

fn default_redis_pool_size() -> usize {
    10
}

fn default_redis_timeout() -> u64 {
    5000
}

/// AI 配置
#[derive(Debug, Clone, Deserialize)]
pub struct AiConfig {
    /// OpenAI API Key
    #[serde(default)]
    pub openai_api_key: Option<String>,

    /// OpenAI API 基础 URL
    #[serde(default)]
    pub openai_base_url: Option<String>,

    /// 默认模型
    #[serde(default = "default_model")]
    pub default_model: String,

    /// Embedding 模型
    #[serde(default = "default_embedding_model")]
    pub embedding_model: String,
}

impl Default for AiConfig {
    fn default() -> Self {
        Self {
            openai_api_key: None,
            openai_base_url: None,
            default_model: default_model(),
            embedding_model: default_embedding_model(),
        }
    }
}

fn default_model() -> String {
    "gpt-4o-mini".to_string()
}

fn default_embedding_model() -> String {
    "text-embedding-3-small".to_string()
}
