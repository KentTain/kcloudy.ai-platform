import { test, expect } from '@playwright/test';
import { login } from './fixtures';

test.describe('会话管理功能', () => {
  test('创建新会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');

    const input = page.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 10000 });
  });

  test('切换历史会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible({ timeout: 15000 });

    await conversationItem.click();

    await expect(page).toHaveURL(/\/ai\?conversationId=/);

    const messages = page.locator('[data-testid="assistant-message"], [data-testid="user-message"]');
    await expect(messages.first()).toBeVisible({ timeout: 15000 });
  });

  test('删除会话', async ({ page }) => {
    await login(page);
    await page.goto('/ai/conversations');
    await page.waitForLoadState('networkidle');

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    await expect(conversationItem).toBeVisible({ timeout: 15000 });

    const countBefore = await page.locator('[data-testid="conversation-item"]').count();

    await conversationItem.hover();

    const deleteButton = page.locator('[data-testid="delete-conversation"]').first();
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();

    const confirmButton = page.locator('button:has-text("删除")').last();
    await confirmButton.click();

    if (countBefore > 1) {
      await expect(page.locator('[data-testid="conversation-item"]')).toHaveCount(countBefore - 1, { timeout: 10000 });
    } else {
      await expect(page.locator('text=暂无会话记录')).toBeVisible({ timeout: 10000 });
    }
  });
});
