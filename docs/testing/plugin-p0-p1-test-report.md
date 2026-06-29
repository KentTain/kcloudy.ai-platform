# 插件系统 P0/P1 集成测试报告

**测试时间**: 2026-06-29
**测试环境**: Docker 本地环境
**后端地址**: http://localhost:8080
**前端地址**: http://localhost:5173

---

## ✅ 测试通过的功能

### 1. 后端服务状态

| API | 状态 | 说明 |
|-----|------|------|
| `/health` | ✅ 通过 | 服务运行正常 |
| `/ai/console/v1/plugins` | ✅ 通过 | 插件列表 API |
| `/ai/console/v1/plugins/available` | ✅ 通过 | 可用插件列表（9个插件定义） |
| `/ai/console/v1/plugins/installations` (POST) | ✅ 通过 | 插件安装 API |

### 2. 插件安装功能

**测试步骤**：
1. 调用 `POST /ai/console/v1/plugins/installations`
2. 请求体：`{"plugin_id":"langgenius/ollama","auto_start":false}`

**测试结果**：
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "task_id": "1ea7ad6c-cdcc-498d-95fc-dc606a55744c",
    "plugin_id": "langgenius/ollama",
    "status": "pending"
  }
}
```

**验证**：
- ✅ 安装任务创建成功
- ✅ 插件出现在已安装列表中
- ✅ 插件状态为 PENDING

### 3. Tenant 模块事件监听器

**验证方式**：代码检查

**修改文件**：`server/python/src/tenant/module.py`

**修改内容**：
```python
def get_listener_setup(self) -> tuple | None:
    """Tenant 模块消息监听器"""
    from tenant.listeners.setup import cleanup_listeners, setup_listeners
    return (setup_listeners, cleanup_listeners)
```

**状态**：✅ 已启用

### 4. 前端代码完整性

**新增文件**：
- ✅ `web/vue/src/ai/pages/PluginConfigPage.vue`
- ✅ `docs/testing/plugin-p0-p1-test-guide.md`

**修改文件**：
- ✅ `web/vue/src/ai/api/plugin.ts` - 添加 API 函数和类型
- ✅ `web/vue/src/ai/router/index.ts` - 添加配置页面路由
- ✅ `web/vue/src/ai/pages/PluginList.vue` - 添加配置按钮
- ✅ `server/python/src/ai/module.py` - 调整路由注册顺序

---

## ❌ 测试失败的功能

### 1. 配置管理 API

**测试 API**：
- `GET /ai/console/v1/plugins/installations/{plugin_id}/config`
- `PATCH /ai/console/v1/plugins/installations/{plugin_id}/config`

**测试结果**：
```json
{
  "code": 400,
  "msg": "插件不存在: installations/langgenius/ollama/config",
  "data": null
}
```

**失败原因**：

FastAPI 路由冲突问题。当使用 `{plugin_id:path}` 参数时，它会匹配所有剩余路径。

**问题分析**：

```
请求路径: /ai/console/v1/plugins/installations/langgenius/ollama/config

期望匹配:
  installations_router (prefix: /ai/console/v1/plugins/installations)
  路由: /{plugin_id:path}/config
  plugin_id = "langgenius/ollama"

实际匹配:
  console_plugin_router (prefix: /ai/console/v1/plugins)
  路由: /{plugin_id:path}
  plugin_id = "installations/langgenius/ollama/config"
```

**根本原因**：

1. FastAPI 按照路由添加顺序匹配
2. 虽然 `installations_router` 先注册，但它的完整路径是 `/ai/console/v1/plugins/installations/{plugin_id:path}/config`
3. `console_plugin_router` 的 `/{plugin_id:path}` 路由会匹配以 `/ai/console/v1/plugins/` 开头的所有路径
4. 导致 `installations` 被当作 `plugin_id` 的一部分

### 2. 运行时状态 API

**测试 API**：
- `GET /ai/console/v1/plugins/installations/{plugin_id}/runtime-state`
- `GET /ai/console/v1/plugins/installations/statistics`

**状态**：❌ 同样受路由冲突影响

---

## 🔧 解决方案

### 方案 1：修改路由结构（推荐）

**修改文件**：`server/python/src/ai/controllers/console/installations.py`

**修改内容**：使用查询参数替代路径参数

```python
# 修改前
@router.get("/{plugin_id:path}/config")
async def get_plugin_config(
    plugin_id: str = Path(..., description="插件ID"),
    ...
):

# 修改后
@router.get("/config")
async def get_plugin_config(
    plugin_id: str = Query(..., description="插件ID"),
    ...
):
```

**请求方式变更**：
```
修改前: GET /ai/console/v1/plugins/installations/langgenius%2Follama/config
修改后: GET /ai/console/v1/plugins/installations/config?plugin_id=langgenius/ollama
```

**优点**：
- 彻底避免路由冲突
- 更清晰的 API 结构
- 便于前端编码

**缺点**：
- 需要修改 API 规范
- 前端需要相应调整

### 方案 2：使用独立的路径段

**修改文件**：`server/python/src/ai/controllers/console/installations.py`

**修改内容**：将配置 API 移到单独的路由器

```python
# 创建新的路由器
config_router = APIRouter(prefix="/configs", tags=["配置管理"])

@config_router.get("/{plugin_id:path}")
async def get_plugin_config(plugin_id: str = Path(...)):
    ...

# 注册路由
(config_router, "/ai/console/v1/plugins", ["Console - Plugin Configs"]),
```

**请求方式**：
```
GET /ai/console/v1/plugins/configs/langgenius%2Follama
```

### 方案 3：使用 POST 请求体传递 plugin_id

**修改内容**：
```python
@router.post("/config")
async def get_plugin_config(request: PluginConfigRequest):
    plugin_id = request.plugin_id
    ...
```

---

## 📋 修复建议

### 立即修复（P0）

1. **采用方案 1**：修改路由结构，使用查询参数
2. **同步修改前端**：更新 API 调用方式
3. **更新 API 文档**：记录变更

### 后续优化（P1）

1. **统一路由规范**：制定明确的路径参数使用规范
2. **添加路由测试**：在测试中验证所有路由可访问性
3. **API 版本管理**：考虑引入版本控制

---

## 📊 测试覆盖率

| 功能模块 | 后端 API | 前端页面 | 整体状态 |
|---------|---------|---------|---------|
| 插件列表 | ✅ 通过 | ✅ 通过 | ✅ 正常 |
| 插件安装 | ✅ 通过 | ⏸️ 未测试 | ✅ 正常 |
| 插件配置 | ❌ 路由冲突 | ⏸️ 依赖后端 | ❌ 需修复 |
| 运行时状态 | ❌ 路由冲突 | ⏸️ 依赖后端 | ❌ 需修复 |
| 统计数据 | ❌ 路由冲突 | ⏸️ 依赖后端 | ❌ 需修复 |
| 事件监听 | ✅ 已启用 | N/A | ✅ 正常 |

---

## 🎯 下一步行动

1. **决定修复方案**：选择方案 1、2 或 3
2. **实施修复**：修改后端路由和前端 API 调用
3. **重新测试**：验证所有 API 正常工作
4. **更新文档**：记录最终实现方案

---

**建议**：采用方案 1（查询参数），这是最清晰的解决方案，也符合 RESTful API 设计原则。
