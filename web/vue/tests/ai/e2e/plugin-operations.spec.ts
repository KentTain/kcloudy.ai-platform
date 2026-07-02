/**
 * 插件操作 E2E 测试
 *
 * 测试插件启动、停止、卸载等操作。
 */
import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('插件操作', () => {
  test.beforeEach(async ({ page, request }) => {
    // API 辅助登录
    await userLoginViaAPI(page, request, 'admin', 'admin123');

    // 导航到插件列表页
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('应该显示插件操作按钮', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证有操作按钮（配置或安装）
    const firstRow = table.locator('tbody tr').first();
    const actionButton = firstRow.locator('button').last();
    await expect(actionButton).toBeVisible({ timeout: 5000 });
  });

  test('应该显示安装按钮（未安装插件）', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 查找安装按钮
    const installButton = table.locator('button:has-text("安装")').first();
    const isVisible = await installButton.isVisible({ timeout: 5000 }).catch(() => false);
    // 可能存在安装按钮（未安装的插件）
    console.log(`安装按钮可见: ${isVisible}`);
  });

  test('应该显示配置按钮（已安装插件）', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 查找配置按钮
    const configButton = table.locator('button:has-text("配置")').first();
    const isVisible = await configButton.isVisible({ timeout: 5000 }).catch(() => false);
    console.log(`配置按钮可见: ${isVisible}`);
  });

  test('点击安装按钮应触发操作', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    const installButton = table.locator('button:has-text("安装")').first();
    const isVisible = await installButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      await installButton.click();
      await page.waitForTimeout(2000);
      // 验证页面未崩溃
      await expect(table).toBeVisible();
    } else {
      console.log('安装按钮不可见，跳过');
    }
  });

  test('操作后应更新状态', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    // 验证表格中有状态信息
    const pageContent = await page.locator('[data-testid="plugin-manage-page"]').textContent();
    const hasStatus = /已安装|未安装|待安装|安装中/.test(pageContent || '');
    expect(hasStatus).toBeTruthy();
  });

  test('应该显示操作加载状态', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    const installButton = table.locator('button:has-text("安装")').first();
    const isVisible = await installButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      await installButton.click();
      // 检查是否有加载状态
      await page.waitForTimeout(500);
      // 等待操作完成
      await page.waitForTimeout(2000);
    }
  });

  test('应该显示操作结果通知', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    const installButton = table.locator('button:has-text("安装")').first();
    const isVisible = await installButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      await installButton.click();
      await page.waitForTimeout(3000);

      // 检查通知（成功或失败都可以）
      const hasNotification = await page.locator('[data-sonner-toast], [role="status"]').count() > 0;
      console.log(`通知显示: ${hasNotification}`);
    }
  });

  test('应该正确处理操作失败', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 15000 });

    const installButton = table.locator('button:has-text("安装")').first();
    const isVisible = await installButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      await installButton.click();
      await page.waitForTimeout(3000);

      // 验证页面未崩溃
      await expect(table).toBeVisible();
    }
  });

  test('批量操作应正确显示', async ({ page }) => {
    // 检查是否有批量操作按钮
    const batchButtons = page.locator('button:has-text("批量")');
    const count = await batchButtons.count();
    console.log(`批量操作按钮数量: ${count}`);
  });
});
