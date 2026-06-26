/**
 * Tenant E2E 测试 Fixtures
 *
 * 提供两种登录方式：
 * 1. API 辅助登录：快速测试其他功能，绕过 UI
 * 2. UI 登录：测试登录页面的 UI 交互
 *
 * 性能优化：
 * - 使用 addInitScript 替代 page.goto + page.evaluate，避免重复加载 SPA
 * - 使用缓存机制避免跨测试重复登录 API 调用
 */
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';

// ============================================================================
// Token 存储常量（与前端源码保持一致）
// ============================================================================

// Tenant 管理端常量（src/tenant/stores/adminAuth.ts:10-14）
const ADMIN_TOKEN_KEY = "admin_token";
const ADMIN_INFO_KEY = "admin_info";
const ADMIN_ROLE_KEY = "admin_role";
const ADMIN_PERMISSIONS_KEY = "admin_permissions";
const ADMIN_MENUS_KEY = "admin_menus";

// IAM 用户端常量（src/iam/stores/auth.ts:99-107）
const TOKEN_KEY = "token";
const TENANT_ID_KEY = "tenant_id";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRES_AT_KEY = "token_expires_at";

// 导出常量供测试使用
export {
  ADMIN_TOKEN_KEY,
  ADMIN_INFO_KEY,
  ADMIN_ROLE_KEY,
  ADMIN_PERMISSIONS_KEY,
  ADMIN_MENUS_KEY,
  TOKEN_KEY,
  TENANT_ID_KEY,
  REFRESH_TOKEN_KEY,
  TOKEN_EXPIRES_AT_KEY
};

// ============================================================================
// Token 缓存（同一测试文件内复用，减少 API 调用）
// ============================================================================

let cachedToken: string | null = null;
let cachedAdminInfo: any = null;

/**
 * 获取管理员 Token（带缓存）
 */
async function obtainAdminToken(
  request: APIRequestContext,
  username = 'tenant_admin',
  password = 'admin123'
): Promise<{ token: string; adminInfo: any }> {
  if (cachedToken && cachedAdminInfo) {
    return { token: cachedToken, adminInfo: cachedAdminInfo };
  }

  const loginResponse = await request.post('/api/tenant/admin/v1/auth/login', {
    data: { username, password }
  });

  if (!loginResponse.ok()) {
    const errorText = await loginResponse.text();
    throw new Error(
      `管理员登录失败 (HTTP ${loginResponse.status()}): ${errorText}`
    );
  }

  const loginData = await loginResponse.json();
  const token = loginData?.data?.token;

  if (!token) {
    throw new Error(
      `管理员登录失败: 响应中未找到 token 字段 (响应: ${JSON.stringify(loginData)})`
    );
  }

  const meResponse = await request.get('/api/tenant/admin/v1/admin/me', {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!meResponse.ok()) {
    const errorText = await meResponse.text();
    throw new Error(
      `获取管理员信息失败 (HTTP ${meResponse.status()}): ${errorText}`
    );
  }

  const adminData = await meResponse.json();
  const adminInfo = adminData?.data;

  if (!adminInfo) {
    throw new Error(
      `获取管理员信息失败: 响应中未找到 data 字段 (响应: ${JSON.stringify(adminData)})`
    );
  }

  cachedToken = token;
  cachedAdminInfo = adminInfo;
  return { token, adminInfo };
}

/**
 * 清除缓存的 Token（测试文件间重置）
 */
export function clearAdminTokenCache() {
  cachedToken = null;
  cachedAdminInfo = null;
}

// ============================================================================
// API 辅助登录函数
// ============================================================================

/**
 * 管理员 API 辅助登录
 *
 * 通过 API 调用完成管理员认证，绕过 UI 登录流程，将 Token 直接注入浏览器存储。
 * 使用 addInitScript 在页面加载前注入 localStorage。
 *
 * @param page Playwright Page 对象
 * @param request Playwright APIRequestContext 对象
 * @param username 用户名，默认 'tenant_admin'
 * @param password 密码，默认 'admin123'
 * @throws 登录失败时抛出包含 HTTP 状态码和错误消息的异常
 */
export async function adminLoginViaAPI(
  page: Page,
  request: APIRequestContext,
  username = 'tenant_admin',
  password = 'admin123'
) {
  // 1. 获取 Token 和管理员信息（带缓存）
  const { token, adminInfo } = await obtainAdminToken(request, username, password);

  // 2. 使用 addInitScript 在页面加载前注入 localStorage
  //    注意：addInitScript 需要在 page.goto() 之前调用，脚本会在每次导航时执行
  await page.addInitScript(
    ({ token, adminInfo, ADMIN_TOKEN_KEY, ADMIN_INFO_KEY, ADMIN_ROLE_KEY, ADMIN_PERMISSIONS_KEY, ADMIN_MENUS_KEY }) => {
      localStorage.setItem(ADMIN_TOKEN_KEY, token);
      localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(adminInfo));
      localStorage.setItem(ADMIN_ROLE_KEY, adminInfo.role || '');
      localStorage.setItem(ADMIN_PERMISSIONS_KEY, JSON.stringify(adminInfo.permissions || []));
      localStorage.setItem(ADMIN_MENUS_KEY, JSON.stringify(adminInfo.menus || []));
    },
    {
      token,
      adminInfo,
      ADMIN_TOKEN_KEY,
      ADMIN_INFO_KEY,
      ADMIN_ROLE_KEY,
      ADMIN_PERMISSIONS_KEY,
      ADMIN_MENUS_KEY
    }
  );
}

