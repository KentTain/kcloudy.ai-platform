# E2E 测试计划：完整对话流程含工具调用

## 概述

本文档描述 AI 对话功能的端到端测试计划。测试覆盖完整对话流程，包括工具调用场景。

## 前置条件

- ✅ 安装 Playwright: `pnpm add -D @playwright/test@1.60.0`
- ✅ 配置 `playwright.config.ts`
- 后端服务运行中
- 测试租户和用户已配置

## 环境配置

```bash
# 安装浏览器
npx playwright install chromium

# 设置环境变量（可选）
export E2E_BASE_URL=http://localhost:5173
```

## 测试文件

### 已实现的测试文件

| 文件 | 描述 |
|------|------|
| `tests/ai/e2e/fixtures.ts` | 测试辅助函数（登录等） |
| `tests/ai/e2e/chat.spec.ts` | 基础对话流程测试 |
| `tests/ai/e2e/tool-call.spec.ts` | 工具调用流程测试 |
| `tests/ai/e2e/conversation.spec.ts` | 会话管理流程测试 |

## 测试场景

### 1. 基础对话流程

```typescript
// tests/ai/e2e/chat.spec.ts

import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('AI 对话功能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('发送消息并收到回复', async ({ page }) => {
    // 输入消息
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('你好，请介绍一下自己');

    // 发送消息
    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();

    // 等待 AI 回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });

    // 验证回复内容非空
    const content = await assistantMessage.textContent();
    expect(content?.length).toBeGreaterThan(0);
  });

  test('切换模型后发送消息', async ({ page }) => {
    // 打开模型选择器
    const modelSelector = page.locator('[data-testid="model-selector"]');
    await expect(modelSelector).toBeVisible({ timeout: 10000 });
    await modelSelector.click();

    // 选择其他模型
    const modelOption = page.locator('[role="option"]').first();
    await expect(modelOption).toBeVisible();
    await modelOption.click();

    // 发送消息验证模型切换生效
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('测试消息');
    await page.locator('[data-testid="send-button"]').click();

    // 等待回复
    const message = page.locator('[data-testid="assistant-message"]');
    await expect(message).toBeVisible({ timeout: 60000 });
  });
});
```

### 2. 工具调用流程

```typescript
// tests/ai/e2e/tool-call.spec.ts

import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('工具调用功能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('搜索工具调用流程', async ({ page }) => {
    // 发送触发工具调用的消息
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('请帮我搜索今天的天气');
    await page.locator('[data-testid="send-button"]').click();

    // 等待工具调用显示
    const toolCall = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCall).toBeVisible({ timeout: 60000 });

    // 验证工具名称
    const toolName = page.locator('[data-testid="tool-name"]');
    const nameText = await toolName.textContent();
    expect(nameText?.toLowerCase()).toContain('search');

    // 等待 AI 基于工具结果的回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });
  });

  test('工具调用错误处理', async ({ page }) => {
    // 发送触发失败场景的消息
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('搜索一个不存在的关键词 xyz123abc');
    await page.locator('[data-testid="send-button"]').click();

    // 即使工具失败，AI 也应给出回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });
  });

  test('多工具连续调用', async ({ page }) => {
    // 发送触发多工具调用的消息
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('先搜索北京天气，再搜索上海天气，然后对比两地天气');
    await page.locator('[data-testid="send-button"]').click();

    // 等待多个工具调用
    const toolCalls = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCalls).toHaveCount(2, { timeout: 90000 });

    // 验证最终回复包含对比内容
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 90000 });
    const content = await assistantMessage.textContent();
    expect(content).toContain('北京');
    expect(content).toContain('上海');
  });
});
```

### 3. 会话管理流程

