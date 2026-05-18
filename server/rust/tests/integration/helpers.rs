//! 测试辅助函数

use axum::Router;
use demo::config::AppConfig;
use demo::controllers::create_app;

/// 创建测试应用
pub async fn create_test_app() -> Router {
    let config = test_config();
    create_app(&config).await.expect("创建应用失败")
}

/// 创建测试配置
pub fn test_config() -> AppConfig {
    AppConfig {
        name: "demo-test".to_string(),
        server: demo::config::ServerConfig {
            host: "127.0.0.1".to_string(),
            port: 0, // 随机端口
            debug: true,
            timeout: 30,
            body_limit: 1024 * 1024,
        },
        database: demo::config::DatabaseConfig {
            url: std::env::var("TEST_DATABASE_URL")
                .unwrap_or_else(|_| "postgresql://postgres:postgres@localhost:5432/demo_test".to_string()),
            max_connections: 5,
            min_connections: 0,
            connect_timeout: 30,
            idle_timeout: 300,
            echo: false,
        },
        redis: demo::config::RedisConfig {
            url: std::env::var("TEST_REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379/1".to_string()),
            pool_size: 5,
            timeout_ms: 5000,
        },
        ..Default::default()
    }
}

/// 生成随机字符串
pub fn random_string(length: usize) -> String {
    use std::iter;
    use rand::{Rng, distr::Alphanumeric};

    let mut rng = rand::rng();
    iter::repeat(())
        .map(|()| rng.sample(Alphanumeric))
        .map(char::from)
        .take(length)
        .collect()
}
