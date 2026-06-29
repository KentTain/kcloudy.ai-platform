# 插件系统 P0/P1 修复后测试指南

## ⚠️ 重要：需要重启后端服务

代码已修复并推送，需要重启后端服务应用更改：

```bash
# 重启后端服务
docker-compose restart backend
# 或
cd server/python && uv run python manage.py runserver
```

---

## 🔧 修复内容

### 问题
FastAPI 的 `{plugin_id:path}` 通配符路由会匹配所有剩余路径，导致 `/installations` 前缀被当作 `plugin_id` 的一部分。

### 解决方案
将所有使用 `{plugin_id:path}` 的路由改为使用查询参数。

### API 变更对照表

| 修改前 | 修改后 |
|--------|--------|
| `DELETE /installations/{plugin_id}` | `DELETE /installations?plugin_id=xxx` |
| `POST /installations/{plugin_id}/start` | `POST /installations/start?plugin_id=xxx` |
| `POST /installations/{plugin_id}/stop` | `POST /installations/stop?plugin_id=xxx` |
| `GET /installations/{plugin_id}/config` | `GET /installations/config?plugin_id=xxx` |
| `PATCH /installations/{plugin_id}/config` | `PATCH /installations/config?plugin_id=xxx` |
| `GET /installations/{plugin_id}/runtime-state` | `GET /installations/runtime-state?plugin_id=xxx` |

---

## 🧪 测试步骤

### 1. 后端 API 测试

#### 1.1 获取认证 Token

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/iam/console/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account":"admin","password":"admin123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

echo "Token: ${TOKEN:0:50}..."
```

#### 1.2 测试统计数据 API

```bash
curl -s "http://localhost:8080/ai/console/v1/plugins/installations/statistics" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  | python -m json.tool
```

**预期结果**：
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "status_stats": { ... },
    "usage_stats": { ... },
    "runtime_stats": { ... }
  }
}
```

#### 1.3 测试配置管理 API

```bash
# 获取插件配置
curl -s "http://localhost:8080/ai/console/v1/plugins/installations/config?plugin_id=langgenius/ollama" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  | python -m json.tool
```

**预期结果**：
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "plugin_id": "langgenius/ollama",
    "plugin_config": { ... },
    "runtime_config": { ... }
  }
}
```

#### 1.4 测试更新配置 API

```bash
curl -s -X PATCH "http://localhost:8080/ai/console/v1/plugins/installations/config?plugin_id=langgenius/ollama" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  -H "Content-Type: application/json" \
  -d '{"runtime_config": {"test_key": "test_value"}}' \
  | python -m json.tool
```

#### 1.5 测试运行时状态 API

```bash
curl -s "http://localhost:8080/ai/console/v1/plugins/installations/runtime-state?plugin_id=langgenius/ollama" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  | python -m json.tool
```

#### 1.6 测试启动/停止插件 API

```bash
# 启动插件
curl -s -X POST "http://localhost:8080/ai/console/v1/plugins/installations/start?plugin_id=langgenius/ollama" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  | python -m json.tool

# 停止插件
curl -s -X POST "http://localhost:8080/ai/console/v1/plugins/installations/stop?plugin_id=langgenius/ollama" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  | python -m json.tool
```

---

### 2. 前端功能测试

#### 2.1 访问插件配置页面

1. 打开浏览器：http://localhost:5173
2. 登录系统（账号：admin，密码：admin123）
3. 导航到 AI → 插件管理
4. 点击已安装插件的"配置"按钮
5. 验证配置页面正常显示

#### 2.2 测试配置编辑

1. 在配置页面的 JSON 编辑器中修改配置
2. 点击"格式化"按钮
3. 点击"保存"按钮
4. 验证配置保存成功

#### 2.3 测试插件操作

1. 在插件列表页点击"启动"按钮
2. 验证插件状态更新
3. 点击"停止"按钮
4. 验证插件状态更新

---

## 📋 验收清单

### P0 验收项

- [ ] Tenant 模块事件监听器启动成功
- [ ] 前端可以查看插件配置
- [ ] 前端可以更新插件配置
- [ ] 前端可以查看运行时状态
- [ ] 统计数据 API 正常工作

### P1 验收项

- [ ] 配置验证功能正常
- [ ] 运行时状态实时更新
- [ ] 统计数据展示正确

---

## 🎯 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `server/python/src/ai/controllers/console/installations.py` | 路由改为查询参数 |
| `web/vue/src/ai/api/plugin.ts` | API 函数改用查询参数 |
| `web/vue/src/ai/pages/PluginList.vue` | 使用新的 API 函数 |

---

## ⚠️ 注意事项

1. **后端必须重启**才能应用路由修改
2. **前端无需重启**，热更新即可
3. 测试时注意 `plugin_id` 参数值是 `langgenius/ollama`（包含斜杠）
4. 查询参数会自动处理 URL 编码

---

**状态**：✅ 代码已修复并推送，等待重启后端服务进行测试