```typescript
// tests/ai/e2e/conversation.spec.ts

import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('会话管理功能', () => {
  test('创建新会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');

    // 验证输入框存在
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
  });

  test('切换历史会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');

    // 等待会话列表加载
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible({ timeout: 15000 });

    // 点击进入会话
    await conversationItem.click();

    // 验证跳转到对话页面
    await expect(page).toHaveURL(/\/ai\?conversationId=/);

    // 验证历史消息加载
    const messages = page.locator('[data-testid="assistant-message"], [data-testid="user-message"]');
    await expect(messages.first()).toBeVisible({ timeout: 15000 });
  });

  test('删除会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');

    // 等待会话列表加载
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible({ timeout: 15000 });

    // 记录删除前的会话数量
    const countBefore = await page.locator('[data-testid="conversation-item"]').count();

    // 悬停显示删除按钮
    await conversationItem.hover();

    // 点击删除按钮
    const deleteButton = page.locator('[data-testid="delete-conversation"]').first();
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();

    // 确认删除
    const confirmButton = page.locator('button:has-text("删除")').last();
    await confirmButton.click();

    // 验证会话被移除
    if (countBefore > 1) {
      await expect(page.locator('[data-testid="conversation-item"]')).toHaveCount(countBefore - 1, { timeout: 10000 });
    } else {
      // 如果只有一个会话，删除后应显示空状态
      await expect(page.locator('text=暂无会话记录')).toBeVisible({ timeout: 10000 });
    }
  });
});
```

## 数据测试属性 (data-testid)

已在组件中添加的测试属性：

| 组件 | data-testid | 文件 |
|------|-------------|------|
| 聊天输入框 | `chat-input` | `src/ai/pages/ChatPage.vue` |
| 发送按钮 | `send-button` | `src/ai/pages/ChatPage.vue` |
| 用户消息 | `user-message` | `src/ai/pages/ChatPage.vue` |
| AI 消息 | `assistant-message` | `src/ai/pages/ChatPage.vue` |
| 工具调用项 | `tool-call-item` | `src/ai/components/ToolCallItem.vue` |
| 工具名称 | `tool-name` | `src/ai/components/ToolCallItem.vue` |
| 模型选择器 | `model-selector` | `src/ai/components/ModelSelector.vue` |
| 会话项 | `conversation-item` | `src/ai/pages/ConversationListPage.vue` |
| 删除会话按钮 | `delete-conversation` | `src/ai/pages/ConversationListPage.vue` |

## 配置示例

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 使用方式：
 * - pnpm test:e2e              # 运行所有 E2E 测试
 * - pnpm test:e2e tests/ai/    # 运行 AI 模块 E2E 测试
 * - pnpm test:e2e:ui           # UI 模式运行
 */
export default defineConfig({
  testDir: './tests',
  testMatch: '**/e2e/*.spec.ts',
  outputDir: './tests/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { outputFolder: './tests/playwright-report' }]],
  timeout: 60000,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## 运行命令

```bash
# 安装依赖（固定版本）
pnpm add -D @playwright/test@1.60.0

# 安装浏览器
npx playwright install chromium

# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定模块 E2E 测试
pnpm test:e2e tests/ai/

# 带界面运行
pnpm test:e2e:ui tests/ai/

# 查看测试报告
npx playwright show-report tests/playwright-report
```

## 测试环境要求

E2E 测试需要以下环境：

1. **后端服务运行中**
   - Python 后端服务启动并监听正确端口
   - 数据库连接正常
   - AI 服务可用

2. **测试用户配置**
   - 需要在系统中存在测试用户账号
   - 默认使用 `admin/admin123`，可在 `tests/ai/e2e/fixtures.ts` 中修改

3. **前端服务**
   - 由 Playwright 自动启动（`pnpm dev`）
   - 或手动启动后设置 `E2E_BASE_URL`

## 注意事项

- 测试需要完整的后端服务支持
- 首次运行需安装 Playwright 浏览器
- 测试超时设置为 60 秒，AI 响应可能需要较长时间
- 建议在 CI 环境中使用 mock 服务以提高稳定性
