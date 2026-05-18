//! Demo - 最小化 AI 助手平台 Rust 后端
//!
//! 这是一个使用 Axum 框架构建的异步 Web 服务，
//! 集成了 LangChain Rust 用于 AI 编排，
//! SQLx 用于数据库操作，以及 redis-rs 用于缓存。

pub mod common;
pub mod config;
pub mod controllers;
pub mod db;
pub mod models;
pub mod schemas;
pub mod services;
pub mod utils;

#[cfg(feature = "examples")]
pub mod examples;

pub use config::AppConfig;
pub use common::error::{Error, Result};
