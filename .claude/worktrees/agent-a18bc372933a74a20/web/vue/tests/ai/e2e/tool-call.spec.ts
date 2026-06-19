import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('工具调用功能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('搜索工具调用流程', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('请帮我搜索今天的天气');
    await page.locator('[data-testid="send-button"]').click();

    const toolCall = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCall).toBeVisible({ timeout: 60000 });

    const toolName = page.locator('[data-testid="tool-name"]');
    const nameText = await toolName.textContent();
    expect(nameText?.toLowerCase()).toContain('search');

    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });
  });

  test('工具调用错误处理', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('搜索一个不存在的关键词 xyz123abc');
    await page.locator('[data-testid="send-button"]').click();

    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });
  });

  test('多工具连续调用', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('先搜索北京天气，再搜索上海天气，然后对比两地天气');
    await page.locator('[data-testid="send-button"]').click();

    const toolCalls = page.locator('[data-testid="tool-call-item"]');
    await expect(toolCalls).toHaveCount(2, { timeout: 90000 });

    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 90000 });
    const content = await assistantMessage.textContent();
    expect(content).toContain('北京');
    expect(content).toContain('上海');
  });
});
