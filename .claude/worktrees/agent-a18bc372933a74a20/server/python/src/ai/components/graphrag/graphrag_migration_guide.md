# GraphRAG 集成改造指南

## 1. 概述

本文档指导如何将 Microsoft GraphRAG 组件从独立工程迁移到 Alon 主工程中，确保技术栈对齐和架构一致性。

### 1.1 当前状态

- **源目录**: `alon/components/graphrag/`
- **来源**: Microsoft 开源 GraphRAG 项目 (v0.3.0)
- **改造内容**: 已添加 webserver 模块提供 REST API 服务
- **运行方式**: 独立服务运行在端口 20214

### 1.2 目标

- 将 GraphRAG 完全集成到 Alon 主工程
- 统一依赖管理（从 Poetry 迁移到 uv）
- 统一配置管理（对齐 Alon 的配置系统）
- 统一代码规范和工具链
- 统一部署和运维

---

## 2. 技术栈差异对比

### 2.1 依赖管理工具

| 项目 | 工具 | Python 版本要求 |
|------|------|-----------------|
| GraphRAG | Poetry | >=3.10,<3.13 |
| Alon | uv | >=3.10,<3.13 |

**改造方案**:
- 移除 `pyproject.toml` 中的 Poetry 配置
- 将依赖迁移到 Alon 主工程的 `pyproject.toml`

### 2.2 Web 框架

| 项目 | 框架 | 版本 |
|------|------|------|
| GraphRAG | FastAPI + uvicorn | ~0.103.0 + ~0.20.0 |
| Alon | FastAPI[standard] + uvicorn[standard] | 0.115.12 + 0.34.3 |

**改造方案**:
- 升级 GraphRAG 的 FastAPI 到 Alon 版本
- 将 GraphRAG 路由集成到 Alon 主应用

### 2.3 配置管理

| 项目 | 方式 | 文件 |
|------|------|------|
| GraphRAG | YAML + python-dotenv | `ragconfig/settings.yaml` |
| Alon | YAML + Pydantic Settings | `config/application.yml` |

**改造方案**:
- 将 GraphRAG 配置迁移到 Alon 配置系统
- 使用 Pydantic Settings 替代 pyaml-env

### 2.4 代码质量工具

| 工具 | GraphRAG | Alon |
|------|----------|------|
| Linter | ruff 0.5.2 | ruff 0.14.8 |
| Type Checker | pyright 1.1.371 | pyright 1.1.391 |
| Pre-commit | ❌ | ✅ |

**改造方案**:
- 升级 ruff 和 pyright 到 Alon 版本
- 添加 pre-commit 配置

### 2.5 存储依赖

| 功能 | GraphRAG | Alon |
|------|----------|------|
| MinIO | 7.2.7 | 7.2.15 |
| Azure Blob | ✅ | ❌ |
| 阿里云 OSS | ❌ | ✅ |
| 腾讯云 COS | ❌ | ✅ |

**改造方案**:
- 升级 MinIO 版本到 7.2.15
- 保留 Azure Blob 支持（可选依赖）

---

## 3. 依赖整合方案

### 3.1 核心依赖迁移

需要添加到 Alon `pyproject.toml` 的依赖：

```toml
[project.optional-dependencies]

# GraphRAG 模块依赖
graphrag = [
    # 数据处理
    "datashaper==0.0.49",
    "pandas==2.3.0",  # 已存在，版本对齐
    "numpy>=1.25.2,<2.0",
    "scipy==1.12.0",
    "numba==0.60.0",

    # 图处理
    "networkx>=3.0,<4.0",
    "graspologic==3.4.1",
    "fastparquet==2024.2.0",

    # 向量存储
    "lancedb==0.11.0",
    "azure-search-documents==11.4.0",

    # LLM
    "openai==1.37.1",  # 可能与 agno 冲突，需测试
    "tiktoken==0.9.0",  # 已在 plugin 组
    "nltk==3.8.1",

    # 配置
    "pyaml-env==1.2.1",

    # 工具
    "tenacity==9.0.0",
    "rich==13.6.0",
    "textual==0.76.0",
    "devtools==0.12.2",
    "json-repair==0.26.0",
    "swifter==1.4.0",

    # 异步
    "aiolimiter==1.1.0",
    "aiofiles==24.1.0",  # 已在 knowledge_base 组
    "uvloop==0.19.0; platform_system != 'Windows'",
    "nest-asyncio==1.6.0; platform_system == 'Windows'",
]
```

