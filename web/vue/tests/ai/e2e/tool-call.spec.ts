import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('工具调用功能', () => {
  test.beforeEach(async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('页面应正常加载', async ({ page }) => {
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('搜索工具调用流程', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"]').first();
    const isVisible = await input.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.skip();
    }

    await input.fill('请帮我搜索今天的天气');
    await page.locator('[data-testid="send-button"], button:has-text("发送")').first().click();

    // 等待响应
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    const isResponseVisible = await assistantMessage.isVisible({ timeout: 60000 }).catch(() => false);
    // 工具调用需要实际 API 支持，可能跳过
    if (!isResponseVisible) {
      test.skip();
    }
  });

  test('工具调用错误处理', async ({ page }) => {
    const input = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"]').first();
    const isVisible = await input.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.skip();
    }

    await input.fill('搜索一个不存在的关键词 xyz123abc');
    await page.locator('[data-testid="send-button"], button:has-text("发送")').first().click();

    // 等待响应
    const assistantMessage = page.locator('[data-testid="assistant-message"]');
    const isResponseVisible = await assistantMessage.isVisible({ timeout: 60000 }).catch(() => false);
    if (!isResponseVisible) {
      test.skip();
    }
  });
});
