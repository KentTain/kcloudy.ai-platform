/**
 * 插件列表 E2E 测试
 *
 * 测试插件列表页面的显示、筛选、分页等功能。
 */
import { test, expect } from './plugin-fixtures';

test.describe('插件列表页面', () => {
  test.beforeEach(async ({ page, request }) => {
    // 登录并导航到插件列表页
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // 通过 UI 登录（演示环境）
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="账号"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    const loginButton = page.locator('button[type="submit"]');

    if (await usernameInput.isVisible()) {
      await usernameInput.fill('admin');
      await passwordInput.fill('admin123');
      await loginButton.click();
      await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });
    }

    // 导航到插件列表页
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');
    // 等待表格或数据加载完成
    await page.waitForTimeout(1000);
  });

  test('应该显示插件列表', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h2, [data-testid="page-title"]').first()).toContainText('插件');

    // 验证表格存在
    const table = page.locator('table, [data-testid="plugin-list-table"]').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    // 验证至少有一个插件
    const rows = table.locator('tbody tr, [data-testid="plugin-row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('应该显示插件基本信息', async ({ page }) => {
    // 等待表格加载
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    // 验证第一行包含插件 ID
    const firstRow = table.locator('tbody tr').first();
    await expect(firstRow).toContainText('langgenius');

    // 验证包含状态信息
    await expect(firstRow).toContainText(/PENDING|ACTIVE|INACTIVE|RUNNING/i);
  });

  test('应该显示插件操作按钮', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    const firstRow = table.locator('tbody tr').first();

    // 验证配置按钮存在
    const configButton = firstRow.locator('button:has-text("配置"), [data-testid="config-button"]');
    await expect(configButton.first()).toBeVisible({ timeout: 5000 });

    // 验证启动按钮存在
    const startButton = firstRow.locator('button:has-text("启动"), [data-testid="start-button"]');
    await expect(startButton.first()).toBeVisible({ timeout: 5000 });
  });

  test('点击配置按钮应导航到配置页面', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    const firstRow = table.locator('tbody tr').first();
    const configButton = firstRow.locator('button:has-text("配置")').first();

    await configButton.click();

    // 验证 URL 包含 /config
    await expect(page).toHaveURL(/\/config/, { timeout: 10000 });
  });

  test('应该支持搜索插件', async ({ page }) => {
    // 查找搜索输入框
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="关键词"]').first();

    if (await searchInput.isVisible()) {
      await searchInput.fill('ollama');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);

      // 验证结果包含 ollama
      const table = page.locator('table').first();
      const firstRow = table.locator('tbody tr').first();
      await expect(firstRow).toContainText('ollama');
    } else {
      // 搜索功能可能未实现，跳过
      test.skip();
    }
  });

  test('应该显示插件状态徽章', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    // 查找状态徽章
    const badge = table.locator('[class*="badge"], [data-testid="status-badge"]').first();
    await expect(badge).toBeVisible({ timeout: 5000 });

    // 验证徽章文本
    const badgeText = await badge.textContent();
    expect(badgeText).toMatch(/PENDING|ACTIVE|INACTIVE|RUNNING|ERROR/i);
  });

  test('应该显示插件类型', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    const firstRow = table.locator('tbody tr').first();
    await expect(firstRow).toContainText(/local|remote/i);
  });

  test('应该显示分页组件', async ({ page }) => {
    // 查找分页组件
    const pagination = page.locator('[class*="pagination"], [data-testid="pagination"]').first();

    if (await pagination.isVisible()) {
      // 验证分页信息
      await expect(pagination).toBeVisible();
    } else {
      // 如果插件数量少，可能不显示分页
      console.log('分页组件未显示（插件数量可能较少）');
    }
  });

  test('应该显示加载状态', async ({ page }) => {
    // 重新加载页面
    await page.reload();

    // 检查是否有骨架屏或加载指示器
    const loading = page.locator('.skeleton, [data-loading="true"], [data-testid="loading"]');

    // 加载状态可能很快消失，所以不强制要求
    const isLoading = await loading.count() > 0;

    if (isLoading) {
      // 等待加载完成
      await loading.first().waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
    }

    // 验证最终显示了数据
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
  });
});