/**
 * IAM 用户端 API 辅助登录
 *
 * 通过 API 调用完成 IAM 用户认证，支持 X-Tenant-Id 请求头注入。
 *
 * 存储到 localStorage 的字段（与 src/iam/stores/auth.ts 保持一致）：
 * - token: access_token
 * - tenant_id: 租户 ID
 * - refresh_token: 刷新令牌
 * - token_expires_at: Token 过期时间
 *
 * @param page Playwright Page 对象
 * @param request Playwright APIRequestContext 对象
 * @param account 账号，默认 'admin'
 * @param password 密码，默认 'admin123'
 * @throws 登录失败时抛出包含 HTTP 状态码和错误消息的异常
 */
export async function userLoginViaAPI(
  page: Page,
  request: APIRequestContext,
  account = 'admin',
  password = 'admin123'
) {
  // 1. 调用登录 API
  const loginResponse = await request.post('/api/iam/console/v1/auth/login', {
    data: { account, password }
  });

  if (!loginResponse.ok()) {
    const errorText = await loginResponse.text();
    throw new Error(
      `用户登录失败 (HTTP ${loginResponse.status()}): ${errorText}`
    );
  }

  const loginData = await loginResponse.json();
  const access_token = loginData?.data?.access_token;
  const refresh_token = loginData?.data?.refresh_token;
  const tenant_id = loginData?.data?.tenant_id;
  const expires_in = loginData?.data?.expires_in || 3600;

  if (!access_token) {
    throw new Error(
      `用户登录失败: 响应中未找到 access_token 字段 (响应: ${JSON.stringify(loginData)})`
    );
  }

  // 2. 使用 addInitScript 在页面加载前注入 localStorage
  // 计算过期时间
  const expires_at = Date.now() + expires_in * 1000;

  await page.addInitScript(
    ({ access_token, refresh_token, tenant_id, expires_at, TOKEN_KEY, TENANT_ID_KEY, REFRESH_TOKEN_KEY, TOKEN_EXPIRES_AT_KEY }) => {
      localStorage.setItem(TOKEN_KEY, access_token);
      if (refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
      }
      localStorage.setItem(TOKEN_EXPIRES_AT_KEY, String(expires_at));
      if (tenant_id) {
        localStorage.setItem(TENANT_ID_KEY, tenant_id);
      }
    },
    {
      access_token,
      refresh_token,
      tenant_id,
      expires_at,
      TOKEN_KEY,
      TENANT_ID_KEY,
      REFRESH_TOKEN_KEY,
      TOKEN_EXPIRES_AT_KEY
    }
  );

  // 注意：用户信息不存储到 localStorage（与 IAM auth store 实现一致）
  // 如果页面需要用户信息，会在加载时通过 /me API 获取
}

// ============================================================================
// UI 登录辅助函数（保留以兼容现有测试）
// ============================================================================

/**
 * 管理员 UI 登录辅助函数
 */
export async function adminLogin(page: Page, username = 'tenant_admin', password = 'admin123') {
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
  // 额外等待 300ms 确保渲染稳定
  await page.waitForTimeout(300);
}

export { test, expect };
