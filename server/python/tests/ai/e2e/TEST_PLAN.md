# 插件功能 E2E 测试计划

## 文档信息

| 项目 | 说明 |
|------|------|
| 模块 | AI 插件系统 |
| 测试类型 | E2E（端到端测试） |
| 测试目录 | `server/python/tests/ai/e2e/` |
| 创建日期 | 2026-07-02 |
| 最后更新 | 2026-07-02 |

---

## 一、测试目标

### 1.1 核心目标

验证插件系统在真实环境下的完整业务流程，包括：

- ✅ 插件生命周期管理（安装、启动、停止、卸载）
- ✅ 插件配置与凭证管理
- ✅ 插件模型调用功能
- ✅ 插件运行时状态监控
- ✅ 多租户隔离机制
- ✅ 资源清理与异常处理

### 1.2 质量指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 核心流程覆盖率 | 100% | 所有核心业务流程必须有测试覆盖 |
| 边界场景覆盖率 | ≥ 80% | 异常、错误、边界条件 |
| 测试稳定性 | ≥ 95% | 通过率，允许少量外部依赖失败 |
| 执行时间 | ≤ 5 分钟 | 单个测试用例执行时间 |

---

## 二、系统架构

### 2.1 插件系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       前端应用层                              │
│          (Vue Admin / Console / 租户管理后台)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     API 控制器层                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ Admin API    │  │ Console API  │  │ Inner API    │    │
│   │ /ai/admin/v1 │  │/ai/console/v1│  │ /ai/inner/v1 │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     服务层 (Service)                         │
│   ┌──────────────────┐  ┌───────────────────────────────┐  │
│   │ PluginManagement │  │ PluginInstallationProvider    │  │
│   │     Service      │  │ (Tenant Module)               │  │
│   └──────────────────┘  └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   插件管理器 (PluginManager)                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │TenantManager │  │RuntimeFactory│  │SecurityManager│   │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   插件运行时 (Runtime)                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │LocalRuntime  │  │RemoteRuntime │  │ DaemonRuntime│    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据持久层 (Database)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │tenant.plugins│  │ai.plugin_    │  │ai.plugin_    │    │
│   │_installations│  │configs       │  │runtime_states│    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型关系

```
┌──────────────────────────────┐
│ tenant.plugin_definitions    │  全局插件注册表
│ - plugin_id (PK)             │
│ - name, version, type        │
│ - declaration (JSONB)        │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│ tenant.plugin_installations  │  租户级安装记录
│ - tenant_id (PK)             │
│ - plugin_id (PK)             │
│ - status, version            │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│ ai.plugin_configs            │  插件配置
│ - tenant_id (PK)             │
│ - plugin_id (PK)             │
│ - plugin_config (JSONB)      │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│ ai.plugin_runtime_states     │  运行时状态
│ - tenant_id (PK)             │
│ - plugin_id (PK)             │
│ - state, pid, port           │
└──────────────────────────────┘
```

---

## 三、测试范围

### 3.1 功能范围

| 功能模块 | 测试文件 | 优先级 | 状态 |
|----------|----------|--------|------|
| 插件安装 | `test_plugin_install.py` | P0 | ✅ 已实现 |
| 插件运行时 | `test_plugin_runtime.py` | P0 | ✅ 已实现 |
| 插件配置 | `test_plugin_configure.py` | P0 | ✅ 已实现 |
| 模型调用 | `test_plugin_invoke.py` | P0 | ✅ 已实现 |
| 完整生命周期 | `test_plugin_full_lifecycle.py` | P0 | ✅ 已实现 |
| 事件监听 | `test_event_listeners.py` | P1 | ✅ 已实现 |
| 插件解析 | `test_plugin_parse.py` | P1 | ✅ 已实现 |

### 3.2 非功能范围

| 类型 | 测试内容 | 优先级 | 状态 |
|------|----------|--------|------|
| 性能测试 | 并发安装、批量启动 | P2 | 🚧 待实现 |
| 稳定性测试 | 崩溃恢复、异常处理 | P1 | ⚠️ 部分实现 |
| 安全测试 | 凭证加密、租户隔离 | P1 | 🚧 待实现 |

---

## 四、测试环境

