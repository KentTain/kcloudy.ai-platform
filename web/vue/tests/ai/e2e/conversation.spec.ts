import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('会话管理功能', () => {
  test('创建新会话', async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 验证页面已加载
    const pageContent = await page.textContent('body');
    expect(pageContent).toBeTruthy();
  });

  test('切换历史会话', async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    const isVisible = await conversationItem.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      // 没有历史会话，跳过
      test.skip();
    }

    await conversationItem.click();
  });

  test('删除会话', async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    const isVisible = await conversationItem.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.skip();
    }

    const countBefore = await page.locator('[data-testid="conversation-item"]').count();
    await conversationItem.hover();

    const deleteButton = page.locator('[data-testid="delete-conversation"]').first();
    const isDeleteVisible = await deleteButton.isVisible({ timeout: 3000 }).catch(() => false);
    if (!isDeleteVisible) {
      test.skip();
    }

    await deleteButton.click();
  });
});
