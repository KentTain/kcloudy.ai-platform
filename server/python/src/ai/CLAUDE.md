# AI 模块开发指南

本文件为 Claude Code 在 src/ai/ AI 模块中工作时提供指导。

## 模块定位

AI 模块负责 AI 相关的能力，包括：LLM、插件、工具等。它是业务模块，可以依赖 ramework 和  enant 模块，但不应把 IAM 专属逻辑下沉到 framework。

**依赖关系：**

- AI → framework（基础设施）
- AI → tenant（通过 inner 接口获取租户信息）

## 目录职责

| 目录 | 职责 |
| --- | --- |
| controllers/ | FastAPI 路由控制器，包含 admin、console 和 inner 三层 |
| services/ | 模型、插件、工具等业务逻辑 |
| models/ | 模型、插件、工具等数据库模型与枚举 |
| schemas/ | 请求、响应、模型、插件、工具等 Pydantic 模型 |
| migrations/ | 模型、插件、工具等数据库迁移与种子数据 |
| middlewares/ | 模型、插件、工具等鉴权与租户上下文中间件 |
| components/ | AI 组件模块，包含 graphrag、model、plugin 等子模块 |
| components/graphrag/ | GraphRAG 图检索增强生成组件 |
| components/model/ | LLM 模型适配与管理组件 |
| components/plugin/ | 插件系统核心组件 |

## 接口分层

| 前缀 | 用途 | 权限 |
| --- | --- | --- |
| /admin/v1/models | 管理后台模型管理 | 系统管理员 |
| /console/v1/models | 用户端接口（个人中心） | 登录用户 |
| /inner/v1/models | 内部接口，供模块间调用 | 无（模块内部调用） |
| /inner/v1/plugins | 内部接口，插件管理 | 无（模块内部调用） |
| /inner/v1/tools | 内部接口，工具管理 | 无（模块内部调用） |

## 角色体系

| 角色 | 职责 | 场景 |
| --- | --- | --- |
| 系统管理员 | 管理本租户模型、插件、工具 | 租户内管理操作 |
| 普通用户 | 使用业务功能与维护个人信息 | 日常登录和业务访问 |

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装；业务逻辑放在 Service。
- Service 负责事务边界、业务校验和跨模型协作；不要在 Controller 中直接拼装复杂查询。
- Model 使用 framework 的数据库基类、Mixin 和 SQLAlchemy 2.0 声明式类型。
- Schema 区分请求 DTO、响应 VO 和内部数据结构，避免把数据库模型直接暴露给 API。

## 内部接口

AI 模块提供以下内部接口供其他模块调用：

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| /inner/v1/models/{model_id} | GET | 获取单个模型 |
| /inner/v1/models/batch | POST | 批量获取模型 |
| /inner/v1/plugins/{plugin_id} | GET | 获取单个插件 |
| /inner/v1/plugins/batch | POST | 批量获取插件 |
| /inner/v1/tools/{tool_id} | GET | 获取单个工具 |
| /inner/v1/tools/batch | POST | 批量获取工具 |
| /inner/v1/health | GET | 健康检查 |

调用方式支持两种模式：

- **单体模式**：直接调用 ModelService、PluginService、ToolService 方法
- **微服务模式**：通过 IamClient（ramework/clients/iam_client.py）HTTP 调用

## 数据库模型

| 模型 | 说明 | Schema |
| --- | --- | --- |
| Model | 模型实体 | ai.models |
| Plugin | 插件实体 | ai.plugins |
| Tool | 工具实体 | ai.tools |

## API 入口

| 前缀 | 用途 |
| --- | --- |
| /api/v1/auth | 登录、刷新 Token 等认证接口 |
| /api/v1/models | 模型管理 |
| /api/v1/plugins | 插件管理 |
| /api/v1/tools | 工具管理 |

以实际路由注册为准，修改接口时同步检查对应 Controller、Schema、Service 和测试。

## 插件系统架构

AI 模块包含完整的插件系统实现，支持 Dify 风格的插件运行时管理。

### 核心组件

| 组件 | 路径 | 职责 |
| --- | --- | --- |
| PluginManager | `components/plugin/engine/core/plugin_manager.py` | 插件生命周期管理 |
| PluginDaemon | `components/plugin/engine/core/` | 插件守护进程 |
| Runtime | `components/plugin/engine/core/runtime/` | 插件运行时（Local/Process/Docker） |
| SessionManager | `components/plugin/engine/core/session/` | 插件会话管理 |
| Security | `components/plugin/engine/core/security/` | 插件安全沙箱 |
| Monitoring | `components/plugin/engine/core/monitoring/` | 插件监控与日志 |
| Communication | `components/plugin/engine/core/communication/` | 插件通信协议 |
| Warmup | `components/plugin/engine/core/warmup/` | 插件预热机制 |

### 插件客户端

| 客户端 | 路径 | 职责 |
| --- | --- | --- |
| ModelClient | `components/plugin/client/model_client.py` | 模型调用客户端 |
| ToolClient | `components/plugin/client/tool_client.py` | 工具调用客户端 |
| StreamPrinter | `components/plugin/client/stream_printer.py` | 流式响应处理 |

### 插件类型

支持以下插件类型：

- **Model**: 大语言模型插件
- **Tool**: 工具插件
- **Agent**: Agent 策略插件

### 数据库表

| 表名 | 说明 | 租户隔离 |
| --- | --- | --- |
| `ai.plugins` | 插件全局注册表 | 否 |
| `ai.plugin_declarations` | 插件声明缓存 | 否 |
| `ai.plugin_installations` | 插件安装实例 | 是 |
| `ai.plugin_install_tasks` | 批量安装任务 | 是 |
| `ai.plugin_credentials` | 插件凭证 | 是 |

### API 端点

| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/admin/v1/plugins` | GET | 插件列表 |
| `/admin/v1/plugins/{plugin_id}` | GET | 获取插件详情 |
| `/admin/v1/plugins/install` | POST | 安装插件 |
| `/admin/v1/plugins/{plugin_id}/uninstall` | POST | 卸载插件 |
| `/admin/v1/plugins/{plugin_id}/start` | POST | 启动插件 |
| `/admin/v1/plugins/{plugin_id}/stop` | POST | 停止插件 |
| `/console/v1/plugins` | GET | 用户端插件列表 |
| `/inner/v1/plugins/{plugin_id}` | GET | 内部插件接口 |

### 插件开发

开发插件使用 `ai_plugin` SDK（`src/ai_plugin/`）：

```python
from ai_plugin import Plugin

plugin = Plugin()

@plugin.tool()
def my_tool(query: str) -> str:
    """工具描述"""
    return f"处理结果: {query}"

if __name__ == "__main__":
    plugin.run()
```

### 扩展阅读

- 插件引擎设计: `components/plugin/engine/`
- 插件客户端使用: `components/plugin/client/`
- 插件命令行工具: `components/plugin/commands/`

## 测试

AI 相关能力当前主要通过 framework 租户集成测试和 AI 服务 / 控制器测试覆盖。新增模型、插件、工具逻辑时，应补充以下测试：

- Service 单元测试：业务规则、异常路径、事务行为。
- API 集成测试：鉴权、租户上下文、权限边界。
- Seed / migration 验证：默认模型、插件、工具与数据库结构一致。

通用测试命令和标记见 [../../tests/CLAUDE.md](../../tests/CLAUDE.md)。
