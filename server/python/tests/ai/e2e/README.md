# 插件 E2E 测试执行指南

> 快速参考：如何执行插件 E2E 测试并生成报告

---

## 一、环境准备（5 分钟）

### 1.1 检查服务状态

```bash
# PostgreSQL
psql -h localhost -U postgres -c "SELECT version();"

# Redis
redis-cli ping

# MinIO（可选）
curl http://localhost:9000/minio/health/live
```

### 1.2 配置 API Keys

**方式 1：环境变量（推荐）**

```bash
export E2E_TONGYI_API_KEY="your-api-key"
export E2E_GPUSTACK_API_KEY="your-api-key"  # 可选
export E2E_GPUSTACK_ENDPOINT="https://your-endpoint"  # 可选
```

**方式 2：使用默认配置**

默认配置已内置在 `tests/ai/conftest.py`，适用于开发环境测试。

### 1.3 检查插件包

```bash
# 插件包位于项目根目录 plugins/
ls plugins/*.zip

# 预期输出：
# langgenius-tongyi_0.2.0.zip
# langgenius-gpustack_0.0.15.zip
# langgenius-ollama_1.0.0.zip
# ...
```

---

## 二、执行测试（5-10 分钟）

### 2.1 运行所有测试

```bash
# 进入后端目录
cd server/python

# 运行所有 E2E 测试
uv run pytest -m e2e tests/ai/e2e/ -v
```

### 2.2 运行指定测试

```bash
# 测试插件安装
uv run pytest -m e2e tests/ai/e2e/test_plugin_install.py -v

# 测试插件运行时
uv run pytest -m e2e tests/ai/e2e/test_plugin_runtime.py -v

# 测试插件调用
uv run pytest -m e2e tests/ai/e2e/test_plugin_invoke.py -v

# 测试完整生命周期
uv run pytest -m e2e tests/ai/e2e/test_plugin_full_lifecycle.py -v
```

### 2.3 生成覆盖率报告

```bash
uv run pytest -m e2e tests/ai/e2e/ \
  --cov=src/ai/components/plugin \
  --cov-report=html:reports/coverage/html \
  -v

# 查看覆盖率报告
open reports/coverage/html/index.html
```

---

## 三、生成报告（5 分钟）

### 3.1 自动化报告

```bash
# 生成 HTML 报告
uv run pytest -m e2e tests/ai/e2e/ \
  --html=reports/e2e-report.html \
  --self-contained-html \
  -v

# 查看报告
open reports/e2e-report.html
```

### 3.2 测试执行报告

```bash
# 1. 复制报告模板
cp docs/tests/plugin-e2e-2026-07-02.md docs/tests/plugin-e2e-$(date +%Y-%m-%d).md

# 2. 根据 HTML 报告填写 Markdown 报告
# 主要填写内容：
# - 执行摘要（通过/失败/跳过数量）
# - 失败用例分析
# - 性能瓶颈
# - 改进建议
```

---

## 四、常见问题

### 4.1 PostgreSQL 连接失败

**错误**：`psycopg.OperationalError: connection failed`

**解决**：

```bash
# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 启动服务
sudo systemctl start postgresql

# 检查连接配置
cat server/config/application-local.yml | grep sqlalchemy
```

### 4.2 Redis 连接失败

**错误**：`redis.exceptions.ConnectionError`

**解决**：

```bash
# 检查 Redis 服务
redis-cli ping

# 启动服务
sudo systemctl start redis
```

### 4.3 插件包不存在

**错误**：`FileNotFoundError: 插件包不存在`

**解决**：

```bash
# 检查插件包
ls plugins/*.zip

# 如果不存在，从代码仓库下载或联系团队获取
```

### 4.4 模型调用失败

**错误**：`模型调用失败（可能是 API 配额限制）`

**解决**：

1. 检查 API Key 是否有效
2. 检查 API 配额是否充足
3. 使用环境变量覆盖默认配置

```bash
export E2E_TONGYI_API_KEY="your-valid-api-key"
```

### 4.5 Windows 上插件调用超时

**错误**：`Windows 上 gevent.os.tp_read 无法读取 asyncio 子进程 stdin 管道`

**说明**：这是已知的平台限制，Windows 上部分测试会被跳过。

**解决**：在 Linux 环境下执行完整测试。

---

## 五、测试配置参考

### 5.1 配置文件位置

| 配置类型 | 文件位置 |
|----------|----------|
| 基础设施配置 | `server/python/tests/conftest.py` |
| API Key 配置 | `server/python/tests/ai/conftest.py` |
| E2E 测试配置 | `server/python/tests/ai/e2e/conftest.py` |
| 应用配置 | `server/config/application-local.yml` |

### 5.2 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `E2E_TONGYI_API_KEY` | `sk-623fdfb2b75f43b8bb6a61b8b183359a` | 通义千问 API Key |
| `E2E_GPUSTACK_API_KEY` | `gpustack_14d9f2aee5629a0f_...` | GPUStack API Key |
| `E2E_GPUSTACK_ENDPOINT` | `https://llm-stack.flydiysz.cn` | GPUStack 端点 |

### 5.3 GPUStack 可用模型

```python
GPUSTACK_AVAILABLE_MODELS = [
    "qwen3.5-9b",              # 聊天模型
    "bge-large-zh-v1.5",       # Embedding 模型
    "bge-reranker-large",      # Reranker 模型
    "qwen3-embedding-0.6b",    # Embedding 模型
    "qwen3-reranker-0.6b",     # Reranker 模型
]
```

---

## 六、快速命令参考

```bash
# 运行所有 E2E 测试
uv run pytest -m e2e tests/ai/e2e/ -v

# 运行指定文件
uv run pytest -m e2e tests/ai/e2e/test_plugin_install.py -v

# 生成 HTML 报告
uv run pytest -m e2e tests/ai/e2e/ --html=reports/e2e-report.html --self-contained-html

# 生成覆盖率报告
uv run pytest -m e2e tests/ai/e2e/ --cov=src/ai --cov-report=html

# 并行执行（最大 4 进程）
uv run pytest -m e2e tests/ai/e2e/ -n 4 -v

# 失败时停止
uv run pytest -m e2e tests/ai/e2e/ -x -v

# 详细输出
uv run pytest -m e2e tests/ai/e2e/ -vv --tb=long
```

---

## 相关文档

- 📋 [测试计划](../../server/python/tests/ai/e2e/TEST_PLAN.md)
- 📊 [测试报告模板](../../docs/tests/plugin-e2e-2026-07-02.md)
- 📖 [AI 模块开发指南](../../server/python/src/ai/CLAUDE.md)
- 🔧 [测试编写规范](../../server/python/tests/CLAUDE.md)
