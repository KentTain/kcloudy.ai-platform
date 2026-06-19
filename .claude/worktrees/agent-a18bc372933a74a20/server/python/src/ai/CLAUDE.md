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

AI 模块 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 类型 | 路由前缀 | 用途 | 权限 |
|------|---------|------|------|
| admin | `/ai/admin/v1/models` | 管理后台模型管理 | JWT Token + 管理员权限 |
| console | `/ai/console/v1/chat-messages` | 用户端 AI 接口 | JWT Token |
| inner | `/ai/inner/v1/models` | 内部接口，供模块间调用 | 无认证 |

### 完整路由表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ai/admin/v1/models` | 获取模型列表 |
| POST | `/ai/admin/v1/models` | 创建模型配置 |
| GET | `/ai/admin/v1/models/{id}` | 获取模型详情 |
| PUT | `/ai/admin/v1/models/{id}` | 更新模型配置 |
| DELETE | `/ai/admin/v1/models/{id}` | 删除模型配置 |
| POST | `/ai/console/v1/chat-messages` | 发送聊天消息 |
| GET | `/ai/console/v1/chat-messages` | 获取聊天历史 |
| GET | `/ai/inner/v1/models/{id}` | 内部接口：获取模型配置 |

## 核心组件

| 组件 | 路径 | 职责 |
|------|------|------|
| LLMService | components/model/services/ | LLM 调用统一入口 |
| EmbeddingService | components/model/services/ | 文本嵌入服务 |
| RerankService | components/model/services/ | 重排序服务 |
| PluginManager | components/plugin/engine/ | 插件生命周期管理 |
| ModelInstanceFactory | components/model/internal/ | 模型实例创建工厂 |
| EncryptionManager | components/encryption/ | 加密管理器 |
| GraphRAGClient | components/graphrag/ | 图谱检索增强生成客户端 |
| CodeExecutor | components/code_executor/ | 代码执行器 |
| MySQLConnect | components/datasource/ | MySQL 数据源连接 |

## AI 组件模块

AI 组件位于 `components/` 目录下，提供可复用的 AI 能力封装：

| 组件 | 说明 | 主要类 |
|------|------|--------|
| encryption | 加密组件 | AESEncryption, RSAEncryption, EncryptionManager |
| datasource | 数据源组件 | BaseConnect, RDBMSDatabase, MySQLConnect |
| code_executor | 代码执行器 | CodeExecutor, Python3TemplateTransformer, NodeJsTemplateTransformer |
| graphrag | 图谱检索增强生成 | GraphRAGClient, GraphData |
| model | 模型管理 | LLMService, EmbeddingService, RerankService |
| plugin | 插件系统 | PluginManager, PluginInstance |

### 加密组件 (encryption)

提供 AES-256-CBC 和 RSA 加密算法实现：

```python
from ai.components import EncryptionManager, get_encryption_manager

# 初始化加密管理器
await init_encryption_manager(config)

# 获取加密实例
encryption = get_encryption_manager().get_instance("default")
encrypted = encryption.encrypt("sensitive data")
decrypted = encryption.decrypt(encrypted)
```

### 数据源组件 (datasource)

提供统一的数据库连接和查询接口：

```python
from ai.components import MySQLConnect

# 创建 MySQL 连接
conn = MySQLConnect(host="localhost", port=3306, database="test")
await conn.connect()

# 执行查询
results = await conn.run("SELECT * FROM users")
df = await conn.run_to_df("SELECT * FROM orders")
```

### 代码执行器 (code_executor)

支持 Python3、JavaScript、Jinja2 代码执行（依赖 dify-sandbox）：

```python
from ai.components import CodeExecutor, CodeLanguage

result = await CodeExecutor.execute_workflow_code_template(
    language=CodeLanguage.PYTHON3,
    code="def main(x, y): return {'result': x + y}",
    inputs={"x": 1, "y": 2}
)
```

### GraphRAG 组件 (graphrag)

提供图谱检索增强生成能力：

```python
from ai.components import GraphRAGClient

client = GraphRAGClient()

# 创建索引任务
task = await client.create_index_build_task(
    namespace="dataset_123",
    kb_code="kb_001",
    filename="document.pdf",
    docs=["文档内容..."]
)

# 搜索
result = await client.search(
    namespace="dataset_123",
    kb_code="kb_001",
    filename="document.pdf",
    query="查询内容",
    query_method="local",
    score_threshold=0.5
)
```

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

AI 模块测试位于 `tests/ai/` 目录下，采用分层测试策略。

### 测试覆盖情况

| 组件 | 测试文件 | 测试用例数 | 覆盖内容 |
|------|---------|-----------|---------|
| encryption | test_encryption.py | 35+ | AES/RSA 加密、密钥管理、异常处理 |
| datasource | test_*.py | 44+ | 接口定义、URI 构造、SQL 解析、数据库连接 |
| code_executor | test_*.py | 85+ | 代码执行、模板转换、Provider 实现 |
| graphrag | test_*.py | 38+ | GraphData 模型、GraphRAGClient 客户端 |
| model | test_*.py | - | LLM 服务、模型工厂、Provider 管理 |

**总计**：216+ 测试用例，覆盖所有核心组件

### 运行测试

```bash
# 运行所有 AI 组件测试
uv run pytest tests/ai/components -v

# 运行特定组件测试
uv run pytest tests/ai/components/encryption -v
uv run pytest tests/ai/components/datasource -v
uv run pytest tests/ai/components/code_executor -v
uv run pytest tests/ai/components/graphrag -v
```

### 测试特点

1. **隔离性**：所有测试使用 mock 隔离外部依赖（数据库、Redis、MinIO）
2. **快速执行**：单元测试不依赖真实服务，执行速度快
3. **中文文档**：所有测试用例使用中文文档字符串
4. **TDD 实践**：新增功能先编写测试，再实现功能

详细插件系统说明、API 端点见 [README.md](README.md)。
