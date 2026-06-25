# Tenant 模块开发指南

本文件为 Claude Code 在 `src/tenant/` 租户管理模块中工作时提供指导。

## 模块定位

Tenant 模块负责多租户系统的核心租户管理功能，包括：
- 租户 CRUD、租户配置、全局管理员管理
- **插件资源管理**（2026-06-25 架构变更）：插件定义、安装记录管理
- 提供 `PluginInstallationProvider` 协议供 AI 模块访问

它是基础模块，无依赖其他业务模块。

## 依赖边界

```
IAM / Demo / AI ──▶ Tenant
Tenant ──X──▶ IAM / Demo / AI
```

- IAM、Demo 和 AI 模块可依赖 Tenant
- Tenant 不依赖其他业务模块
- AI 模块通过 `PluginInstallationProvider` 访问 Tenant 侧插件数据

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 租户业务逻辑、TenantProvider 实现、**PluginInstallationProvider 实现** |
| models/ | 租户数据库模型（Tenant、TenantConfig、TenantAdmin、**PluginDefinition、PluginInstallation**） |
| schemas/ | 请求、响应 Pydantic 模型 |
| migrations/ | 租户数据库迁移与 seed 数据 |
| listeners/ | 事件监听器（处理插件安装/卸载失败事件） |

## 接口分层

Tenant 模块 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 类型 | 路由前缀 | 用途 | 权限 |
|------|---------|------|------|
| admin | `/tenant/admin/v1/tenants` | 管理后台租户 CRUD | 租户管理员 Token |
| console | `/tenant/console/v1/tenants` | 用户端租户接口 | JWT Token |
| inner | `/tenant/inner/v1/tenants` | 内部接口，供模块间调用 | 无认证 |

### 完整路由表

#### 租户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/admin/v1/tenants` | 获取租户列表 |
| POST | `/tenant/admin/v1/tenants` | 创建租户 |
| GET | `/tenant/admin/v1/tenants/{id}` | 获取租户详情 |
| PUT | `/tenant/admin/v1/tenants/{id}` | 更新租户 |
| DELETE | `/tenant/admin/v1/tenants/{id}` | 删除租户 |
| GET | `/tenant/console/v1/tenants/current` | 获取当前租户信息 |
| GET | `/tenant/inner/v1/tenants/{id}` | 内部接口：获取租户信息 |

#### 插件资源管理（2026-06-25 新增）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenant/admin/v1/plugins` | 获取插件定义列表 |

**注意**：插件安装记录的 CRUD 通过 `PluginInstallationProvider` 协议提供给 AI 模块，不直接暴露 HTTP API。

## 数据库模型

### 租户管理

| 模型 | 说明 | Schema |
|------|------|--------|
| Tenant | 租户实体 | tenant.tenants |
| TenantConfig | 租户资源配置 | tenant.tenant_configs |
| TenantAdmin | 全局管理员账号 | tenant.tenant_admins |

### 插件资源管理（2026-06-25 新增）

| 模型 | 说明 | Schema |
|------|------|--------|
| TenantPluginDefinition | 全局插件注册表（替代原 ai.plugins + ai.plugin_declarations） | tenant.plugin_definitions |
| TenantPluginInstallation | 租户级安装记录（仅管理面字段） | tenant.plugin_installations |

**架构说明**：
- `plugin_definitions`：管理"有什么"（插件定义），支持引用计数
- `plugin_installations`：管理"用什么"（安装记录），租户隔离
- 插件配置和运行时状态由 AI 模块管理（ai.plugin_configs、ai.plugin_runtime_states）

## 开发规则

- Controller 只处理路由、参数校验和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- 敏感配置（数据库密码、加密密钥）使用 AES-256-GCM 加密保存

## Provider 协议（2026-06-25 新增）

### PluginInstallationProvider

Tenant 模块提供 `PluginInstallationProvider` 协议实现，供 AI 模块访问插件安装记录。

**协议定义**：`framework/tenant/plugin_protocols.py`

```python
class PluginInstallationProvider(Protocol):
    """插件安装提供者协议"""
    
    async def get_tenant_installations(self, tenant_id: str) -> list[PluginInstallationDTO]: ...
    async def get_installation(self, tenant_id: str, plugin_id: str) -> PluginInstallationDTO | None: ...
    async def create_installation(self, tenant_id: str, data: PluginInstallationDTO) -> PluginInstallationDTO: ...
    async def update_installation(self, tenant_id: str, plugin_id: str, data: dict) -> PluginInstallationDTO: ...
    async def delete_installation(self, tenant_id: str, plugin_id: str) -> None: ...
```

**协议实现**：`tenant/services/plugin_provider.py`

```python
from framework.tenant.plugin_protocols import get_plugin_installation_provider

# AI 模块使用示例
provider = get_plugin_installation_provider()
installation = await provider.get_installation(tenant_id, plugin_id)
```

**注册机制**：
```python
# application_web.py 启动时注册
from framework.tenant.plugin_protocols import register_plugin_installation_provider
from tenant.services.plugin_provider import plugin_installation_provider_impl

register_plugin_installation_provider(plugin_installation_provider_impl)
```

### 依赖倒置

通过 Provider 协议实现依赖倒置：
- AI 模块依赖抽象接口（Protocol），不直接访问 Tenant Schema
- Tenant 模块实现接口，提供具体数据访问
- 便于测试和模块解耦

## 事件监听器（2026-06-25 新增）

Tenant 模块提供事件监听器，处理插件安装/卸载失败事件。

### 文件位置

```
tenant/listeners/
├── __init__.py
├── handlers/
│   ├── __init__.py
│   └── plugin_handler.py
└── setup.py
```

### 启动监听器

在应用启动时调用：

```python
from tenant.listeners.setup import setup_listeners

await setup_listeners(settings)
```

### 停止监听器

在应用关闭时调用：

```python
from tenant.listeners.setup import cleanup_listeners

await cleanup_listeners()
```

### 事件处理器

| 事件 | 处理器 | 说明 |
|------|--------|------|
| PluginInstallationFailed | PluginInstallationFailedHandler | 更新安装记录状态为 FAILED |
| PluginUninstallFailed | PluginUninstallFailedHandler | 记录失败日志 |

### 工作原理

1. 监听器使用 Redis Stream 消费者组模式
2. 接收 AI 模块发布的事件消息
3. 解析消息并调用对应的处理器
4. 处理成功后确认消息（ACK）

## 测试

```bash
uv run pytest tests/tenant/ -v
```
