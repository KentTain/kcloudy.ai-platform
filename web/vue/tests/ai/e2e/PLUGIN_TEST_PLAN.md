# 插件管理 E2E 测试计划

## 测试概述

本测试计划覆盖插件管理功能的所有 E2E 测试场景，包括插件列表、配置管理、运行时状态、插件操作等。

## 测试文件

| 文件 | 说明 | 测试用例数 |
|------|------|-----------|
| `plugin-list.spec.ts` | 插件列表页面测试 | 9 |
| `plugin-config.spec.ts` | 插件配置页面测试 | 14 |
| `plugin-operations.spec.ts` | 插件操作测试 | 9 |
| `plugin-api.spec.ts` | 插件 API 测试 | 12 |
| **总计** | - | **44** |

## 测试环境要求

### 必需服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8080 | Python FastAPI 服务 |
| 前端应用 | http://localhost:5173 | Vue 应用 |
| 数据库 | PostgreSQL 14+ | - |
| 缓存 | Redis 6+ | - |

### 测试账号

- 账号: `admin`
- 密码: `admin123`
- 租户 ID: `00000000-0000-0000-0000-000000000000`

## 测试场景

### 1. 插件列表页面 (plugin-list.spec.ts)

#### 1.1 显示测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示插件列表 | 验证表格和基本元素 | P0 |
| 应该显示插件基本信息 | 验证插件 ID、名称、状态 | P0 |
| 应该显示插件操作按钮 | 验证配置、启动、停止按钮 | P0 |

#### 1.2 交互测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 点击配置按钮应导航到配置页面 | 验证页面跳转 | P0 |
| 应该支持搜索插件 | 验证搜索功能 | P1 |
| 应该显示分页组件 | 验证分页功能 | P1 |

#### 1.3 UI 测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示插件状态徽章 | 验证状态显示 | P1 |
| 应该显示插件类型 | 验证类型显示 | P1 |
| 应该显示加载状态 | 验证骨架屏/加载指示器 | P1 |

### 2. 插件配置页面 (plugin-config.spec.ts)

#### 2.1 显示测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示插件配置页面 | 验证页面标题和插件 ID | P0 |
| 应该显示返回按钮 | 验证导航功能 | P0 |
| 应该显示插件能力配置区域 | 验证只读配置展示 | P0 |
| 应该显示运行时配置编辑区域 | 验证 JSON 编辑器 | P0 |

#### 2.2 编辑测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示格式化按钮 | 验证 JSON 格式化 | P0 |
| 应该显示重置按钮 | 验证重置功能 | P0 |
| 应该显示保存按钮 | 验证保存功能 | P0 |
| 编辑配置后保存按钮应该可用 | 验证状态管理 | P0 |

#### 2.3 验证测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 输入无效 JSON 应显示错误提示 | 验证输入验证 | P0 |
| 点击格式化按钮应格式化 JSON | 验证格式化功能 | P0 |
| 未修改配置时保存按钮应禁用 | 验证变更检测 | P1 |

#### 2.4 操作测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 点击返回按钮应导航到插件列表 | 验证导航 | P0 |
| 点击重置按钮应恢复原始配置 | 验证重置功能 | P0 |
| 保存有效配置应成功 | 验证保存流程 | P0 |

#### 2.5 边界测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该正确处理空配置 | 验证空值处理 | P1 |
| 应该正确处理特殊字符 | 验证字符编码 | P1 |

### 3. 插件操作 (plugin-operations.spec.ts)

#### 3.1 按钮测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示启动按钮 | 验证启动按钮存在 | P0 |
| 应该显示停止按钮 | 验证停止按钮存在 | P1 |
| 应该显示卸载按钮 | 验证卸载按钮存在 | P1 |

#### 3.2 操作测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 点击启动按钮应触发操作 | 验证启动流程 | P0 |
| 操作后应更新状态 | 验证状态更新 | P0 |
| 应该显示操作结果通知 | 验证反馈机制 | P0 |

#### 3.3 错误处理测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 应该显示操作确认对话框 | 验证确认机制 | P1 |
| 应该显示操作加载状态 | 验证加载反馈 | P1 |
| 应该正确处理操作失败 | 验证错误处理 | P1 |

### 4. 插件 API (plugin-api.spec.ts)