### 3.2 版本冲突处理

#### 冲突 1: pandas
- GraphRAG: 2.2.2
- Alon: 2.3.0
- **解决**: 使用 Alon 版本 2.3.0（向后兼容）

#### 冲突 2: minio
- GraphRAG: 7.2.7
- Alon: 7.2.15
- **解决**: 使用 Alon 版本 7.2.15（向后兼容）

#### 冲突 3: aiofiles
- GraphRAG: 24.1.0
- Alon: 24.1.0
- **解决**: 无冲突

#### 冲突 4: tiktoken
- GraphRAG: 0.7.0
- Alon plugin: 0.9.0
- **解决**: 使用 Alon 版本 0.9.0，测试 GraphRAG 兼容性

#### 冲突 5: openai
- GraphRAG: 1.37.1
- Alon (通过 agno): 需确认版本
- **解决**: 优先使用 agno 框架集成，可能需要适配 GraphRAG 的 LLM 调用

### 3.3 开发依赖整合

GraphRAG 的开发依赖已被 Alon 覆盖：
- pytest: 8.3.5 (Alon) vs 8.3.2 (GraphRAG) ✅
- pytest-asyncio: 0.25.3 (Alon) vs 0.23.4 (GraphRAG) ✅
- ruff: 0.14.8 (Alon) vs 0.5.2 (GraphRAG) ✅
- pyright: 1.1.391 (Alon) vs 1.1.371 (GraphRAG) ✅

---

## 4. 代码结构改造

### 4.1 目录结构调整

**当前结构**:
```
alon/components/graphrag/
├── pyproject.toml          # 删除
├── run_*.py                # 保留或重构
├── webserver/              # 集成到 Alon
├── config/                 # 迁移到 Alon 配置
├── index/                  # 保留
├── query/                  # 保留
├── llm/                    # 可能整合到 Alon LLM
├── model/                  # 保留
├── vector_stores/          # 保留
├── ragconfig/              # 删除，迁移到主配置
└── prompt/                 # 保留
```

**建议新结构**:
```
alon/components/graphrag/
├── __init__.py             # 包初始化
├── core/                   # 核心功能
│   ├── index/              # 索引管道
│   ├── query/              # 查询引擎
│   ├── prompt_tune/        # 提示优化
│   ├── model/              # 数据模型
│   └── vector_stores/      # 向量存储
├── api/                    # API 路由（原 webserver）
│   ├── routes/
│   │   ├── index.py        # 索引管理 API
│   │   ├── search.py       # 搜索 API
│   │   ├── prompt.py       # 提示管理 API
│   │   └── task.py         # 任务管理 API
│   ├── models/             # 请求/响应模型
│   └── services/           # 业务逻辑
├── config/                 # GraphRAG 专用配置模型
├── storage/                # 存储抽象层
└── tasks/                  # 后台任务管理
```

### 4.2 WebServer 集成方案

#### 方案 A: 独立蓝图（推荐）

将 GraphRAG API 作为独立的 APIRouter 集成：

```python
# alon/components/graphrag/api/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/graphrag", tags=["GraphRAG"])

# 注册所有子路由
from .routes import index, search, prompt, task
router.include_router(index.router)
router.include_router(search.router)
router.include_router(prompt.router)
router.include_router(task.router)
```

在 Alon 主应用中注册：

```python
# alon/application.py
from alon.components.graphrag.api.router import router as graphrag_router

def create_app():
    app = FastAPI()
    # ... 其他中间件和路由
    app.include_router(graphrag_router)
    return app
```

#### 方案 B: 服务化集成

保留独立服务，但使用 Alon 配置和中间件：

```python
# alon/components/graphrag/server.py
from alon.application import create_base_app
from alon.components.graphrag.api.router import router

def create_graphrag_app():
    app = create_base_app(service_name="graphrag")
    app.include_router(router, prefix="/v1")
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_graphrag_app()
    uvicorn.run(app, host="0.0.0.0", port=20214)
```

**推荐**: 方案 A，完全集成到主应用，统一管理。

### 4.3 配置整合

#### 步骤 1: 定义 GraphRAG 配置模型

