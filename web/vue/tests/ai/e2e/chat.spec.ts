import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('AI 对话功能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('发送消息并收到回复', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
    await input.fill('你好，请介绍一下自己');

    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();

    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessage).toBeVisible({ timeout: 60000 });

    const content = await assistantMessage.textContent();
    expect(content?.length).toBeGreaterThan(0);
  });

  test('切换模型后发送消息', async ({ page }) => {
    const modelSelector = page.locator('[data-testid="model-selector"]');
    await expect(modelSelector).toBeVisible({ timeout: 10000 });
    await modelSelector.click();

    const modelOption = page.locator('[role="option"]').first();
    await expect(modelOption).toBeVisible();
    await modelOption.click();

    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('测试消息');
    await page.locator('[data-testid="send-button"]').click();

    const message = page.locator('[data-testid="assistant-message"]');
    await expect(message).toBeVisible({ timeout: 60000 });
  });
});
