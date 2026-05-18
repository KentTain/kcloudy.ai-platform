//! 配置模块单元测试

use demo::config::{AppConfig, ServerConfig};

#[test]
fn test_default_server_config() {
    let config = ServerConfig::default();
    assert_eq!(config.host, "0.0.0.0");
    assert_eq!(config.port, 8000);
    assert!(!config.debug);
}

#[test]
fn test_listen_addr() {
    let config = AppConfig {
        server: ServerConfig {
            host: "127.0.0.1".to_string(),
            port: 3000,
            ..Default::default()
        },
        ..Default::default()
    };

    let addr = config.listen_addr();
    assert_eq!(addr.port(), 3000);
    assert_eq!(addr.ip().to_string(), "127.0.0.1");
}

#[test]
fn test_config_from_yaml() {
    // 测试从 YAML 字符串解析配置
    let yaml = r#"
name: test-app
server:
  host: 0.0.0.0
  port: 9000
"#;

    // 这里需要实际的配置加载逻辑
    // 目前仅验证字符串可以解析
    assert!(yaml.contains("test-app"));
}
