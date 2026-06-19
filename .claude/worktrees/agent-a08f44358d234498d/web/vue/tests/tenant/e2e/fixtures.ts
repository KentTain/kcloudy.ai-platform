/**
 * Tenant E2E 测试 Fixtures
 */
import { test, expect, type Page } from '@playwright/test';

/**
 * 管理员登录辅助函数
 */
export async function adminLogin(page: Page, username = 'admin', password = 'admin123') {
  await page.goto('/admin/login');
  await page.waitForLoadState('networkidle');

  // 检查是否已登录
  const currentUrl = page.url();
  if (!currentUrl.includes('/login')) {
    return;
  }

  // 填写登录表单
  const usernameInput = page.locator('input[type="text"], input[name="username"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  const loginButton = page.locator('button[type="submit"]');

  if (await usernameInput.isVisible()) {
    await usernameInput.fill(username);
    await passwordInput.fill(password);
    await loginButton.click();

    // 等待登录完成并跳转
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });
  }
}

/**
 * 等待页面加载完成
 */
export async function waitForPageReady(page: Page) {
  await page.waitForLoadState('networkidle');
  // 等待骨架屏消失
  await page.waitForSelector('.skeleton, [data-loading="true"]', { state: 'hidden', timeout: 10000 }).catch(() => {});
}

export { test, expect };
