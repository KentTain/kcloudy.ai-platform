//! 配置管理模块

mod settings;

pub use settings::*;

use std::path::Path;

use config::{Config, File, FileFormat};
use thiserror::Error;

/// 配置错误
#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("配置文件读取失败: {0}")]
    Io(#[from] std::io::Error),

    #[error("配置解析失败: {0}")]
    Parse(#[from] config::ConfigError),

    #[error("环境变量解析失败: {0}")]
    EnvVar(String),
}

/// 从 YAML 文件加载配置
pub fn load_config<P: AsRef<Path>>(path: P) -> Result<Config, ConfigError> {
    let config = Config::builder()
        .add_source(File::new(path.as_ref().to_str().unwrap(), FileFormat::Yaml))
        .add_source(
            config::Environment::with_prefix("DEMO")
                .separator("__")
                .try_parsing(true),
        )
        .build()?;

    Ok(config)
}
