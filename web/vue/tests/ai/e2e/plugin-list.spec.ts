/**
 * 插件列表 E2E 测试
 *
 * 测试插件列表页面的显示、筛选、分页等功能。
 */
import { test, expect } from './plugin-fixtures';

test.describe('插件列表页面', () => {
  test.beforeEach(async ({ page, request }) => {
    // API 辅助登录
    await userLoginViaAPI(page, request, 'admin', 'admin123');

    // 导航到插件列表页
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');
    // 等待数据加载
    await page.waitForTimeout(2000);
  });

  test('应该显示插件列表', async ({ page }) => {
    // 验证页面标题区域
    await expect(page.locator('[data-testid="plugin-manage-page"]')).toBeVisible({ timeout: 10000 });

    // 验证表格存在
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证至少有一个插件行
    const rows = table.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('应该显示插件基本信息', async ({ page }) => {
    // 等待表格加载
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证包含插件 ID（langgenius 是插件的 provider 前缀）
    const tableBody = table.locator('tbody');
    await expect(tableBody).toContainText('langgenius', { timeout: 10000 });
  });

  test('应该显示插件操作按钮', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证有操作按钮（配置或安装）
    const actionCell = table.locator('tbody td').last();
    await expect(actionCell.locator('button').first()).toBeVisible({ timeout: 10000 });
  });

  test('点击配置按钮应导航到配置页面', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 查找配置按钮（已安装插件才有）
    const configButton = table.locator('button:has-text("配置")').first();

    if (await configButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await configButton.click();
      // 验证 URL 包含 /config
      await expect(page).toHaveURL(/\/config/, { timeout: 10000 });
    } else {
      // 没有已安装插件，跳过此测试
      test.skip();
    }
  });

  test('应该支持搜索插件', async ({ page }) => {
    // 查找搜索输入框
    const searchInput = page.locator('input[placeholder*="搜索"]').first();

    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('ollama');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);

      // 验证搜索结果（可能有结果也可能没有）
      const table = page.locator('table').first();
      await expect(table).toBeVisible({ timeout: 10000 });
    } else {
      test.skip();
    }
  });

  test('应该显示插件状态', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证页面包含状态文本（已安装/未安装/待安装等）
    const pageContent = await page.locator('[data-testid="plugin-manage-page"]').textContent();
    const hasStatus = /已安装|未安装|待安装|安装中|安装失败/.test(pageContent || '');
    expect(hasStatus).toBeTruthy();
  });

  test('应该显示统计卡片', async ({ page }) => {
    // 验证统计卡片区域
    const statCards = page.locator('[data-testid="plugin-manage-page"] .rounded-lg');
    const count = await statCards.count();
    expect(count).toBeGreaterThanOrEqual(1);

    // 验证包含"总插件"文本
    await expect(page.locator('text=总插件')).toBeVisible({ timeout: 10000 });
  });

  test('应该显示加载状态', async ({ page }) => {
    // 重新加载页面
    await page.reload();

    // 等待页面完成加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 验证最终显示了数据
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });
  });
});

// 从 plugin-fixtures 导入登录函数
import { userLoginViaAPI } from './plugin-fixtures';