### 4.1 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.12+ | 运行时环境 |
| PostgreSQL | 14+ | 数据库（含 pgvector） |
| Redis | 6+ | 缓存 / 队列 |
| MinIO | Latest | 对象存储（可选） |
| uv | Latest | Python 包管理器 |

### 4.2 环境变量配置

#### 4.2.1 配置文件位置

| 配置类型 | 文件位置 | 说明 |
|----------|----------|------|
| **基础设施配置** | `server/python/tests/conftest.py` | PostgreSQL、Redis、MinIO 服务检测与连接 |
| **API Key 配置** | `server/python/tests/ai/conftest.py` | tongyi、gpustack 等 API Key |
| **应用配置** | `server/config/application-local.yml` | 数据库连接、Redis、MinIO 配置 |

#### 4.2.2 API Key 环境变量

测试使用的 API Key 配置（**推荐使用环境变量覆盖默认值**）：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `E2E_TONGYI_API_KEY` | `sk-623fdfb2b75f43b8bb6a61b8b183359a` | 通义千问 API Key（模型调用测试） |
| `E2E_GPUSTACK_API_KEY` | `gpustack_14d9f2aee5629a0f_465d73985f7b8f370caecd9e3de838ec` | GPUStack API Key（模型调用测试） |
| `E2E_GPUSTACK_ENDPOINT` | `https://llm-stack.flydiysz.cn` | GPUStack 服务端点 |

**GPUStack 可用模型**（配置文件中预定义）：

```python
GPUSTACK_AVAILABLE_MODELS = [
    "qwen3.5-9b",              # 聊天模型
    "bge-large-zh-v1.5",       # Embedding 模型
    "bge-reranker-large",      # Reranker 模型
    "qwen3-embedding-0.6b",    # Embedding 模型
    "qwen3-reranker-0.6b",     # Reranker 模型
]
```

#### 4.2.3 数据库与服务配置

数据库连接配置位于 `server/config/application-local.yml`：

```yaml
# 示例配置
sqlalchemy:
  url: postgresql+asyncpg://admin:password@localhost:5432/kcloudy_test

redis:
  single:
    host: localhost
    port: 6379

oss:
  minio:
    endpoint: localhost:9000
    access_key: minioadmin
    secret_key: minioadmin
    bucket: kcloudy-test
```

**配置加载优先级**：

1. 环境变量（最高优先级）
2. `application-local.yml`
3. `application.yml`（默认配置）

#### 4.2.4 配置验证脚本

```bash
#!/bin/bash
# 验证测试环境配置

echo "=== 检查环境变量 ==="
echo "TONGYI_API_KEY: ${E2E_TONGYI_API_KEY:-(使用默认值)}"
echo "GPUSTACK_API_KEY: ${E2E_GPUSTACK_API_KEY:-(使用默认值)}"
echo "GPUSTACK_ENDPOINT: ${E2E_GPUSTACK_ENDPOINT:-(使用默认值)}"

echo -e "\n=== 检查 PostgreSQL ==="
psql -h localhost -U postgres -c "SELECT version();" 2>&1 || echo "PostgreSQL 连接失败"

echo -e "\n=== 检查 Redis ==="
redis-cli ping 2>&1 || echo "Redis 连接失败"

echo -e "\n=== 检查 MinIO ==="
curl -s http://localhost:9000/minio/health/live && echo "MinIO 正常" || echo "MinIO 不可用（可选）"

echo -e "\n=== 检查插件包 ==="
ls -lh plugins/*.zip | head -n 5 || echo "插件包不存在"
```

### 4.3 插件包准备

测试使用的插件包位于项目根目录 `server/plugins` 下：

| 插件 ID | 文件名 | 用途 |
|---------|--------|------|
| tongyi | `langgenius-tongyi_0.2.0.zip` | 模型调用测试 |
| gpustack | `langgenius-gpustack_0.0.15.zip` | 模型调用测试 |
| ollama | `langgenius-ollama_1.0.0.zip` | 安装测试 |

---

## 五、测试用例设计

### 5.1 P0 核心测试用例

