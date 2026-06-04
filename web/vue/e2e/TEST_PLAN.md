# E2E 测试计划：完整对话流程含工具调用

## 概述

本文档描述 AI 对话功能的端到端测试计划。测试覆盖完整对话流程，包括工具调用场景。

## 前置条件

- 安装 Playwright: `pnpm add -D @playwright/test`
- 配置 `playwright.config.ts`
- 后端服务运行中
- 测试租户和用户已配置

## 测试场景

### 1. 基础对话流程

```typescript
// e2e/chat.spec.ts

import { test, expect } from '@playwright/test';

test.describe('AI 对话功能', () => {
  test.beforeEach(async ({ page }) => {
    // 登录并导航到 AI 对话页面
    await page.goto('/ai/chat');
    await page.waitForLoadState('networkidle');
  });

  test('发送消息并收到回复', async ({ page }) => {
    // 输入消息
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('你好，请介绍一下自己');

    // 发送消息
    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();

    // 等待 AI 回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });

    // 验证回复内容非空
    const content = await assistantMessage.textContent();
    expect(content?.length).toBeGreaterThan(0);
  });

  test('切换模型后发送消息', async ({ page }) => {
    // 打开模型选择器
    const modelSelector = page.locator('[data-testid="model-selector"]');
    await modelSelector.click();

    // 选择其他模型
    const modelOption = page.locator('text=GPT-4o');
    await modelOption.click();

    // 发送消息验证模型切换生效
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('测试消息');
    await page.locator('[data-testid="send-button"]').click();

    // 等待回复
    const message = page.locator('[data-testid="assistant-message"]');
    await expect(message).toBeVisible({ timeout: 30000 });
  });
});
```

### 2. 工具调用流程

```typescript
// e2e/tool-call.spec.ts

import { test, expect } from '@playwright/test';

test.describe('工具调用功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ai/chat');
    await page.waitForLoadState('networkidle');
  });

  test('搜索工具调用流程', async ({ page }) => {
    // 发送触发工具调用的消息
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('请帮我搜索今天的天气');
    await page.locator('[data-testid="send-button"]').click();

    // 等待工具调用显示
    const toolCall = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCall).toBeVisible({ timeout: 30000 });

    // 验证工具名称
    const toolName = await toolCall.locator('[data-testid="tool-name"]').textContent();
    expect(toolName).toContain('search');

    // 等待工具结果
    const toolResult = page.locator('[data-testid="tool-result"]');
    await expect(toolResult).toBeVisible({ timeout: 30000 });

    // 验证 AI 基于工具结果的回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
  });

  test('工具调用错误处理', async ({ page }) => {
    // 发送触发失败场景的消息
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('搜索一个不存在的关键词 xyz123abc');
    await page.locator('[data-testid="send-button"]').click();

    // 等待工具结果显示
    const toolResult = page.locator('[data-testid="tool-result"]');
    await expect(toolResult).toBeVisible({ timeout: 30000 });

    // 验证错误状态显示
    const errorState = page.locator('[data-testid="tool-error"]');
    // 即使工具失败，AI 也应给出回复
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
  });

  test('多工具连续调用', async ({ page }) => {
    // 发送触发多工具调用的消息
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('先搜索北京天气，再搜索上海天气，然后对比两地天气');
    await page.locator('[data-testid="send-button"]').click();

    // 等待多个工具调用
    const toolCalls = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCalls).toHaveCount(2, { timeout: 30000 });

    // 验证最终回复包含对比内容
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });
    const content = await assistantMessage.textContent();
    expect(content).toContain('北京');
    expect(content).toContain('上海');
  });
});
```

### 3. 会话管理流程

```typescript
// e2e/conversation.spec.ts

import { test, expect } from '@playwright/test';

test.describe('会话管理功能', () => {
  test('创建新会话', async ({ page }) => {
    await page.goto('/ai/chat');

    // 开始新对话
    const newChatButton = page.locator('text=新对话');
    await newChatButton.click();

    // 验证输入框清空
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toHaveValue('');
  });

  test('切换历史会话', async ({ page }) => {
    await page.goto('/ai/conversations');

    // 等待会话列表加载
    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible();

    // 点击进入会话
    await conversationItem.click();

    // 验证跳转到对话页面
    await expect(page).toHaveURL(/\/ai\/chat\?conversationId=/);

    // 验证历史消息加载
    const messages = page.locator('[data-testid="message-item"]');
    await expect(messages.first()).toBeVisible();
  });

  test('删除会话', async ({ page }) => {
    await page.goto('/ai/conversations');

    // 点击删除按钮
    const deleteButton = page.locator('[data-testid="delete-conversation"]').first();
    await deleteButton.click();

    // 确认删除
    const confirmButton = page.locator('text=删除');
    await confirmButton.click();

    // 验证会话被移除
    await expect(page.locator('[data-testid="conversation-item"]').first()).not.toBeVisible();
  });
});
```

## 数据测试属性 (data-testid)

需要在组件中添加以下测试属性：

| 组件 | data-testid |
|------|-------------|
| 聊天输入框 | `chat-input` |
| 发送按钮 | `send-button` |
| 用户消息 | `user-message` |
| AI 消息 | `assistant-message` |
| 工具调用项 | `tool-call-item` |
| 工具名称 | `tool-name` |
| 工具结果 | `tool-result` |
| 工具错误 | `tool-error` |
| 模型选择器 | `model-selector` |
| 会话项 | `conversation-item` |
| 删除会话按钮 | `delete-conversation` |

## 配置示例

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
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
  },
});
```

## 运行命令

```bash
# 安装依赖
pnpm add -D @playwright/test

# 安装浏览器
npx playwright install

# 运行测试
npx playwright test

# 带界面运行
npx playwright test --ui
```
