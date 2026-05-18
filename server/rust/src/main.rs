//! Demo Web 服务器入口

use clap::Parser;
use demo::AppConfig;
use demo::common::error::Result;
use demo::controllers::create_app;
use std::net::SocketAddr;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Demo AI 助手平台后端服务
#[derive(Parser, Debug)]
#[command(name = "demo", version, about, long_about = None)]
struct Args {
    /// 服务器监听地址
    #[arg(short, long, default_value = "0.0.0.0")]
    host: String,

    /// 服务器监听端口
    #[arg(short, long, default_value_t = 8000)]
    port: u16,

    /// 启用调试模式
    #[arg(short, long)]
    debug: bool,

    /// 配置文件路径
    #[arg(short, long, default_value = "config/application.yml")]
    config: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // 解析命令行参数
    let args = Args::parse();

    // 初始化日志
    init_tracing(args.debug);

    // 加载配置
    let config = AppConfig::from_file(&args.config)?;
    info!(?config, "配置加载完成");

    // 创建 Axum 应用
    let app = create_app(&config).await?;

    // 绑定地址
    let addr: SocketAddr = format!("{}:{}", args.host, args.port)
        .parse()
        .map_err(|e| demo::common::error::Error::Internal(format!("地址解析失败: {}", e)))?;
    info!("服务器启动于 http://{}", addr);

    // 启动服务器
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

/// 初始化 tracing 日志系统
fn init_tracing(debug: bool) {
    let filter = if debug {
        "debug"
    } else {
        "info"
    };

    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new(filter)),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
}