#### 5.1.1 插件安装流程（test_plugin_install.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| INSTALL-001 | 安装 tongyi 插件并验证虚拟环境 | 1. 上传插件包<br>2. 调用安装 API<br>3. 验证虚拟环境创建<br>4. 验证 OSS 上传 | ✅ 安装状态 ACTIVE<br>✅ 虚拟环境存在<br>✅ OSS 文件存在 |
| INSTALL-002 | 重复安装相同插件 | 1. 安装 tongyi 插件<br>2. 再次安装相同插件 | ❌ 返回错误：插件已安装 |
| INSTALL-003 | 卸载已安装插件 | 1. 安装插件<br>2. 卸载插件<br>3. 验证资源清理 | ✅ 安装记录删除<br>✅ 虚拟环境清理<br>✅ OSS 文件删除 |
| INSTALL-004 | 安装无效插件包 | 1. 上传无效 zip 文件 | ❌ 返回错误：无效插件包格式 |

#### 5.1.2 插件运行时管理（test_plugin_runtime.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| RUNTIME-001 | 启动插件并验证进程 | 1. 安装插件<br>2. 启动插件<br>3. 验证进程存在 | ✅ 进程 PID 有效<br>✅ 状态为 RUNNING |
| RUNTIME-002 | 停止运行中的插件 | 1. 启动插件<br>2. 停止插件<br>3. 验证进程退出 | ✅ 进程已退出<br>✅ 状态为 STOPPED |
| RUNTIME-003 | 查询插件运行时状态 | 1. 启动插件<br>2. 查询运行时状态 | ✅ 返回 PID、端口、状态 |
| RUNTIME-004 | 插件崩溃后状态更新 | 1. 启动插件<br>2. 强制杀掉进程<br>3. 查询状态 | ✅ 状态更新为 CRASHED |

#### 5.1.3 插件配置管理（test_plugin_configure.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| CONFIG-001 | 配置插件凭证 | 1. 安装插件<br>2. 配置 API Key<br>3. 验证配置保存 | ✅ 配置已保存<br>✅ 凭证已加密 |
| CONFIG-002 | 更新插件配置 | 1. 配置插件<br>2. 更新配置<br>3. 验证更新生效 | ✅ 新配置生效 |
| CONFIG-003 | 删除插件配置 | 1. 配置插件<br>2. 删除配置<br>3. 验证配置删除 | ✅ 配置已删除 |

#### 5.1.4 插件模型调用（test_plugin_invoke.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| INVOKE-001 | 调用 tongyi 模型 | 1. 安装并启动 tongyi<br>2. 配置 API Key<br>3. 调用模型生成 | ✅ 返回有效响应<br>✅ 内容不为空 |
| INVOKE-002 | 流式调用 tongyi 模型 | 1. 配置插件<br>2. 流式调用模型<br>3. 验证增量响应 | ✅ 多次增量响应<br>✅ 最终完整响应 |
| INVOKE-003 | 无效 API Key 调用 | 1. 配置无效 API Key<br>2. 调用模型 | ❌ 返回认证错误 |
| INVOKE-004 | 调用 gpustack 模型 | 1. 安装并启动 gpustack<br>2. 配置 Endpoint 和 API Key<br>3. 调用模型 | ✅ 返回有效响应 |

#### 5.1.5 插件完整生命周期（test_plugin_full_lifecycle.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| LIFECYCLE-001 | tongyi 插件完整生命周期 | 1. 安装插件<br>2. 配置凭证<br>3. 启动插件<br>4. 调用模型<br>5. 停止插件<br>6. 卸载插件 | ✅ 每步骤成功<br>✅ 资源完全清理 |
| LIFECYCLE-002 | gpustack 插件完整生命周期 | 同 LIFECYCLE-001 | ✅ 每步骤成功<br>✅ 资源完全清理 |
| LIFECYCLE-003 | 生命周期资源清理验证 | 1. 完整生命周期<br>2. 验证内存清理<br>3. 验证数据库清理<br>4. 验证文件清理 | ✅ 内存无残留<br>✅ 数据库记录删除<br>✅ 文件已删除 |

### 5.2 P1 边界测试用例

#### 5.2.1 事件监听（test_event_listeners.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| EVENT-001 | 插件安装失败事件 | 1. 触发安装失败<br>2. 验证事件发布 | ✅ 事件已发布<br>✅ 状态更新为 FAILED |
| EVENT-002 | 插件崩溃事件 | 1. 启动插件<br>2. 模拟崩溃<br>3. 验证事件发布 | ✅ 事件已发布 |

