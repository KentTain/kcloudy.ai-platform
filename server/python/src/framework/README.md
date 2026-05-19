# Framework 模块

统一的 Python 后端基础设施组件库。

## 功能特性

- **统一配置** - 基于 YAML 的分层配置，支持环境变量覆盖
- **Redis 缓存** - 封装常用操作，支持连接池管理
- **对象存储** - 支持 MinIO、阿里云 OSS、腾讯云 COS
- **消息队列** - 基于 Redis Stream 的消息队列
- **发布订阅** - 基于 Redis PubSub
- **分布式锁** - 基于 Redis 的分布式锁
- **数据库组件** - Base、Mixins、Types、事件监听
- **多租户模型** - 数据库级隔离的租户设计
- **工具函数** - 字符串、时间、枚举、字典等工具

## 安装

```bash
pip install framework
```

## 快速开始

```python
from framework.config import init_settings, get_settings

# 初始化配置
init_settings("config/")

# 获取配置实例
settings = get_settings()
```

## 文档

详细开发指南请参阅 [CLAUDE.md](./CLAUDE.md)

## 许可证

Copyright © 2025 Moles. All Rights Reserved.
