## 上下文

### 当前状态

项目已有基础的插件管理架构：
- `TenantPluginDefinition` 模型：全局插件注册表（`tenant.plugin_definitions`）
- `TenantPluginInstallation` 模型：租户级安装记录（`tenant.plugin_installations`）
- `PluginInstallationProvider` 协议：Tenant 与 AI 模块的契约接口
- `PluginManagerFactory`：多租户插件管理器工厂
- `TenantPluginManager`：单个租户的插件生命周期管理
- 事件监听器：处理安装/卸载失败事件

### 约束

- 遵循现有三层架构（Controller → Service → Model）
- 使用现有基础设施（PostgreSQL、Redis、MinIO）
- 保持与现有 `PluginInstallationProvider` 协议的兼容性
- 插件安装流程改为异步，需保证数据一致性

### 利益相关者

| 角色 | 关注点 |
|------|--------|
| 平台管理员 | 插件定义的注册、管理、统计 |
| 租户管理员 | 插件的安装、配置、监控 |
| 开发团队 | 代码可维护性、扩展性 |

## 目标 / 非目标

**目标：**

1. 实现插件定义的全生命周期管理（注册、查询、标记、删除）
2. 实现插件安装的异步工作流（任务队列、进度追踪）
3. 实现插件运行时的可视化管理（启动、停止、配置、监控）
4. 提供统一的权限控制机制
5. 统一插件包存储策略（MinIO）

**非目标：**

1. 远程 URL 拉取注册（后续迭代）
2. Docker/.venv 隔离策略（后续迭代）
3. 配额管理、插件市场、审批流程（后续迭代）
4. 前端页面实现（阶段 2）

## 决策

### 1. 插件包存储策略

**决策**：所有插件包统一上传到 MinIO

**理由**：
- 统一存储路径，便于管理和清理
- MinIO 支持预签名 URL，便于安全下载
- 避免服务器目录依赖，支持分布式部署

**流程**：
```
输入（文件路径或上传文件）→ 解析 manifest → 计算校验和 → 上传 MinIO → 注册
```

**存储路径**：
- Bucket: `plugins`
- Object Key: `{plugin_id}/{version}.zip`
- 示例: `langgenius/ollama/1.0.0.zip`

**替代方案**：
- 服务器目录扫描保留本地路径 → 部署灵活性差
- 不上传 MinIO → 无法统一管理

### 2. 安装任务队列

**决策**：使用 Redis Stream + 数据库任务表

**理由**：
- 项目已有 Redis Stream 封装（`framework.queue`）
- 无需引入 Celery 等额外依赖
- 任务状态持久化到数据库，支持重启恢复

**架构**：
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 安装 API     │───▶│ Redis Stream │───▶│ 任务消费者   │
│ 创建任务     │    │ 任务队列     │    │ 执行安装     │
└──────────────┘    └──────────────┘    └──────────────┘
       │                                        │
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│ plugin_      │                        │ 更新任务状态 │
│ install_     │                        │ 发布事件     │
│ tasks 表     │                        └──────────────┘
└──────────────┘
```

**替代方案**：
- Celery → 需要额外部署 worker，复杂度高
- asyncio.create_task → 进程重启后任务丢失

### 3. 数据一致性保障

**决策**：事件驱动 + 最终一致性

**安装流程**：
```
1. AI API 创建安装任务 → plugin_install_tasks 表
2. AI API 调用 Tenant Provider → 创建 plugin_installations 记录（PENDING）
3. 任务消费者执行安装：
   - 成功：更新安装状态为 ACTIVE
   - 失败：发布 PluginInstallationFailed 事件