#### 5.2.2 插件解析（test_plugin_parse.py）

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| PARSE-001 | 解析插件配置 | 1. 解析插件 manifest | ✅ 配置解析成功 |
| PARSE-002 | 解析无效配置 | 1. 解析无效 manifest | ❌ 返回解析错误 |

---

## 六、测试执行

### 6.1 运行方式

```bash
# 方式 1：运行所有 E2E 测试
uv run pytest -m e2e tests/ai/e2e/ -v

# 方式 2：运行指定测试文件
uv run pytest -m e2e tests/ai/e2e/test_plugin_full_lifecycle.py -v

# 方式 3：运行指定测试用例
uv run pytest -m e2e tests/ai/e2e/test_plugin_install.py::TestPluginInstall::test_install_tongyi_plugin_and_verify_environment -v

# 方式 4：生成覆盖率报告
uv run pytest -m e2e tests/ai/e2e/ --cov=src/ai --cov-report=html
```

### 6.2 测试前置条件

**必须满足**：

1. ✅ PostgreSQL 服务运行正常
2. ✅ Redis 服务运行正常
3. ✅ MinIO 服务运行正常（可选）
4. ✅ 插件包文件存在于 `plugins/` 目录
5. ✅ 环境变量配置完整

**验证命令**：

```bash
# 检查 PostgreSQL
psql -h localhost -U postgres -c "SELECT version();"

# 检查 Redis
redis-cli ping

# 检查 MinIO（可选）
curl http://localhost:9000/minio/health/live

# 检查插件包
ls plugins/*.zip
```

