## 上下文

### 背景

Alon 平台的插件系统是一个成熟的插件生命周期管理框架，需要迁移到 Demo 项目中。该系统包含：

- **ai_plugin**：插件开发 SDK + 服务端运行时（技术框架）
- **ai/components/plugin**：插件管理引擎（业务组件）
- 完整的进程隔离运行时、安全沙箱、多租户支持

### 当前状态

- Demo 项目已有完善的 framework 基础设施
- AI 模块已创建 `components/plugin/` 空目录
- 已有 `framework/utils/crypto.py` 提供 AES-256-GCM 加密能力
- 已有 `framework/storage/` 提供对象存储能力

### 约束

1. 遵循三层架构（Controller → Service → Model）
2. 使用 `Mapped[...]` 声明式字段注解
3. 跨 Schema 外键需要显式创建
4. ai_plugin 作为技术框架独立，不需要 module.py

## 目标 / 非目标

**目标：**

1. 将 Alon 插件系统完整迁移到 Demo 项目
2. 保持插件 SDK 的独立性和可复用性
3. 与现有 framework 基础设施集成
4. 建立与 tenant、iam 模块的外键关联
5. 提供完整的插件生命周期管理 API

**非目标：**

1. 不迁移 ToolStoreService（工具商店服务）
2. 不修改现有业务模块的功能
3. 不在前端实现插件管理界面（本次仅后端）

## 决策

### 决策 1：ai_plugin 独立为顶级目录

**选择**：将 alon_plugin 更名为 ai_plugin，作为 `src/ai_plugin/` 独立顶级目录。

**理由**：
- ai_plugin 是技术框架（类似 framework），不是业务模块
- 提供插件开发 SDK + 服务端运行时，具有独立复用价值
- 职责单一：专门服务于"插件开发"，不混杂业务逻辑

**替代方案**：
- 合并到 `ai/components/plugin/sdk/`：会导致目录结构过于复杂，职责混淆

### 决策 2：凭证加密使用 framework 的 AES-256-GCM

**选择**：使用 `framework/utils/crypto.py` 提供的 AES-256-GCM 加密，而非 Alon 的 base64 简单编码。

**理由**：
- framework 已有更安全的加密实现
- 统一加密方式，避免引入重复代码
- AES-256-GCM 提供认证加密，安全性更高

**实现**：新建 `ai/services/credential_service.py` 封装凭证相关操作。

### 决策 3：插件运行时使用 uv 管理虚拟环境

**选择**：保留 Alon 的设计，使用 uv 管理插件虚拟环境。

**理由**：
- uv 是高性能 Python 包管理器
- 插件需要独立的依赖环境，避免与主应用冲突
- 已在 Alon 项目验证可行

**依赖**：需要在 pyproject.toml 中添加 `uv`、`psutil` 依赖。

### 决策 4：数据库表放在 ai schema

**选择**：插件相关表统一放在 `ai` schema 下。

**理由**：
- 插件是 AI 模块的核心能力
- 遵循模块级 Schema 隔离原则
- 与 AI 模块的其他表保持一致

### 决策 5：跨 Schema 外键显式创建

**选择**：在迁移脚本中使用 `op.create_foreign_key()` 显式创建跨 Schema 外键。

**理由**：
- 遵循项目的跨 Schema 外键处理规范
- Alembic 自动生成的外键会因 schema 缺失导致问题
- 需要指定 `source_schema` 和 `referent_schema`

## 架构设计

### 目录结构