4. Tenant 监听器处理失败事件 → 删除或更新安装记录
```

**回滚机制**：
- 安装失败：Tenant 监听器删除 `plugin_installations` 记录
- 定时任务：清理超过 24 小时的 PENDING 状态记录

### 4. 权限模型

**决策**：细粒度权限控制

| 模块 | 权限码 | 说明 |
|------|--------|------|
| tenant | `tenant:plugin:read` | 查看插件定义 |
| tenant | `tenant:plugin:write` | 管理插件定义（注册、标记、删除） |
| ai | `ai:plugin:read` | 查看插件 |
| ai | `ai:plugin:write` | 管理插件（安装、启动、停止、配置） |
| ai | `ai:plugin:delete` | 卸载插件 |

**实现**：
- 在 `iam` 模块注册权限定义
- Controller 层使用 `@require_permission` 装饰器

### 5. API 路由设计

**决策**：遵循现有路由规范

| 模块 | 类型 | 路径前缀 | 认证方式 |
|------|------|----------|----------|
| tenant | admin | `/tenant/admin/v1/plugin-definitions` | AdminAuthMiddleware |
| ai | console | `/ai/console/v1/plugins` | IAMAuthMiddleware |

## 风险 / 权衡

### 风险 1：安装过程中 AI 侧创建失败，Tenant 侧记录已存在

**风险描述**：Tenant Provider 创建 `plugin_installations` 成功，但 AI 侧 `plugin_configs` 创建失败。

**缓解措施**：
- 事件驱动：发布 `PluginInstallationFailed` 事件
- Tenant 监听器：删除或更新安装记录
- 定时任务：清理孤儿记录

### 风险 2：缓存一致性

**风险描述**：`PluginManager.plugins` 是内存缓存，其他进程修改 `plugin_installations` 后缓存不更新。

**缓解措施**：
- 缓存 TTL = 60 秒
- 关键操作后主动刷新缓存

### 风险 3：插件定义删除时仍有租户在使用

**风险描述**：删除 `plugin_definitions` 记录时，`refers > 0`。

**缓解措施**：
- `refers > 0` 时禁止删除
- 提供"禁用"操作（`is_enabled = false`）作为软删除

### 风险 4：MinIO 存储空间

**风险描述**：大量插件包占用存储空间。

**缓解措施**：
- 删除插件定义时同时删除 MinIO 上的插件包
- 实现版本清理策略（保留最近 N 个版本）

## 迁移计划

### 数据库迁移

1. **新增字段**：`tenant.plugin_definitions`
   ```sql
   ALTER TABLE tenant.plugin_definitions
   ADD COLUMN is_recommended BOOLEAN NOT NULL DEFAULT false,
   ADD COLUMN is_enabled BOOLEAN NOT NULL DEFAULT true;
   ```

2. **新建表**：`ai.plugin_install_tasks`
   ```sql
   CREATE TABLE ai.plugin_install_tasks (
     id VARCHAR(64) PRIMARY KEY,
     tenant_id VARCHAR(64) NOT NULL,
     plugin_id VARCHAR(128) NOT NULL,
     status VARCHAR(16) NOT NULL DEFAULT 'pending',
     progress INTEGER DEFAULT 0,
     current_step VARCHAR(64),
     steps JSONB,
     error_message TEXT,
     started_at TIMESTAMP,
     completed_at TIMESTAMP,
     created_at TIMESTAMP NOT NULL DEFAULT now(),
     updated_at TIMESTAMP NOT NULL DEFAULT now()
   );
   ```

### 权限数据

在 `iam` 模块的种子数据中添加：
- `tenant:plugin:read`、`tenant:plugin:write`
- `ai:plugin:read`、`ai:plugin:write`、`ai:plugin:delete`

### 回滚策略

- 数据库迁移使用 Alembic，支持 `downgrade`
- 权限数据删除对应记录
- MinIO 上的插件包保留（可手动清理）

## 开放问题

1. **安装任务超时处理**：任务执行超过阈值时如何处理？
   - 建议：设置 30 分钟超时，超时后标记为 FAILED

2. **插件版本更新**：同一插件新版本发布后，已安装租户如何感知？
   - 建议：后续迭代实现版本更新通知

3. **多租户隔离的下载链接**：MinIO 预签名 URL 如何防止跨租户下载？
   - 建议：下载 API 通过后端代理，验证租户权限后返回文件流