#### 4.1 基本 API 测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 获取插件列表 | GET /plugins | P0 |
| 获取插件配置 | GET /installations/config | P0 |
| 更新插件配置 | PATCH /installations/config | P0 |
| 获取运行时状态 | GET /installations/runtime-state | P0 |
| 获取统计数据 | GET /installations/statistics | P0 |

#### 4.2 操作 API 测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 启动插件 | POST /installations/start | P0 |
| 停止插件 | POST /installations/stop | P0 |

#### 4.3 错误处理测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 获取不存在的插件配置应返回错误 | 验证 404 处理 | P0 |
| 无认证访问应返回 401 | 验证认证检查 | P0 |
| 无租户 ID 应返回 400 | 验证租户检查 | P0 |

#### 4.4 边界测试

| 测试用例 | 说明 | 优先级 |
|---------|------|--------|
| 更新配置为空对象应成功 | 验证空值处理 | P1 |
| 批量运行时状态查询 | 验证批量接口 | P1 |

## 运行测试

### 前置条件

```bash
# 1. 安装依赖
cd web/vue
pnpm install

# 2. 安装 Playwright 浏览器
npx playwright install chromium

# 3. 启动后端服务
cd server/python
uv run python manage.py runserver --host 0.0.0.0 --port 8080

# 4. 启动前端服务（在另一个终端）
cd web/vue
pnpm dev
```

### 运行命令

```bash
# 运行所有插件测试
pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts

# 运行特定测试文件
pnpm test:e2e tests/ai/e2e/plugin-list.spec.ts
pnpm test:e2e tests/ai/e2e/plugin-config.spec.ts
pnpm test:e2e tests/ai/e2e/plugin-operations.spec.ts
pnpm test:e2e tests/ai/e2e/plugin-api.spec.ts

# 带 UI 运行
pnpm test:e2e:ui tests/ai/e2e/plugin-*.spec.ts

# 生成 HTML 报告
pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
npx playwright show-report
```

### 性能优化

内存不足时使用单线程运行：

```bash
E2E_WORKERS=1 pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
```

## 测试数据

### 测试插件

- `langgenius/ollama` - Ollama 插件
- `langgenius/openai` - OpenAI 插件

### 测试配置键

使用时间戳确保唯一性：

```typescript
const timestamp = Date.now();
const testKey = `e2e_test_${timestamp}`;
const testValue = `test_value_${timestamp}`;
```

## 测试覆盖目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| 插件列表 | 100% | - |
| 插件配置 | 100% | - |
| 插件操作 | 90% | - |
| 插件 API | 100% | - |

## 持续集成

测试应集成到 CI/CD 流程中：

```yaml
# .github/workflows/e2e-test.yml
- name: Run E2E Tests
  run: |
    cd web/vue
    pnpm test:e2e tests/ai/e2e/plugin-*.spec.ts
```

## 测试报告

测试完成后生成以下报告：

1. **控制台输出**: 实时显示测试进度
2. **HTML 报告**: `tests/playwright-report/index.html`
3. **测试结果**: `tests/test-results/`

## 维护指南

### 添加新测试

1. 在 `tests/ai/e2e/` 创建新测试文件
2. 使用 `plugin-fixtures.ts` 中的辅助函数
3. 遵循现有测试的命名和结构

### 更新选择器

当 UI 变化时，更新测试中的选择器：

```typescript
// 优先使用 data-testid
page.locator('[data-testid="plugin-list-table"]')

// 其次使用语义化选择器
page.locator('table').first()
```

### 调试测试

```bash
# 查看浏览器操作
pnpm test:e2e:ui tests/ai/e2e/plugin-list.spec.ts

# 查看详细日志
DEBUG=pw:api pnpm test:e2e tests/ai/e2e/plugin-list.spec.ts
```

## 注意事项

1. **测试隔离**: 每个测试独立运行，不依赖其他测试
2. **数据清理**: 测试完成后不清理数据（演示环境）
3. **并发限制**: 内存不足时设置 `E2E_WORKERS=1`
4. **超时设置**: 默认 60 秒，可在 `playwright.config.ts` 调整

## 相关文档

- [测试指南](../CLAUDE.md)
- [Playwright 文档](https://playwright.dev/)
- [AI 模块文档](../../../src/ai/CLAUDE.md)
