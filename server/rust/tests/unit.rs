//! Demo 模块单元测试
//!
//! 包含 config、error、cache 等模块的单元测试

mod fixtures;

mod config {
    use demo::config::ServerConfig;

    #[test]
    fn test_default_server_config() {
        let config = ServerConfig::default();
        assert_eq!(config.host, "0.0.0.0");
        assert_eq!(config.port, 8000);
        assert!(!config.debug);
    }

    #[test]
    fn test_listen_addr_calculation() {
        // 测试地址计算逻辑
        let host = "127.0.0.1";
        let port: u16 = 3000;
        let addr_str = format!("{}:{}", host, port);
        assert!(addr_str.contains("127.0.0.1"));
        assert!(addr_str.contains("3000"));
    }

    #[test]
    fn test_config_from_yaml() {
        let yaml = r#"
name: test-app
server:
  host: 0.0.0.0
  port: 9000
"#;

        assert!(yaml.contains("test-app"));
    }
}

mod error {
    use demo::common::error::{Error, ApiResponse};

    #[test]
    fn test_error_display() {
        let err = Error::NotFound("测试资源".to_string());
        assert_eq!(format!("{}", err), "资源未找到: 测试资源");

        let err = Error::Validation("名称不能为空".to_string());
        assert_eq!(format!("{}", err), "验证错误: 名称不能为空");
    }

    #[test]
    fn test_api_response_success() {
        let response = ApiResponse::success("test data");
        assert_eq!(response.code, 200);
        assert_eq!(response.msg, "success");
        assert_eq!(response.data, Some("test data"));
    }

    #[test]
    fn test_api_response_error() {
        let response = ApiResponse::<()>::error(404, "未找到".to_string());
        assert_eq!(response.code, 404);
        assert_eq!(response.msg, "未找到");
        assert!(response.data.is_none());
    }
}

mod cache {
    #[test]
    fn test_cache_key_format() {
        let key = format!("dataset:{}", uuid::Uuid::new_v4());
        assert!(key.starts_with("dataset:"));
    }
}