```
src/
├── ai_plugin/                      # 插件开发框架（技术框架）
│   ├── sdk/                        # 插件开发 SDK
│   │   ├── entities/               # 实体定义
│   │   ├── interfaces/             # 接口定义
│   │   ├── errors/                 # 错误定义
│   │   ├── file/                   # 文件操作
│   │   └── schemas/                # Schema 定义
│   ├── server/                     # 插件服务端运行时
│   │   ├── core/                   # 核心模块
│   │   ├── config/                 # 配置
│   │   └── invocations/            # 调用实现
│   └── cli/                        # CLI 工具
│
├── ai/                             # AI 业务模块
│   ├── components/plugin/          # 插件管理组件
│   │   ├── client/                 # 插件客户端
│   │   ├── engine/                 # 插件引擎
│   │   │   ├── api/                # API 路由
│   │   │   ├── config/             # 配置
│   │   │   ├── core/               # 核心模块
│   │   │   │   ├── plugin_manager.py
│   │   │   │   ├── runtime/
│   │   │   │   ├── session/
│   │   │   │   ├── security/
│   │   │   │   ├── communication/
│   │   │   │   ├── monitoring/
│   │   │   │   └── warmup/
│   │   │   ├── models/             # 数据模型
│   │   │   └── utils/              # 工具函数
│   │   ├── commands/               # CLI 命令
│   │   ├── remotable.py
│   │   └── setup.py
│   │
│   ├── services/
│   │   ├── plugin.py               # 插件管理服务
│   │   └── credential_service.py   # 凭证服务
│   │
│   ├── models/
│   │   └── plugin.py               # 插件数据库模型
│   │
│   ├── schemas/
│   │   └── plugin.py               # 插件 Pydantic 模型
│   │
│   ├── controllers/
│   │   ├── admin/v1/plugin.py      # 管理后台接口
│   │   ├── console/v1/plugin.py    # 用户控制台接口
│   │   └── inner/v1/plugin.py      # 内部接口
│   │
│   └── migrations/
│       └── versions/               # 迁移文件
```

### 数据模型

```python
# ai/models/plugin.py

# 枚举定义
class PluginType(EnumBase):
    MODEL = "model"      # AI 模型插件
    TOOL = "tool"        # 工具插件
    AGENT = "agent"      # AI 代理插件
    OAUTH = "oauth"      # OAuth 认证插件
    ENDPOINT = "endpoint"  # 端点插件

class PluginStatus(EnumBase):
    ACTIVE = "active"    # 活跃
    INACTIVE = "inactive"  # 非活跃

class RuntimeType(EnumBase):
    LOCAL = "local"      # 本地运行
    REMOTE = "remote"    # 远程运行
    CONTAINER = "container"  # 容器运行

class CredentialScope(EnumBase):
    GLOBAL = "global"    # 全局
    PERSONAL = "personal"  # 个人（预留）

# 数据库模型
class Plugin(BaseModel, AuditMixin):
    """插件元数据（全局）"""
    __tablename__ = "plugins"

    plugin_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    plugin_unique_identifier: Mapped[str] = mapped_column(String(256), unique=True)
    refers: Mapped[int] = mapped_column(Integer, default=0)
    install_type: Mapped[InstallType] = mapped_column(...)

class PluginInstallation(BaseModel, TenantMixin, AuditMixin):
    """插件安装记录（租户隔离）"""
    __tablename__ = "plugin_installations"

    plugin_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    plugin_unique_identifier: Mapped[str] = mapped_column(String(256), index=True)
    runtime_type: Mapped[RuntimeType] = mapped_column(...)
    plugin_type: Mapped[PluginType] = mapped_column(...)
    status: Mapped[PluginStatus] = mapped_column(default=PluginStatus.ACTIVE)
    # ... 生命周期、运行时信息等字段

class PluginCredential(BaseModel, TenantMixin, AuditMixin):
    """插件凭证（租户隔离）"""
    __tablename__ = "plugin_credentials"

    plugin_id: Mapped[str] = mapped_column(String(128), index=True)
    plugin_type: Mapped[PluginType] = mapped_column(...)
    scope: Mapped[CredentialScope] = mapped_column(default=CredentialScope.GLOBAL)
    name: Mapped[str] = mapped_column(String(128))
    credentials: Mapped[dict] = mapped_column(JSON)
```