```python
# alon/components/graphrag/config/settings.py
from pydantic import BaseModel, Field
from typing import Literal

class GraphRAGLLMConfig(BaseModel):
    type: str = "openai_chat"
    model: str = "gpt-4-turbo-preview"
    api_base: str | None = None
    api_key: str | None = None
    max_tokens: int = 6000
    temperature: float = 0.0
    tokens_per_minute: int = 150000
    requests_per_minute: int = 10000

class GraphRAGEmbeddingConfig(BaseModel):
    model: str = "text-embedding-3-small"
    batch_size: int = 16

class GraphRAGStorageConfig(BaseModel):
    type: Literal["file", "blob", "minio"] = "minio"
    connection_string: str | None = None
    container_name: str | None = None
    base_path: str = "/ragdata"

class GraphRAGConfig(BaseModel):
    enabled: bool = True
    encoding_model: str = "cl100k_base"
    llm: GraphRAGLLMConfig = Field(default_factory=GraphRAGLLMConfig)
    embeddings: GraphRAGEmbeddingConfig = Field(default_factory=GraphRAGEmbeddingConfig)
    storage: GraphRAGStorageConfig = Field(default_factory=GraphRAGStorageConfig)
    chunk_size: int = 1200
    chunk_overlap: int = 30
```

#### 步骤 2: 集成到 Alon 主配置

```yaml
# config/application.yml
graphrag:
  enabled: true
  encoding_model: cl100k_base
  llm:
    type: openai_chat
    model: ${GRAPHRAG_LLM_MODEL:gpt-4-turbo-preview}
    api_base: ${GRAPHRAG_API_BASE:}
    api_key: ${GRAPHRAG_API_KEY:}
    max_tokens: 6000
    temperature: 0.0
  embeddings:
    model: ${GRAPHRAG_EMBEDDING_MODEL:text-embedding-3-small}
    batch_size: 16
  storage:
    type: ${GRAPHRAG_STORAGE_TYPE:minio}
    connection_string: ${GRAPHRAG_STORAGE_CONNECTION:}
    base_path: /ragdata
  chunk_size: 1200
  chunk_overlap: 30
```

#### 步骤 3: 在 Alon Settings 中注册

```python
# alon/config/settings.py
from alon.components.graphrag.config.settings import GraphRAGConfig

class Settings(BaseSettings):
    # ... 其他配置
    graphrag: GraphRAGConfig = Field(default_factory=GraphRAGConfig)
```

### 4.4 LLM 集成策略

GraphRAG 使用 OpenAI SDK，Alon 使用 Agno 框架。两种方案：

#### 方案 A: 保留 GraphRAG 原有 LLM 实现（推荐短期）

优点：改动最小，快速集成
缺点：维护两套 LLM 调用逻辑

```python
# alon/components/graphrag/core/llm/
# 保留原有 openai.py 实现
```

#### 方案 B: 适配 Agno 框架（推荐长期）

优点：统一 LLM 管理，便于监控和成本控制
缺点：需要适配代码

```python
# alon/components/graphrag/core/llm/agno_adapter.py
from agno import OpenAIClient
from graphrag.llm.base import BaseLLM

class AgnoLLMAdapter(BaseLLM):
    def __init__(self, agno_client: OpenAIClient):
        self.client = agno_client

    async def complete(self, prompt: str, **kwargs):
        # 适配 Agno 接口到 GraphRAG 接口
        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
```

**建议**: 先使用方案 A 快速集成，后续迭代到方案 B。

---

## 5. 数据库和缓存集成

### 5.1 GraphRAG 当前存储

- **输入文件**: MinIO/File/Blob
- **输出工件**: Parquet 文件（MinIO/File/Blob）
- **元数据**: 无独立数据库（文件系统）

### 5.2 集成到 Alon 数据库

建议添加 GraphRAG 索引元数据表：

```python
# alon/components/graphrag/models/db.py
from sqlalchemy import Column, String, DateTime, Integer, JSON
from alon.extensions.database import Base

class GraphRAGIndex(Base):
    __tablename__ = "graphrag_indexes"

    id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    namespace = Column(String(100), nullable=False)
    code = Column(String(100), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)  # pending/indexing/completed/failed
    storage_path = Column(String(500))
    config = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    __table_args__ = (
        Index('idx_tenant_namespace_code', 'tenant_id', 'namespace', 'code'),
    )
```