### 6.3 测试执行流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 环境检查                                              │
│    - 数据库连接                                          │
│    - Redis 连接                                          │
│    - MinIO 连接（可选）                                  │
│    - 插件包存在性                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 测试执行                                              │
│    - 运行 P0 核心测试                                    │
│    - 运行 P1 边界测试                                    │
│    - 收集测试结果                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 资源清理                                              │
│    - 清理测试租户数据                                    │
│    - 清理 Redis Key                                      │
│    - 清理 OSS 文件                                       │
│    - 清理临时目录                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. 报告生成                                              │
│    - 测试结果汇总                                        │
│    - 覆盖率报告                                          │
│    - 失败用例分析                                        │
└─────────────────────────────────────────────────────────┘
```

### 6.4 并行执行策略

**建议**：

- ✅ 不同租户的测试可以并行执行
- ✅ 不同插件的测试可以并行执行
- ❌ 同一插件的安装/卸载测试需要串行执行

**执行命令**：

```bash
# 并行执行（最大 4 个进程）
uv run pytest -m e2e tests/ai/e2e/ -n 4 -v
```

---

## 七、测试数据管理

### 7.1 测试租户

| 租户 ID 格式 | 说明 | 生命周期 |
|--------------|------|----------|
| `e2e-test-{uuid8}` | E2E 测试专用租户 | 测试结束后自动清理 |

### 7.2 测试数据清理

**自动清理**（通过 `cleanup_test_resources` fixture）：

- ✅ Redis Key：`tenant:{tenant_id}:*`
- ✅ OSS 文件：`{tenant_id}/*`
- ✅ 数据库记录：按租户 ID 删除

**手动清理**（测试失败时）：

```bash
# 清理 Redis
redis-cli KEYS "tenant:e2e-test-*" | xargs redis-cli DEL

# 清理数据库
psql -h localhost -U postgres -d kcloudy_test -c "DELETE FROM ai.plugin_configs WHERE tenant_id LIKE 'e2e-test-%';"
psql -h localhost -U postgres -d kcloudy_test -c "DELETE FROM tenant.plugin_installations WHERE tenant_id LIKE 'e2e-test-%';"

# 清理 OSS
mc rm -r --force minio/kcloudy-test/e2e-test-*
```

---

## 八、测试辅助工具

### 8.1 PluginTestHelper

测试辅助工具类提供以下方法：

| 方法 | 用途 | 示例 |
|------|------|------|
| `get_manager()` | 获取插件管理器 | `manager = await helper.get_manager(session)` |
| `wait_for_plugin_status()` | 等待插件状态 | `await helper.wait_for_plugin_status(session, plugin_id, "ACTIVE")` |
| `assert_plugin_installed()` | 验证插件已安装 | `await helper.assert_plugin_installed(session, plugin_id)` |
| `assert_plugin_running()` | 验证插件运行中 | `await helper.assert_plugin_running(session, plugin_id)` |
| `install_plugin_from_path()` | 从路径安装插件 | `plugin_id = await helper.install_plugin_from_path(session, path)` |
| `cleanup_plugin()` | 清理插件资源 | `await helper.cleanup_plugin(session, plugin_id)` |

### 8.2 测试 Fixtures

#### 8.2.1 核心测试 Fixtures

| Fixture | 提供内容 | 作用域 | 配置位置 |
|---------|----------|--------|----------|
| `e2e_session` | E2E 测试数据库会话 | function | `tests/ai/e2e/conftest.py` |
| `test_tenant_id` | E2E 测试租户 ID（`e2e-test-{uuid8}`） | function | `tests/ai/e2e/conftest.py` |
| `plugin_package_path` | 插件包路径获取函数 | function | `tests/ai/e2e/conftest.py` |
| `plugin_provider` | PluginInstallationProvider 实例 | function | `tests/ai/e2e/conftest.py` |
| `cleanup_test_resources` | 资源清理 | function | `tests/ai/e2e/conftest.py` |

#### 8.2.2 服务检测 Fixtures（来自 `tests/conftest.py`）

| Fixture | 提供内容 | 作用域 | 说明 |
|---------|----------|--------|------|
| `postgres_available` | PostgreSQL 服务可用性检测 | session | 返回 `bool` |
| `redis_available` | Redis 服务可用性检测 | session | 返回 `bool` |
| `minio_available` | MinIO 服务可用性检测 | session | 返回 `bool`（可选） |
| `postgres_session` | PostgreSQL 数据库会话 | function | 自动回滚 |
| `redis_client` | Redis 客户端 | function | 自动清理 |
| `minio_client` | MinIO 客户端 | function | 自动清理 |

#### 8.2.3 API Key Fixtures（来自 `tests/ai/conftest.py`）

| Fixture | 提供内容 | 作用域 | 默认值 |
|---------|----------|--------|--------|
| `tongyi_api_key` | 通义千问 API Key | function | `sk-623fdfb2b75f43b8bb6a61b8b183359a` |
| `gpustack_api_key` | GPUStack API Key | function | `gpustack_14d9f2aee5629a0f_...` |
| `gpustack_endpoint` | GPUStack 服务端点 | function | `https://llm-stack.flydiysz.cn` |

**使用示例**：

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_invoke_tongyi_model(
    e2e_session: AsyncSession,
    test_tenant_id: str,
    tongyi_api_key: str,  # 自动注入 API Key
) -> None:
    """测试调用 tongyi 模型"""
    # 使用 tongyi_api_key 进行测试
    pass
```

---

## 九、缺陷管理

### 9.1 缺陷等级定义

| 等级 | 定义 | 示例 |
|------|------|------|
| 🔴 P0 | 核心功能缺失或崩溃 | 插件无法安装、调用失败 |
| 🟠 P1 | 重要功能缺陷 | 状态更新延迟、资源泄漏 |
| 🟡 P2 | 一般功能缺陷 | 日志错误、提示不友好 |
| 🟢 P3 | 优化建议 | 性能优化、代码重构 |

### 9.2 缺陷报告模板

```markdown
**缺陷标题**：[模块] 简要描述

**环境信息**：
- Python 版本：
- 操作系统：
- 插件版本：

**重现步骤**：
1. 步骤一
2. 步骤二
3. 步骤三

**预期结果**：
应如何表现

**实际结果**：
实际表现

**日志/截图**：
```

[粘贴日志]

```

**补充信息**：
其他相关信息
```

---

## 十、测试报告

### 10.1 报告位置

| 报告类型 | 输出路径 | 说明 |
|----------|----------|------|
| **测试执行报告** | `docs/tests/plugin-e2e-{日期}.md` | Markdown 格式，人工填写 |
| **HTML 报告** | `reports/e2e-report.html` | pytest-html 自动生成 |
| **JUnit XML** | `reports/e2e-junit.xml` | CI/CD 集成使用 |
| **覆盖率报告** | `reports/coverage/html/` | HTML 格式覆盖率报告 |

**报告命名规范**：
- 测试执行报告：`plugin-e2e-{YYYY-MM-DD}.md`
- 示例：`plugin-e2e-2026-07-02.md`

### 10.2 报告内容

测试报告应包含：

1. **执行摘要**
   - 测试总数、通过数、失败数、跳过数
   - 执行时间
   - 覆盖率统计

2. **详细结果**
   - 每个测试用例的执行状态
   - 失败用例的错误信息
   - 跳过用例的原因

3. **趋势分析**
   - 历史测试通过率趋势
   - 缺陷分布统计

### 10.3 报告生成命令

#### 10.3.1 生成自动化报告

```bash
# 生成 HTML 报告
uv run pytest -m e2e tests/ai/e2e/ --html=reports/e2e-report.html --self-contained-html

# 生成 JUnit XML 报告（CI/CD 使用）
uv run pytest -m e2e tests/ai/e2e/ --junitxml=reports/e2e-junit.xml

# 生成覆盖率报告
uv run pytest -m e2e tests/ai/e2e/ --cov=src/ai --cov-report=html:reports/coverage/html

# 生成 Allure 报告（需安装 allure-pytest）
uv run pytest -m e2e tests/ai/e2e/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

#### 10.3.2 填写测试执行报告

测试执行报告模板位于 `docs/tests/plugin-e2e-{日期}.md`，包含以下内容：

1. **执行摘要**
   - 测试统计（总数、通过数、失败数、跳过数）
   - 覆盖率统计
   - 测试环境信息

2. **详细结果**
   - 按模块统计
   - 每个测试用例的执行状态
   - 失败用例的错误信息
   - 跳过用例的原因

3. **分析总结**
   - 失败用例分析
   - 性能分析
   - 稳定性分析
   - 缺陷统计

4. **改进建议**
   - 测试改进建议
   - 环境改进建议

**报告填写流程**：

```bash
# 1. 执行测试并生成报告
uv run pytest -m e2e tests/ai/e2e/ -v --html=reports/e2e-report.html

# 2. 查看自动化报告
open reports/e2e-report.html

# 3. 复制测试报告模板
cp docs/tests/plugin-e2e-2026-07-02.md docs/tests/plugin-e2e-$(date +%Y-%m-%d).md

# 4. 填写测试执行报告
# 根据 reports/e2e-report.html 中的数据填写 Markdown 报告
```

---

## 十一、风险与应对

### 11.1 测试风险

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 外部 API 不可用 | 模型调用测试失败 | 提供 mock 数据，标记为跳过 |
| 资源不足 | 测试超时 | 控制并发数，增加超时时间 |
| 环境差异 | 测试结果不一致 | 使用 Docker 统一环境 |
| 数据污染 | 测试失败 | 每次测试前清理数据 |

### 11.2 应急预案

**测试环境故障**：

1. 检查服务状态（PostgreSQL、Redis、MinIO）
2. 重启相关服务
3. 清理测试数据
4. 重新执行测试

**测试用例失败**：

1. 查看错误日志
2. 分析失败原因
3. 修复问题或更新测试
4. 重新执行失败的测试

---

## 十二、附录

### 12.1 参考资料

- [插件系统设计文档](../../src/ai/components/plugin/README.md)
- [AI 模块开发指南](../../src/ai/CLAUDE.md)
- [测试编写规范](../CLAUDE.md)

### 12.2 术语表

| 术语 | 说明 |
|------|------|
| Plugin | 插件，提供模型、工具等扩展能力 |
| Runtime | 插件运行时，管理插件进程生命周期 |
| Provider | 供应商，提供 AI 模型服务 |
| Tenant | 租户，多租户架构中的隔离单元 |

### 12.3 变更历史

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-07-02 | v1.0 | 初始版本 | Claude |

---

## 快速开始

```bash
# 1. 配置环境变量
export E2E_TONGYI_API_KEY="your-api-key"

# 2. 运行所有 E2E 测试
uv run pytest -m e2e tests/ai/e2e/ -v

# 3. 查看测试报告
open reports/e2e-report.html
```
