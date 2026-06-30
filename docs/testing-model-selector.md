# ModelSelector 组件测试指南

## 环境准备

### 1. Docker 环境已启动

确认以下服务正在运行：
- PostgreSQL (postgres:5432)
- Redis (redis:6379)
- 后端服务 (localhost:8080)
- 前端服务 (localhost:3000)

### 2. 数据库迁移

确保数据库已执行迁移，包含 `ai.plugin_default_models` 表：

```bash
cd server/python
uv run python manage.py db migrate --module ai
```

## 后端测试

### 运行默认模型 API 集成测试

```bash
# 进入后端目录
cd server/python

# 运行所有 AI 模块集成测试
uv run pytest tests/ai/integration/ -v

# 仅运行默认模型 API 测试
uv run pytest tests/ai/integration/test_default_model_api.py -v

# 运行特定测试类
uv run pytest tests/ai/integration/test_default_model_api.py::TestDefaultModelAPI -v

# 运行特定测试用例
uv run pytest tests/ai/integration/test_default_model_api.py::TestDefaultModelAPI::test_set_and_get_default_model -v

# 生成覆盖率报告
uv run pytest tests/ai/integration/test_default_model_api.py --cov=ai.controllers.console.plugin --cov-report=html
```

### 测试内容

#### TestDefaultModelAPI
- ✅ `test_get_default_model_not_found` - 测试获取不存在的默认模型
- ✅ `test_set_and_get_default_model` - 测试设置和获取默认模型
- ✅ `test_update_default_model` - 测试更新默认模型
- ✅ `test_set_default_model_with_credential` - 测试设置带凭证的默认模型

#### TestModelListAPI
- ✅ `test_get_models_with_icon_fields` - 测试获取模型列表（包含图标字段）
- ✅ `test_models_response_format` - 测试模型列表响应格式符合预期

#### TestDefaultModelIntegration
- ✅ `test_default_model_persistence` - 测试默认模型持久化
- ✅ `test_multiple_model_types` - 测试多种模型类型的默认模型

## 前端测试

### 运行 AiModelSelector 组件单元测试

```bash
# 进入前端目录
cd web/vue

# 运行所有 AI 模块单元测试
pnpm test:unit tests/ai/unit/ --run

# 仅运行 AiModelSelector 组件测试
pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run

# 运行测试并生成覆盖率报告
pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run --coverage

# 使用 UI 界面运行测试
pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run --ui
```

### 测试内容

#### 基础功能测试
- ✅ 正确渲染触发器按钮
- ✅ 在挂载时加载模型列表
- ✅ 显示当前选中的模型
- ✅ 按提供商分组显示模型
- ✅ 显示提供商 Logo

#### 交互功能测试
- ✅ 选择模型后更新 Store
- ✅ 加载并应用默认模型
- ✅ 模型 ID 使用 provider/model 格式
- ✅ Logo 加载失败时隐藏
- ✅ 显示占位文本当未选择模型时
- ✅ 正确处理暗色模式下的 Logo

#### 集成测试
- ✅ 完整的模型选择流程
- ✅ Store 状态持久化到 localStorage

## 手动测试清单

### 1. 后端 API 手动测试

#### 1.1 获取模型列表

```bash
curl -X GET "http://localhost:8080/ai/console/v1/models" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

**预期结果**：
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "icon_small": "https://...",
      "icon_large": "https://...",
      "models": [
        {
          "id": "openai/gpt-4o-mini",
          "name": "gpt-4o-mini",
          "label": "GPT-4o Mini",
          "description": "..."
        }
      ]
    }
  ]
}
```

#### 1.2 设置默认模型

```bash
curl -X POST "http://localhost:8080/ai/console/v1/plugins/default-models" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -d '{
    "model_type": "llm",
    "plugin_id": "openai",
    "model_name": "gpt-4o-mini"
  }'
```

**预期结果**：
```json
{
  "code": 200,
  "data": {
    "id": "...",
    "tenant_id": "...",
    "model_type": "llm",
    "plugin_id": "openai",
    "model_name": "gpt-4o-mini",
    "is_valid": true
  }
}
```

