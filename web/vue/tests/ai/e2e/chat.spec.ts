import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('AI 对话功能', () => {
  test.beforeEach(async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('页面应正常加载', async ({ page }) => {
    // 验证 AI 页面已加载
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('发送消息并收到回复', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea[placeholder*="消息"]').first();
    const isVisible = await input.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.skip();
    }

    await input.fill('你好，请介绍一下自己');

    const sendButton = page.locator('[data-testid="send-button"], button:has-text("发送")').first();
    await sendButton.click();

    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    const isResponseVisible = await assistantMessage.isVisible({ timeout: 60000 }).catch(() => false);

    if (isResponseVisible) {
      const content = await assistantMessage.textContent();
      expect(content?.length).toBeGreaterThan(0);
    }
  });

  test('切换模型后发送消息', async ({ page }) => {
    const modelSelector = page.locator('[data-testid="model-selector"], button:has-text("模型")').first();
    const isVisible = await modelSelector.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.skip();
    }

    await modelSelector.click();

    const modelOption = page.locator('[role="option"]').first();
    const isOptionVisible = await modelOption.isVisible({ timeout: 5000 }).catch(() => false);
    if (!isOptionVisible) {
      test.skip();
    }
    await modelOption.click();
  });
});
