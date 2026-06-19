## 为什么

Alon 平台的插件系统是一套完整的插件生命周期管理框架，包含插件安装/卸载/升级、进程级隔离运行时、安全沙箱、多租户支持和凭证加密管理。当前 Demo 项目缺少插件管理能力，需要将 Alon 的插件系统整体迁移，以提供可扩展的 AI 能力插件化支持。

## 变更内容

### 新增

- **ai_plugin/ 顶级目录**：插件开发框架（SDK + 服务端运行时 + CLI），作为技术框架独立存在
- **ai/components/plugin/ 目录**：插件管理引擎，包含 client、engine、commands 等组件
- **ai/services/plugin.py**：插件管理服务层，提供插件生命周期管理和凭证管理
- **ai/models/plugin.py**：插件相关数据库模型（Plugin、PluginInstallation、PluginCredential 等）
- **ai/schemas/plugin.py**：插件相关 Pydantic 模型
- **ai/controllers/\*/plugin.py**：插件管理 API 控制器（admin/console/inner）
- **ai/services/credential_service.py**：凭证加密/解密/脱敏服务
- **数据库迁移**：在 ai schema 下创建插件相关表

### 依赖

- 新增 `uv`、`psutil`、`pyyaml` 等 Python 依赖
- 使用 `framework/utils/crypto.py` 提供的 AES-256-GCM 加密能力
- 使用 `framework/storage/` 提供的对象存储能力

## 功能 (Capabilities)

### 新增功能

- `plugin-runtime`: 插件运行时管理 - 插件进程生命周期管理、虚拟环境隔离、通信协议
- `plugin-installation`: 插件安装管理 - 插件包上传、解析、安装、升级、卸载
- `plugin-credential`: 插件凭证管理 - 凭证加密存储、脱敏显示、格式校验
- `plugin-asset`: 插件资源管理 - 插件图标、静态资源的 OSS 存储与访问
- `plugin-sdk`: 插件开发 SDK - 供插件开发者使用的 SDK 和服务端运行时

### 修改功能

无（这是新增模块，不涉及现有功能修改）

## 影响

### 代码影响

| 目录/文件 | 影响类型 |
|-----------|----------|
| `src/ai_plugin/` | 新增顶级目录（技术框架） |
| `src/ai/components/plugin/` | 新增组件目录 |
| `src/ai/services/plugin.py` | 新增服务 |
| `src/ai/services/credential_service.py` | 新增服务 |
| `src/ai/models/plugin.py` | 新增模型 |
| `src/ai/schemas/plugin.py` | 新增 Schema |
| `src/ai/controllers/admin/v1/plugin.py` | 新增控制器 |
| `src/ai/controllers/console/v1/plugin.py` | 新增控制器 |
| `src/ai/controllers/inner/v1/plugin.py` | 新增控制器 |
| `src/ai/migrations/versions/` | 新增迁移文件 |
| `pyproject.toml` | 新增依赖 |

### API 影响

| 端点 | 用途 |
|------|------|
| `POST /admin/v1/plugins/upload` | 上传安装插件 |
| `POST /admin/v1/plugins/{plugin_id}/upgrade` | 升级插件 |
| `DELETE /admin/v1/plugins/{plugin_id}` | 卸载插件 |
| `POST /admin/v1/plugins/{plugin_id}/start` | 启动插件 |
| `POST /admin/v1/plugins/{plugin_id}/stop` | 停止插件 |
| `GET /console/v1/plugins` | 获取插件列表 |
| `GET /console/v1/plugins/{plugin_id}` | 获取插件详情 |
| `GET /console/v1/plugins/{plugin_id}/credentials` | 获取插件凭证列表 |
| `POST /console/v1/plugins/{plugin_id}/credentials` | 创建插件凭证 |
| `PUT /console/v1/plugins/{plugin_id}/credentials/{credential_id}` | 更新插件凭证 |
| `DELETE /console/v1/plugins/{plugin_id}/credentials/{credential_id}` | 删除插件凭证 |
| `GET /inner/v1/plugins/{plugin_id}` | 内部接口：获取插件信息 |
| `GET /inner/v1/plugins/{plugin_id}/invoke` | 内部接口：调用插件 |

### 数据库影响

| 表名 | Schema | 说明 |
|------|--------|------|
| `plugins` | ai | 插件元数据（全局） |
| `plugin_installations` | ai | 插件安装记录（租户隔离） |
| `plugin_credentials` | ai | 插件凭证（租户隔离） |
| `plugin_install_tasks` | ai | 插件安装任务 |
| `plugin_declarations` | ai | 插件声明 |

### 外键关联

| 表 | 字段 | 关联 |
|----|------|------|
| `ai.plugin_installations` | tenant_id | → `tenant.tenants.id` |
| `ai.plugin_installations` | created_by | → `iam.users.id` |
| `ai.plugin_credentials` | tenant_id | → `tenant.tenants.id` |
| `ai.plugin_credentials` | created_by | → `iam.users.id` |

### 配置影响

需要在 `settings.py` 中新增插件相关配置：
- 插件基础目录
- 插件运行时配置
- 插件预热配置