#### 1.3 获取默认模型

```bash
curl -X GET "http://localhost:8080/ai/console/v1/plugins/default-models?model_type=llm" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

**预期结果**：
```json
{
  "code": 200,
  "data": {
    "id": "...",
    "model_type": "llm",
    "plugin_id": "openai",
    "model_name": "gpt-4o-mini"
  }
}
```

### 2. 前端手动测试

#### 2.1 访问 AI 对话页面

1. 打开浏览器访问 `http://localhost:3000/ai`
2. 登录测试用户

#### 2.2 测试模型选择器

- [ ] 验证模型选择器触发器按钮显示
- [ ] 点击按钮，验证弹窗正确打开
- [ ] 验证模型列表正确显示（按提供商分组）
- [ ] 验证提供商 Logo 正确加载
- [ ] 测试搜索过滤功能
- [ ] 选择模型，验证状态正确更新
- [ ] 刷新页面，验证模型选择保持
- [ ] 测试暗色模式下 Logo 样式
- [ ] 测试响应式布局（移动端/桌面端）

#### 2.3 测试默认模型

- [ ] 刷新页面，验证默认模型恢复
- [ ] 选择新模型后，验证 Store 更新
- [ ] 打开新标签页，验证模型选择同步

### 3. 端到端测试

#### 3.1 完整用户流程

1. 访问 AI 对话页面
2. 点击模型选择器
3. 搜索 "gpt-4o"
4. 选择 "GPT-4o"
5. 发送消息，验证使用正确的模型
6. 刷新页面，验证模型选择保持

#### 3.2 多用户场景

1. 打开两个浏览器标签页
2. 在标签页 1 中选择模型 A
3. 切换到标签页 2，验证模型选择独立
4. 在标签页 2 中选择模型 B
5. 切换回标签页 1，验证模型选择未受影响

## 测试问题排查

### 后端测试失败

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 数据库连接失败 | PostgreSQL 未启动 | 检查 Docker 服务状态 |
| 认证失败 | Token 无效 | 检查认证头配置 |
| 404 错误 | 路由未注册 | 检查模块路由配置 |
| 500 错误 | 后端代码异常 | 查看后端日志 |

### 前端测试失败

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 组件无法找到 | 导入路径错误 | 检查组件路径 |
| Store 未初始化 | Pinia 未设置 | 确认 `setActivePinia(createPinia())` |
| Mock 失效 | Mock 配置错误 | 检查 `vi.mock()` 配置 |
| 异步操作超时 | 等待时间不足 | 增加 `setTimeout` 时间 |

### 手动测试问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| Logo 不显示 | 图标 URL 错误 | 检查 `icon_small` 字段 |
| 模型列表为空 | 插件未安装 | 安装模型插件 |
| 默认模型未生效 | 数据库无数据 | 设置默认模型 |
| 弹窗样式异常 | CSS 冲突 | 检查 Tailwind 类名 |

## 测试覆盖率目标

| 类别 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| 后端 API | > 80% | 待测量 |
| 前端组件 | > 80% | 待测量 |
| 集成测试 | 覆盖主要流程 | 待测量 |

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Test ModelSelector

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd server/python
          pip install uv
          uv sync
      - name: Run tests
        run: |
          cd server/python
          uv run pytest tests/ai/integration/test_default_model_api.py -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '22'
      - name: Install dependencies
        run: |
          cd web/vue
          npm install -g pnpm
          pnpm install
      - name: Run tests
        run: |
          cd web/vue
          pnpm test:unit tests/ai/unit/components/AiModelSelector.spec.ts --run
```

## 测试报告

运行测试后，查看生成的测试报告：

- 后端覆盖率报告：`server/python/htmlcov/index.html`
- 前端覆盖率报告：`web/vue/coverage/index.html`

## 相关文档

- [后端测试指南](server/python/tests/CLAUDE.md)
- [前端测试指南](web/vue/tests/CLAUDE.md)
- [API 文档](docs/api.md)
