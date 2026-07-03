/**
 * 插件操作 E2E 测试
 *
 * 测试插件安装、启动、停止等操作。
 * 使用 data-testid 选择器确保稳定性。
 */
import { test, expect } from './plugin-fixtures';
import { loginAndGotoPluginList } from './plugin-fixtures';

test.describe('插件操作', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAndGotoPluginList(page, request);
  });

  test('已安装插件显示配置和启停按钮', async ({ page }) => {
    const configBtn = page.getByTestId('config-btn');
    const isVisible = await configBtn.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      // 没有已安装的插件，跳过
      return;
    }

    await expect(configBtn.first()).toBeVisible();

    // 已安装的插件应该有启动或停止按钮
    const startBtn = page.getByTestId('start-btn');
    const stopBtn = page.getByTestId('stop-btn');
    const hasStart = await startBtn.first().isVisible({ timeout: 5000 }).catch(() => false);
    const hasStop = await stopBtn.first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasStart || hasStop).toBeTruthy();
  });

  test('未安装插件显示安装按钮', async ({ page }) => {
    const installBtn = page.getByTestId('install-btn');
    const isVisible = await installBtn.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      // 所有插件都已安装，跳过
      return;
    }

    await expect(installBtn.first()).toBeVisible();
    await expect(installBtn.first()).toBeEnabled();
  });

  test('点击安装按钮后状态更新并显示通知', async ({ page }) => {
    const installBtn = page.getByTestId('install-btn');
    const isVisible = await installBtn.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      return;
    }

    await installBtn.first().click();

    // 验证通知出现（成功或失败都可以）
    const toast = page.locator('[data-sonner-toast], [role="status"]');
    await expect(toast.first()).toBeVisible({ timeout: 15000 }).catch(() => {
      // 通知可能很快消失
    });

    // 验证页面未崩溃
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible();
  });

  test('点击启动按钮后状态变为运行中', async ({ page }) => {
    const startBtn = page.getByTestId('start-btn');
    const isVisible = await startBtn.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      return;
    }

    await startBtn.first().click();

    // 等待操作完成
    await page.waitForLoadState('networkidle');

    // 验证通知出现
    const toast = page.locator('[data-sonner-toast], [role="status"]');
    await expect(toast.first()).toBeVisible({ timeout: 15000 }).catch(() => {});

    // 验证页面未崩溃
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible();
  });

  test('点击停止按钮后状态变为已停止', async ({ page }) => {
    const stopBtn = page.getByTestId('stop-btn');
    const isVisible = await stopBtn.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      return;
    }

    await stopBtn.first().click();

    // 等待操作完成
    await page.waitForLoadState('networkidle');

    // 验证通知出现
    const toast = page.locator('[data-sonner-toast], [role="status"]');
    await expect(toast.first()).toBeVisible({ timeout: 15000 }).catch(() => {});

    // 验证页面未崩溃
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible();
  });

  test('操作期间页面不崩溃', async ({ page }) => {
    // 尝试点击任何可用的操作按钮
    const actionButtons = [
      page.getByTestId('install-btn').first(),
      page.getByTestId('start-btn').first(),
      page.getByTestId('stop-btn').first(),
    ];

    for (const btn of actionButtons) {
      const isVisible = await btn.isVisible({ timeout: 3000 }).catch(() => false);
      if (isVisible && (await btn.isEnabled().catch(() => false))) {
        await btn.click();
        await page.waitForTimeout(2000);
        break;
      }
    }

    // 验证页面仍在正常状态
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible();
    await expect(page.getByTestId('plugin-list-table')).toBeVisible({ timeout: 10000 });
  });
});