迁移文件：

```python
# migrations/versions/20251208_1400_add_graphrag_tables.py
def upgrade():
    op.create_table(
        'graphrag_indexes',
        sa.Column('id', sa.String(50), primary_key=True),
        # ... 其他字段
    )
```

### 5.3 Redis 缓存集成

利用 Alon 现有 Redis 缓存：

```python
# alon/components/graphrag/cache.py
from alon.extensions.cache import cache_manager

async def cache_search_result(key: str, result: dict, ttl: int = 3600):
    await cache_manager.set(f"graphrag:search:{key}", result, expire=ttl)

async def get_cached_search_result(key: str):
    return await cache_manager.get(f"graphrag:search:{key}")
```

---

## 6. 任务调度集成

### 6.1 GraphRAG 当前任务管理

- 使用 threading 运行后台任务
- 自定义 Task 类管理任务状态
- 无持久化，重启丢失

### 6.2 集成到 APScheduler

利用 Alon 的 APScheduler：

```python
# alon/components/graphrag/tasks/scheduler.py
from alon.extensions.scheduler import scheduler
from alon.components.graphrag.core.index import run_index_pipeline

async def schedule_index_task(index_id: str, config: dict):
    job = scheduler.add_job(
        run_index_pipeline,
        args=[index_id, config],
        id=f"graphrag_index_{index_id}",
        replace_existing=True
    )
    return job.id

async def cancel_index_task(index_id: str):
    job_id = f"graphrag_index_{index_id}"
    scheduler.remove_job(job_id)
```

### 6.3 任务状态持久化

```python
# alon/components/graphrag/models/db.py (补充)
class GraphRAGTask(Base):
    __tablename__ = "graphrag_tasks"

    id = Column(String(50), primary_key=True)
    index_id = Column(String(50), ForeignKey('graphrag_indexes.id'))
    task_type = Column(String(20))  # index/search/prompt_tune
    status = Column(String(20))  # pending/running/completed/failed/cancelled
    progress = Column(Integer, default=0)
    logs = Column(JSON)
    result = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

---

## 7. API 路由迁移

### 7.1 路径调整

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `/v1/graphrag/index` | `/api/graphrag/index` | 统一前缀 |
| `/v1/graphrag/search` | `/api/graphrag/search` | 统一前缀 |
| `/v1/graphrag/prompt_tune` | `/api/graphrag/prompt/tune` | 更清晰的结构 |

### 7.2 认证和鉴权集成

添加 Alon 的认证中间件：

```python
# alon/components/graphrag/api/routes/search.py
from fastapi import APIRouter, Depends
from alon.middleware.auth import get_current_user
from alon.models.user import User

router = APIRouter()

@router.post("/search")
async def search(
    request: SearchParam,
    current_user: User = Depends(get_current_user)
):
    # 自动注入 tenant_id
    request.namespace = current_user.tenant_id
    # ... 原有逻辑
```

### 7.3 多租户改造

```python
# alon/components/graphrag/services/search.py
async def execute_search(
    tenant_id: str,  # 从认证用户获取
    kb_code: str,
    filename: str,
    query: str,
    **kwargs
):
    # 构建租户隔离的存储路径
    root_path = build_tenant_root_path(tenant_id, kb_code, filename)
    # ... 原有逻辑
```

---

## 8. 部署和运维调整

### 8.1 服务部署方案

#### 方案 A: 合并部署（推荐）

GraphRAG 作为 Alon 主服务的一部分：

```yaml
# docker-compose.yml
services:
  alon-web:
    image: alon:latest
    ports:
      - "8080:8080"
    environment:
      - GRAPHRAG_ENABLED=true
      - GRAPHRAG_STORAGE_TYPE=minio
```

#### 方案 B: 独立部署

GraphRAG 仍作为独立微服务：

```yaml
# docker-compose.yml
services:
  alon-web:
    image: alon:latest
    ports:
      - "8080:8080"

  alon-graphrag:
    image: alon-graphrag:latest
    ports:
      - "20214:20214"
    environment:
      - GRAPHRAG_STORAGE_TYPE=minio
```

**推荐**: 方案 A，减少运维复杂度。

### 8.2 启动脚本调整

```python
# manage.py (添加 GraphRAG 命令)
@cli.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=20214)
def graphrag(host, port):
    """启动 GraphRAG 服务"""
    from alon.components.graphrag.server import create_graphrag_app
    import uvicorn

    app = create_graphrag_app()
    uvicorn.run(app, host=host, port=port)
