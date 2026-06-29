# 插件系统 P0/P1 功能测试指南

## ⚠️ 重要：需要重启后端服务

由于修改了路由注册顺序，需要重启后端服务来应用更改：

```bash
# 重启后端服务（根据您的启动方式选择）
docker-compose restart backend
# 或
cd server/python && uv run python manage.py runserver
```

## 1. 后端 API 测试

### 1.1 获取认证 Token

```bash
curl -X POST http://localhost:8080/iam/console/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account":"admin","password":"admin123"}'
```

记录返回的 `access_token`。

### 1.2 测试统计数据 API

```bash
TOKEN="<your_access_token>"

curl http://localhost:8080/ai/console/v1/plugins/installations/statistics \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000"
```

**预期结果**：
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "status_stats": {
      "active": 0,
      "inactive": 0,
      "frozen": 0,
      "total": 0
    },
    "usage_stats": {
      "total_calls": 0,
      "total_errors": 0,
      "avg_success_rate": 100.0
    },
    "runtime_stats": {
      "total_memory_mb": 0.0,
      "total_cpu_percent": 0.0
    }
  }
}
```

### 1.3 测试配置管理 API（需要先安装插件）

```bash
# 获取插件配置
curl http://localhost:8080/ai/console/v1/plugins/installations/{plugin_id}/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000"

# 更新插件配置
curl -X PATCH http://localhost:8080/ai/console/v1/plugins/installations/{plugin_id}/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000" \
  -H "Content-Type: application/json" \
  -d '{"runtime_config": {"key": "value"}}'
```

### 1.4 测试运行时状态 API

```bash
# 获取单个插件运行时状态
curl http://localhost:8080/ai/console/v1/plugins/installations/{plugin_id}/runtime-state \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Id: 00000000-0000-0000-0000-000000000000"
```

## 2. 前端功能测试

### 2.1 访问插件配置页面

1. 打开浏览器，访问前端应用：http://localhost:5173
2. 登录系统（账号：admin，密码：admin123）
3. 导航到 AI → 插件管理
4. 如果有已安装的插件，点击"配置"按钮
5. 验证配置页面是否正确显示：
   - 插件能力配置（只读）
   - 运行时配置编辑器（JSON 编辑器）
   - 保存和重置按钮

### 2.2 测试配置编辑功能

1. 在配置页面的 JSON 编辑器中修改配置
2. 点击"格式化"按钮，验证 JSON 格式化
3. 点击"保存"按钮，验证配置保存
4. 刷新页面，验证配置是否持久化

### 2.3 测试运行时状态展示

1. 在插件列表页，查看表格中的"调用次数"列
2. 启动一个插件
3. 刷新页面，查看状态更新
4. 查看运行时状态详情

## 3. 事件监听器验证

### 3.1 检查监听器启动日志

查看后端启动日志，应该看到：

```
INFO: Tenant 事件监听器注册完成
INFO: 创建消费者组: plugin_installation_failed_events -> tenant_plugin_handlers_group
INFO: 创建消费者组: plugin_uninstall_failed_events -> tenant_plugin_handlers_group
```

### 3.2 验证事件处理

可以通过模拟安装失败场景来验证事件处理流程。

## 4. 修改文件清单

### 后端修改

| 文件 | 修改内容 |
|------|---------|
| `server/python/src/tenant/module.py` | 启用事件监听器 |
| `server/python/src/ai/module.py` | 调整路由注册顺序，避免通配符路由冲突 |

### 前端修改

| 文件 | 修改内容 |
|------|---------|
| `web/vue/src/ai/api/plugin.ts` | 添加配置和运行时状态 API 函数和类型 |
| `web/vue/src/ai/pages/PluginConfigPage.vue` | 新增配置页面 |
| `web/vue/src/ai/router/index.ts` | 添加配置页面路由 |
| `web/vue/src/ai/pages/PluginList.vue` | 添加"配置"操作按钮 |

## 5. API 端点清单

### 配置管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ai/console/v1/plugins/installations/{plugin_id}/config` | 获取插件配置 |
| PATCH | `/ai/console/v1/plugins/installations/{plugin_id}/config` | 更新插件配置 |

### 运行时状态

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ai/console/v1/plugins/installations/{plugin_id}/runtime-state` | 获取单个插件运行时状态 |
| GET | `/ai/console/v1/plugins/installations/statistics` | 获取插件统计数据 |

## 6. 故障排查

### 问题：统计数据 API 返回 404

**原因**：路由冲突，通配符路由 `/{plugin_id:path}` 拦截了请求。

**解决方案**：已调整路由注册顺序，确保 `installations_router` 先于 `console_plugin_router` 注册。

**验证**：重启后端服务后，访问统计数据 API 应返回 200。

### 问题：配置页面无法访问

**原因**：前端路由或 API 路径不正确。

**验证步骤**：
1. 检查前端路由是否正确配置
2. 检查 API 路径是否包含 `/installations`
3. 查看浏览器控制台是否有错误

### 问题：监听器未启动

**验证步骤**：
1. 检查 `tenant/module.py` 的 `get_listener_setup()` 方法是否返回正确的元组
2. 查看启动日志确认监听器注册
3. 检查 Redis 连接是否正常

## 7. 验收标准

### P0 验收项

- [x] Tenant 模块事件监听器启动成功
- [ ] 前端可以查看插件配置（需重启后验证）
- [ ] 前端可以更新插件配置（需重启后验证）
- [ ] 前端可以查看运行时状态（需重启后验证）
- [ ] 安装失败事件能够正确处理（需测试）

### P1 验收项

- [ ] 配置验证功能正常（需测试）
- [ ] 运行时状态实时更新（需测试）
- [ ] 统计数据展示正确（需测试）

## 8. 下一步

1. **重启后端服务**：应用路由顺序修改
2. **完整功能测试**：按照上述测试指南进行全面测试
3. **创建测试数据**：安装一个测试插件，验证完整流程
4. **性能测试**：测试配置更新和状态查询的性能

---

**注意**：所有修改已完成，等待重启后端服务进行验证。
