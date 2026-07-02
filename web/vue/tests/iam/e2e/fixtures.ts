/**
 * IAM 模块 E2E 测试 Fixtures
 *
 * 为 IAM 用户端页面测试提供登录和页面辅助函数。
 *
 * IAM 用户端使用以下 Token 存储方式（src/iam/stores/auth.ts:99-107）：
 * - token（而非 admin_token）
 * - tenant_id（需要 X-Tenant-Id header）
 *
 * 管理员 Token 通过 tenant 模块的 adminLoginViaAPI 获取，
 * IAM 用户 Token 通过 userLoginViaAPI 获取。
 */
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { userLoginViaAPI } from '../../tenant/e2e/fixtures';

// 重新导出 Playwright 基础工具
export { test, expect };

// ============================================================================
// IAM 用户端登录
// ============================================================================

/**
 * IAM 用户端 API 辅助登录
 *
 * 复用 tenant fixtures 中的 userLoginViaAPI 实现，
 * 通过 API 调用完成 IAM 用户认证，将 Token 注入浏览器存储。
 *
 * 存储到 localStorage 的字段（与 src/iam/stores/auth.ts 保持一致）：
 * - token: access_token
 * - tenant_id: 租户 ID
 *
 * @param page Playwright Page 对象
 * @param request Playwright APIRequestContext 对象
 * @param account 账号，默认 'admin'
 * @param password 密码，默认 'admin123'
 */
export { userLoginViaAPI as iamUserLogin, userLoginViaAPI };

// ============================================================================
// Token 获取辅助函数
// ============================================================================

/**
 * 获取 IAM 用户 Token 和租户 ID
 *
 * 通过 API 调用完成 IAM 用户认证，返回 Token 和租户 ID，
 * 供 data-helpers 中需要手动构造请求时使用。
 *
 * @param request Playwright APIRequestContext
 * @param account 账号，默认 'admin'
 * @param password 密码，默认 'admin123'
 * @returns { accessToken, tenantId } Token 和租户 ID
 */
export async function getIamUserToken(
  request: APIRequestContext,
  account = 'admin',
  password = 'admin123'
): Promise<{ accessToken: string; tenantId: string | null }> {
  const loginResponse = await request.post('/api/iam/console/v1/auth/login', {
    data: { account, password }
  });

  if (!loginResponse.ok()) {
    const errorText = await loginResponse.text();
    throw new Error(
      `IAM 用户登录失败 (HTTP ${loginResponse.status()}): ${errorText}`
    );
  }

  const loginData = await loginResponse.json();
  const access_token = loginData?.data?.access_token;
  const tenant_id = loginData?.data?.tenant_id || null;

  if (!access_token) {
    throw new Error(
      `IAM 用户登录失败: 响应中未找到 access_token 字段 (响应: ${JSON.stringify(loginData)})`
    );
  }

  return { accessToken: access_token, tenantId: tenant_id };
}

// ============================================================================
// 页面辅助函数
// ============================================================================

/**
 * 等待骨架屏消失
 *
 * @param page Playwright Page 对象
 * @param timeout 超时时间（毫秒），默认 10000ms
 */
export async function waitForSkeletonGone(page: Page, timeout = 10000) {
  try {
    await page.waitForSelector('[data-skeleton="true"]', { state: 'hidden', timeout });
    await page.waitForSelector('.skeleton', { state: 'hidden', timeout });
    await page.waitForSelector('[data-loading="true"]', { state: 'hidden', timeout });
  } catch {
    // 骨架屏可能已经不存在，忽略错误
  }
}

/**
 * 验证页面有可见内容
 *
 * @param page Playwright Page 对象
 */
export async function verifyPageHasContent(page: Page) {
  // 等待页面主要内容区域可见
  const contentArea = page.locator('main, [role="main"], .main-content, [data-testid="main-content"]').first();
  const hasMainContent = await contentArea.count() > 0;

  if (hasMainContent) {
    await expect(contentArea).toBeVisible();
  }

  // 验证页面至少有一些可见的文本内容
  const bodyText = await page.locator('body').textContent();
  expect(bodyText?.trim().length).toBeGreaterThan(0);
}

/**
 * 捕获控制台错误
 *
 * @param page Playwright Page 对象
 * @returns 错误消息数组
 */
export function captureConsoleErrors(page: Page): string[] {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('pageerror', (error) => {
    errors.push(error.message);
  });

  return errors;
}

/**
 * 等待页面加载完成
 *
 * @param page Playwright Page 对象
 */
export async function waitForPageReady(page: Page) {
  await page.waitForLoadState('networkidle');
  await waitForSkeletonGone(page);
}