```

### 8.3 监控和日志

集成到 Alon 日志系统：

```python
# alon/components/graphrag/__init__.py
from loguru import logger

# 移除 GraphRAG 原有的 logging 配置
# 使用 Alon 的 loguru
```

---

## 9. 测试迁移

### 9.1 单元测试

```python
# tests/unit/components/graphrag/test_search.py
import pytest
from alon.components.graphrag.services.search import execute_search

@pytest.mark.asyncio
async def test_local_search():
    result = await execute_search(
        tenant_id="test_tenant",
        kb_code="test_kb",
        filename="test.txt",
        query="test query",
        method="local"
    )
    assert result is not None
```

### 9.2 集成测试

```python
# tests/integration/components/graphrag/test_api.py
import pytest
from httpx import AsyncClient
from alon.application import create_app

@pytest.mark.asyncio
async def test_graphrag_search_api():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/graphrag/search",
            json={
                "namespace": "test",
                "code": "kb1",
                "filename": "doc.txt",
                "query": "test",
                "query_method": "local"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
```

---

## 10. 迁移实施步骤

### Phase 1: 依赖整合（1-2天）

1. ✅ 分析依赖差异
2. ⬜ 更新 `pyproject.toml` 添加 `graphrag` 可选依赖组
3. ⬜ 解决版本冲突
4. ⬜ 运行 `uv sync --extra graphrag` 验证依赖安装
5. ⬜ 运行 GraphRAG 原有测试确保兼容性

### Phase 2: 代码结构调整（2-3天）

1. ⬜ 重组目录结构（core/api/config/storage）
2. ⬜ 移除 `pyproject.toml` 和 `run_*.py`
3. ⬜ 重构 import 路径
4. ⬜ 更新 `__init__.py` 导出

### Phase 3: 配置迁移（1-2天）

1. ⬜ 定义 GraphRAG Pydantic 配置模型
2. ⬜ 集成到 Alon Settings
3. ⬜ 迁移 `settings.yaml` 配置到 `application.yml`
4. ⬜ 环境变量映射
5. ⬜ 测试配置加载

### Phase 4: WebServer 集成（2-3天）

1. ⬜ 将 webserver 模块重构为 APIRouter
2. ⬜ 拆分路由到 `api/routes/`
3. ⬜ 集成认证中间件
4. ⬜ 添加多租户支持
5. ⬜ 注册到 Alon 主应用
6. ⬜ 测试 API 端点

### Phase 5: 数据库集成（1-2天）

1. ⬜ 定义 GraphRAGIndex 和 GraphRAGTask 模型
2. ⬜ 创建数据库迁移文件
3. ⬜ 运行迁移
4. ⬜ 更新服务层使用数据库
5. ⬜ 测试数据持久化

### Phase 6: 任务调度集成（1-2天）

1. ⬜ 集成 APScheduler
2. ⬜ 重构后台任务为 APScheduler jobs
3. ⬜ 任务状态持久化
4. ⬜ 测试任务执行和取消

### Phase 7: 存储集成（1天）

1. ⬜ 对接 Alon 的 MinIO/OSS 配置
2. ⬜ 统一存储路径管理
3. ⬜ 测试文件上传下载

### Phase 8: LLM 集成（可选，2-3天）

1. ⬜ 实现 AgnoLLMAdapter
2. ⬜ 替换 GraphRAG LLM 调用
3. ⬜ 测试 LLM 功能
4. ⬜ 监控和日志集成

### Phase 9: 测试和文档（2-3天）

1. ⬜ 编写单元测试
2. ⬜ 编写集成测试
3. ⬜ 更新 API 文档
4. ⬜ 编写使用指南
5. ⬜ 性能测试

### Phase 10: 部署验证（1-2天）

1. ⬜ 更新 Dockerfile
2. ⬜ 更新 docker-compose.yml
3. ⬜ 本地部署测试
4. ⬜ 集成测试环境部署
5. ⬜ 生产环境部署

**总计**: 约 15-25 个工作日

---

## 11. 风险和注意事项

### 11.1 版本兼容性风险

**风险**: OpenAI SDK、tiktoken 版本升级可能导致行为变化

**缓解措施**:
- 保留原版本进行 A/B 测试
- 编写回归测试覆盖核心功能
- 分阶段升级，逐步验证

### 11.2 性能影响

**风险**: 集成到主应用可能影响性能

**缓解措施**:
- 异步任务执行（已实现）
- 独立线程池/进程池
- 资源限制和监控
- 考虑独立部署（方案 B）

### 11.3 数据迁移

**风险**: 现有索引数据需要迁移

**缓解措施**:
- 提供数据迁移脚本
- 兼容旧路径格式
- 灰度迁移策略

### 11.4 LLM 成本

**风险**: GraphRAG 大量使用 LLM，成本较高

**缓解措施**:
- 集成 Agno 统一成本监控
- 添加 Token 使用限额
- 缓存搜索结果
- 配置更便宜的模型

---

## 12. 后续优化建议

### 12.1 性能优化

1. **索引优化**:
   - 并行处理文档
   - 增量索引更新
   - 使用更快的 embedding 模型

2. **搜索优化**:
   - 添加多级缓存
   - 预加载常用索引
   - 向量索引优化

### 12.2 功能增强

1. **实时更新**: WebSocket 推送索引进度
2. **批量操作**: 批量创建/删除索引
3. **索引版本管理**: 支持索引回滚
4. **可视化**: 知识图谱可视化增强

### 12.3 可观测性

1. **指标监控**:
   - 索引耗时
   - 搜索耗时
   - Token 使用量
   - 存储使用量

2. **日志增强**:
   - 结构化日志
   - 分布式追踪（OpenTelemetry）
   - 错误告警

### 12.4 多模型支持

1. 支持更多 LLM 提供商（通过 Agno）
2. 支持本地模型（Ollama）
3. 支持多模态（图片、音频）

---

## 13. 检查清单

### 开发阶段

- [ ] 依赖添加到 `pyproject.toml`
- [ ] 依赖安装测试通过
- [ ] 目录结构重组完成
- [ ] 配置迁移到 Alon Settings
- [ ] API 路由集成到主应用
- [ ] 认证中间件集成
- [ ] 多租户支持
- [ ] 数据库模型定义
- [ ] 数据库迁移文件
- [ ] 任务调度集成
- [ ] 存储路径统一
- [ ] 日志系统集成
- [ ] 单元测试编写
- [ ] 集成测试编写
- [ ] API 文档更新

### 部署阶段

- [ ] Dockerfile 更新
- [ ] docker-compose.yml 更新
- [ ] 环境变量配置
- [ ] 数据库迁移执行
- [ ] 测试环境部署
- [ ] 功能验证测试
- [ ] 性能测试
- [ ] 生产环境部署
- [ ] 监控配置
- [ ] 告警配置

### 文档阶段

- [ ] API 文档完整
- [ ] 配置说明文档
- [ ] 部署文档
- [ ] 使用指南
- [ ] 故障排查文档
- [ ] 变更日志

---

## 14. 参考资料

### 14.1 GraphRAG 官方资源

- [GraphRAG GitHub](https://github.com/microsoft/graphrag)
- [GraphRAG 文档](https://microsoft.github.io/graphrag/)
- [GraphRAG 论文](https://arxiv.org/abs/2404.16130)

### 14.2 Alon 内部资源

- `config/application.yml` - 配置示例
- `alon/application.py` - FastAPI 应用工厂
- `alon/extensions/` - 扩展组件（数据库、缓存、调度器）
- `docs/` - 开发文档

### 14.3 工具文档

- [uv 文档](https://github.com/astral-sh/uv)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)

---

## 15. 总结

GraphRAG 集成到 Alon 主工程是一个系统性工程，涉及依赖管理、配置系统、API 集成、数据库、任务调度等多个方面。

**核心原则**:
1. **最小化改动**: 优先保留 GraphRAG 核心逻辑
2. **渐进式迁移**: 分阶段实施，每阶段可验证
3. **可回滚**: 保留独立部署能力
4. **可测试**: 每个阶段都有测试覆盖

**关键成功因素**:
1. 详细的测试覆盖（单元测试+集成测试）
2. 分阶段部署验证
3. 充分的文档和知识传递
4. 性能监控和优化

按照本指南逐步实施，预计 3-4 周可完成完整迁移和验证。
