//! 请求上下文模块

use chrono::{DateTime, Local};
use chrono_tz::Tz;
use std::sync::OnceLock;

/// 中国时区
pub static CHINA_TIMEZONE: OnceLock<Tz> = OnceLock::new();

/// 获取中国时区
pub fn china_timezone() -> Tz {
    *CHINA_TIMEZONE.get_or_init(|| "Asia/Shanghai".parse().unwrap())
}

/// 获取当前中国时间
pub fn now_china() -> DateTime<Tz> {
    Local::now().with_timezone(&china_timezone())
}

/// 请求上下文
#[derive(Debug, Clone)]
pub struct RequestContext {
    /// 请求 ID
    pub request_id: String,
    /// 开始时间
    pub start_time: std::time::Instant,
}

impl RequestContext {
    /// 创建新的请求上下文
    pub fn new(request_id: String) -> Self {
        Self {
            request_id,
            start_time: std::time::Instant::now(),
        }
    }

    /// 获取请求耗时（毫秒）
    pub fn elapsed_ms(&self) -> u64 {
        self.start_time.elapsed().as_millis() as u64
    }
}