### 核心类关系

```
┌─────────────────────────────────────────────────────────────────┐
│                      PluginManagementService                     │
│  (ai/services/plugin.py)                                        │
├─────────────────────────────────────────────────────────────────┤
│  - get_plugin_list()                                            │
│  - install_plugin() / upgrade_plugin() / uninstall_plugin()     │
│  - start_plugin() / stop_plugin()                               │
│  - invoke_plugin_stream()                                       │
│  - 凭证管理方法                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TenantPluginManager                          │
│  (ai/components/plugin/engine/core/plugin_manager.py)           │
├─────────────────────────────────────────────────────────────────┤
│  - plugins: dict[str, PluginInfo]                               │
│  - running_plugins: dict[str, PluginRuntime]                    │
│  - session_manager: SessionManager                              │
│  - security_manager: SecurityManager                            │
│  - performance_monitor: PluginPerformanceMonitor                │
│  - warmup_manager: PluginWarmupManager                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LocalPluginRuntime                           │
│  (ai/components/plugin/engine/core/runtime/local_runtime.py)    │
├─────────────────────────────────────────────────────────────────┤
│  - process: asyncio.subprocess.Process                          │
│  - virtual_env_path: Path                                       │
│  - permissions: PluginPermissions                               │
│  - invoke() / invoke_stream()                                   │
│  - start() / stop()                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 风险 / 权衡

### 风险 1：跨 Schema 外键迁移问题

**风险**：Alembic 自动生成的迁移可能遗漏跨 Schema 外键的正确配置。

**缓解措施**：
- 在迁移脚本中手动创建外键
- 使用 `op.create_foreign_key()` 并指定 `source_schema` 和 `referent_schema`
- 迁移后验证外键约束

### 风险 2：插件进程资源消耗

**风险**：每个插件运行在独立进程中，可能消耗大量系统资源。

**缓解措施**：
- 保留预热管理器，实现懒加载
- 设置插件冻结阈值，自动停止长期未使用的插件
- 监控插件资源使用情况

### 风险 3：凭证安全性

**风险**：插件凭证包含敏感信息，需要确保加密存储。

**缓解措施**：
- 使用 AES-256-GCM 加密
- 主密钥从环境变量获取
- 脱敏显示凭证内容

### 风险 4：uv 依赖安装

**风险**：插件运行时需要 uv 管理虚拟环境，可能存在兼容性问题。

**缓解措施**：
- 在 pyproject.toml 中明确 uv 版本要求
- 提供插件开发文档，说明环境要求
- 支持本地开发模式跳过虚拟环境创建

## 迁移计划

### 阶段 1：基础迁移

1. 创建 `src/ai_plugin/` 目录，迁移 alon_plugin 内容
2. 更新所有导入路径
3. 添加 pyproject.toml 依赖

### 阶段 2：组件迁移

1. 创建 `src/ai/components/plugin/` 目录结构
2. 迁移 engine、client、commands 模块
3. 更新导入路径和依赖注入

### 阶段 3：服务层迁移

1. 创建 `src/ai/services/plugin.py`
2. 创建 `src/ai/services/credential_service.py`
3. 适配 framework 基础设施

### 阶段 4：数据层迁移

1. 创建 `src/ai/models/plugin.py`
2. 创建 `src/ai/schemas/plugin.py`
3. 创建数据库迁移脚本
4. 创建跨 Schema 外键

### 阶段 5：控制器迁移

1. 创建 admin/console/inner 控制器
2. 注册路由到 ai 模块

### 阶段 6：测试与文档

1. 编写单元测试
2. 编写集成测试
3. 更新模块文档

## 开放问题

1. **插件市场集成**：未来是否需要支持从插件市场安装插件？（当前仅支持本地上传）
2. **插件热更新**：是否需要支持插件热更新而不重启进程？
3. **分布式部署**：插件系统在多节点部署时的会话同步策略？
