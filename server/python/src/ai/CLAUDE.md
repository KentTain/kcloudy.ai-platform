# AI 模块开发指南

本文件为 Claude Code 在 `src/ai/` AI 模块中工作时提供指导。

## 模块定位

AI 模块负责 AI 相关的能力，包括：LLM、插件、工具等。它是业务模块，可以依赖 framework 和 tenant 模块。

## 依赖边界

```
ai ──▶ framework（基础设施）
ai ──▶ tenant（通过 inner 接口获取租户信息）
```

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 模型、插件、工具等业务逻辑 |
| models/ | 模型、插件、工具等数据库模型 |
| schemas/ | 请求、响应等 Pydantic 模型 |
| migrations/ | 数据库迁移与种子数据 |
| middlewares/ | 鉴权与租户上下文中间件 |
| components/ | AI 组件模块（graphrag、model、plugin） |

## 接口分层

| 前缀 | 用途 | 权限 |
|------|------|------|
| /admin/v1/models | 管理后台模型管理 | 系统管理员 |
| /console/v1/models | 用户端接口 | 登录用户 |
| /inner/v1/models | 内部接口，供模块间调用 | 无（模块内部调用） |

## 核心组件

| 组件 | 路径 | 职责 |
|------|------|------|
| LLMService | components/model/services/ | LLM 调用统一入口 |
| EmbeddingService | components/model/services/ | 文本嵌入服务 |
| RerankService | components/model/services/ | 重排序服务 |
| PluginManager | components/plugin/engine/ | 插件生命周期管理 |
| ModelInstanceFactory | components/model/internal/ | 模型实例创建工厂 |

## 插件系统

支持以下插件类型：
- **Model**: 大语言模型插件
- **Tool**: 工具插件
- **Agent**: Agent 策略插件

### 数据库表

| 表名 | 说明 | 租户隔离 |
|------|------|----------|
| ai.plugins | 插件全局注册表 | 否 |
| ai.plugin_installations | 插件安装实例 | 是 |
| ai.plugin_credentials | 插件凭证 | 是 |

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- Model 使用 framework 的数据库基类、Mixin
- Schema 区分请求 DTO、响应 VO 和内部数据结构

## 测试

AI 相关能力主要通过 framework 租户集成测试和 AI 服务/控制器测试覆盖。

```bash
uv run pytest tests/ai/ -v
```

详细插件系统说明、API 端点见 [README.md](README.md)。
