/**
 * AI 模块冒烟测试
 *
 * 测试场景：
 * 1. 菜单遍历测试 - 访问所有 AI 页面路径
 * 2. 页面基础渲染验证 - 骨架屏消失、内容可见、无控制台错误
 * 3. 关键页面特定验证
 */
import { test, expect } from '@playwright/test';
import {
  iamUserLogin,
  waitForSkeletonGone,
  verifyPageHasContent,
  captureConsoleErrors,
  waitForPageReady,
} from '../../iam/e2e/fixtures';

// ============================================================================
// 测试场景配置
// ============================================================================

const AI_PAGE_PATHS = ['/ai', '/ai/plugins'];

// ============================================================================
// 测试用例
// ============================================================================

test.describe('AI 模块冒烟测试', () => {
  test.beforeEach(async ({ page, request }) => {
    await iamUserLogin(page, request);
  });

  // ===========================================================================
  // 1. 菜单遍历测试
  // ===========================================================================

  test('遍历所有 AI 页面路径', async ({ page }) => {
    for (const path of AI_PAGE_PATHS) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);

      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain(path);
      await verifyPageHasContent(page);
    }
  });

  // ===========================================================================
  // 2. 页面基础渲染验证
  // ===========================================================================

  test('聊天页面基础渲染', async ({ page }) => {
    await page.goto('/ai');
    await waitForSkeletonGone(page, 10000);

    // 验证输入框可见
    await expect(page.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });

    // 验证空状态或消息区域可见
    const emptyState = page.getByTestId('empty-state');
    const messages = page.locator('[data-testid="user-message"], [data-testid="assistant-message"]');
    const hasEmptyState = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    const hasMessages = await messages.first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasEmptyState || hasMessages).toBeTruthy();

    await verifyPageHasContent(page);
  });

  test('插件管理页面基础渲染', async ({ page }) => {
    await page.goto('/ai/plugins');
    await waitForSkeletonGone(page, 10000);

    // 验证页面容器可见
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible({ timeout: 15000 });

    // 验证统计卡片或表格区域可见
    const statsCards = page.locator('.grid.grid-cols-3');
    const table = page.getByTestId('plugin-list-table');
    const hasStats = await statsCards.isVisible({ timeout: 5000 }).catch(() => false);
    const hasTable = await table.isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasStats || hasTable).toBeTruthy();

    await verifyPageHasContent(page);
  });

  test('页面基础渲染 - 无控制台错误', async ({ page }) => {
    const errors = captureConsoleErrors(page);

    await page.goto('/ai');
    await waitForSkeletonGone(page);
    await page.waitForLoadState('networkidle');

    const criticalErrors = errors.filter(
      (err) =>
        !err.includes('warning') &&
        !err.includes('Warning') &&
        !err.includes('[HMR]')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  // ===========================================================================
  // 3. 页面间导航验证
  // ===========================================================================

  test('AI 页面间快速切换无错误', async ({ page }) => {
    for (const path of AI_PAGE_PATHS) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);
      await page.waitForLoadState('networkidle');
    }
  });

  test('插件配置页面可导航', async ({ page }) => {
    await page.goto('/ai/plugins');
    await waitForSkeletonGone(page);

    // 查找配置按钮
    const configBtn = page.getByTestId('config-btn').first();
    const isVisible = await configBtn.isVisible({ timeout: 10000 }).catch(() => false);

    if (isVisible) {
      await configBtn.click();
      await page.waitForLoadState('networkidle');

      // 验证配置页面加载
      await expect(page.getByTestId('plugin-config-page')).toBeVisible({ timeout: 15000 });
    }
  });
});
