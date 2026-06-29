# 插件管理 E2E 测试

本目录包含插件管理功能的完整 E2E 测试套件。

## 快速开始

### 安装依赖

```bash
cd web/vue
pnpm install
npx playwright install chromium
```

### 运行测试

```bash
# 启动服务
# 终端 1: 后端
cd server/python
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 终端 2: 前端
cd web/vue
pnpm dev

# 终端 3: 运行测试
pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
```

## 测试文件

| 文件 | 说明 | 用例数 |
|------|------|--------|
| [plugin-fixtures.ts](./plugin-fixtures.ts) | 测试辅助函数和 API 工具 | - |
| [plugin-list.spec.ts](./plugin-list.spec.ts) | 插件列表页面测试 | 9 |
| [plugin-config.spec.ts](./plugin-config.spec.ts) | 插件配置页面测试 | 14 |
| [plugin-operations.spec.ts](./plugin-operations.spec.ts) | 插件操作测试 | 9 |
| [plugin-api.spec.ts](./plugin-api.spec.ts) | 插件 API 测试 | 12 |

**总计**: 44 个测试用例

## 测试覆盖

### 功能覆盖

- ✅ 插件列表显示
- ✅ 插件搜索筛选
- ✅ 插件分页
- ✅ 插件配置查看
- ✅ 插件配置编辑
- ✅ 配置验证和格式化
- ✅ 配置保存和重置
- ✅ 插件启动/停止
- ✅ 插件卸载
- ✅ 运行时状态查询
- ✅ 统计数据查询
- ✅ 错误处理和验证

### API 覆盖

| API | 方法 | 覆盖 |
|-----|------|------|
| `/ai/console/v1/plugins` | GET | ✅ |
| `/ai/console/v1/plugins/installations/config` | GET | ✅ |
| `/ai/console/v1/plugins/installations/config` | PATCH | ✅ |
| `/ai/console/v1/plugins/installations/runtime-state` | GET | ✅ |
| `/ai/console/v1/plugins/installations/statistics` | GET | ✅ |
| `/ai/console/v1/plugins/installations/start` | POST | ✅ |
| `/ai/console/v1/plugins/installations/stop` | POST | ✅ |
| `/ai/console/v1/plugins/runtime-states` | GET | ✅ |

## 测试示例

### 插件列表测试

```typescript
test('应该显示插件列表', async ({ page }) => {
  const table = page.locator('table').first();
  await expect(table).toBeVisible({ timeout: 10000 });

  const rows = table.locator('tbody tr');
  const count = await rows.count();
  expect(count).toBeGreaterThan(0);
});
```

### 插件配置测试

```typescript
test('保存有效配置应成功', async ({ page }) => {
  const editor = page.locator('textarea').first();
  const currentValue = await editor.inputValue();

  const newValue = currentValue.replace(/\}\s*$/, ', "test_key": "test_value"}');
  await editor.fill(newValue);

  const saveButton = page.locator('button:has-text("保存配置")').first();
  await saveButton.click();

  const successMessage = page.locator('text=配置已保存').first();
  await expect(successMessage).toBeVisible({ timeout: 10000 });
});
```

### API 测试

```typescript
test('获取插件列表', async ({ request }) => {
  const response = await request.get('/api/ai/console/v1/plugins', {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': TENANT_ID,
    },
  });

  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.code).toBe(200);
});
```

## 工具函数

### 登录辅助

```typescript
import { userLoginViaAPI } from './plugin-fixtures';

await userLoginViaAPI(page, request);
```

### API 辅助

```typescript
import { getPluginList, getPluginConfig, updatePluginConfig } from './plugin-fixtures';

const plugins = await getPluginList(request, token, tenantId);
const config = await getPluginConfig(request, token, tenantId, pluginId);
await updatePluginConfig(request, token, tenantId, pluginId, { key: 'value' });
```

### 页面辅助

```typescript
import { waitForPluginListReady, loginAndGotoPluginConfig } from './plugin-fixtures';

await waitForPluginListReady(page);
await loginAndGotoPluginConfig(page, request, pluginId);
```

## 调试技巧

### 查看 UI 模式

```bash
pnpm test:e2e:ui tests/ai/e2e/plugin-list.spec.ts
```

### 查看详细日志

```bash
DEBUG=pw:api pnpm test:e2e tests/ai/e2e/plugin-list.spec.ts
```

### 生成 Trace

```bash
pnpm test:e2e tests/ai/e2e/plugin-list.spec.ts
npx playwright show-trace tests/test-results/*/trace.zip
```

## 性能优化

### 单线程运行

```bash
E2E_WORKERS=1 pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
```

### 减少浏览器内存

在 `playwright.config.ts` 中已配置优化参数。

## 持续集成

```yaml
# .github/workflows/e2e.yml
- name: Run Plugin E2E Tests
  run: |
    cd web/vue
    pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
  env:
    CI: true
```

## 维护

### 更新选择器

当 UI 变化时，更新选择器：

```typescript
// 推荐：使用 data-testid
page.locator('[data-testid="plugin-list-table"]')

// 备用：使用语义化选择器
page.locator('table').first()
```

### 添加新测试

1. 在 `tests/ai/e2e/` 创建或修改测试文件
2. 使用 `plugin-fixtures.ts` 中的工具函数
3. 运行测试验证

## 故障排除

### 测试超时

- 检查后端服务是否运行
- 检查前端服务是否运行
- 增加超时时间（`playwright.config.ts`）

### 测试失败

- 查看截图：`tests/test-results/*/`
- 查看 Trace：`npx playwright show-trace`
- 查看 HTML 报告：`npx playwright show-report`

### 内存不足

```bash
E2E_WORKERS=1 pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
```

## 相关文档

- [测试计划](./PLUGIN_TEST_PLAN.md) - 详细的测试计划和场景
- [测试指南](../CLAUDE.md) - 测试目录指南
- [Playwright 文档](https://playwright.dev/) - 官方文档
