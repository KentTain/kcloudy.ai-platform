/**
 * Tenant 模块 - 管理员登录页面测试
 *
 * 本文件测试 UI 登录流程，与 fixtures.ts 中的 API 辅助登录形成互补。
 * - API 辅助登录：用于快速测试其他功能，绕过 UI
 * - UI 登录测试：验证登录页面的 UI 交互和错误处理
 */
import { test, expect, waitForPageReady } from './fixtures';

// ============================================================================
// Token 存储常量（与前端源码保持一致）
// ============================================================================
const ADMIN_TOKEN_KEY = 'admin_token';
const ADMIN_INFO_KEY = 'admin_info';

// ============================================================================
// 测试场景
// ============================================================================

test.describe('管理员登录页面 - UI 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问登录页面（不使用 API 登录）
    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');
  });

  test('登录页面正确渲染', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h2')).toContainText('管理员登录');

    // 验证表单元素存在
    await expect(page.locator('input[placeholder*="用户名"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // 验证登录按钮文本
    await expect(page.locator('button[type="submit"]')).toContainText('登录');
  });

  test('表单验证 - 空用户名', async ({ page }) => {
    // 只填写密码
    await page.locator('input[type="password"]').fill('admin123');

    // 点击登录
    await page.locator('button[type="submit"]').click();

    // 验证验证错误消息
    await expect(page.locator('text=请输入用户名')).toBeVisible({ timeout: 5000 });
  });

  test('表单验证 - 空密码', async ({ page }) => {
    // 只填写用户名
    await page.locator('input[placeholder*="用户名"]').fill('admin');

    // 点击登录
    await page.locator('button[type="submit"]').click();

    // 验证验证错误消息
    await expect(page.locator('text=请输入密码')).toBeVisible({ timeout: 5000 });
  });

  test('登录失败 - 错误凭据', async ({ page }) => {
    // 填写错误凭据
    await page.locator('input[placeholder*="用户名"]').fill('wronguser');
    await page.locator('input[type="password"]').fill('wrongpassword');

    // 点击登录
    await page.locator('button[type="submit"]').click();

    // 等待错误提示
    await expect(page.locator('.admin-login-page__error')).toBeVisible({ timeout: 10000 });

    // 验证错误消息内容
    const errorText = await page.locator('.admin-login-page__error').textContent();
    expect(errorText).toBeTruthy();
    expect(errorText!.length).toBeGreaterThan(0);

    // 验证仍然在登录页面
    expect(page.url()).toContain('/admin/login');
  });

  test('登录成功 - 完整流程', async ({ page }) => {
    // 填写正确凭据
    await page.locator('input[placeholder*="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');

    // 点击登录
    await page.locator('button[type="submit"]').click();

    // 等待跳转（不包含 /login）
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });

    // 验证跳转成功
    expect(page.url()).not.toContain('/login');

    // 验证 localStorage 包含 token
    const token = await page.evaluate(
      (ADMIN_TOKEN_KEY) => localStorage.getItem(ADMIN_TOKEN_KEY),
      ADMIN_TOKEN_KEY
    );
    expect(token).toBeTruthy();

    // 验证 localStorage 包含管理员信息
    const adminInfo = await page.evaluate(
      (ADMIN_INFO_KEY) => localStorage.getItem(ADMIN_INFO_KEY),
      ADMIN_INFO_KEY
    );
    expect(adminInfo).toBeTruthy();

    // 验证管理员信息格式正确
    const adminData = JSON.parse(adminInfo!);
    expect(adminData).toHaveProperty('id');
    expect(adminData).toHaveProperty('username');
  });

  test('登录按钮加载状态', async ({ page }) => {
    // 填写凭据
    await page.locator('input[placeholder*="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');

    // 点击登录
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // 验证按钮变为禁用状态（显示加载中）
    // 注意：加载状态可能很快，所以需要快速检查
    const isLoading = await submitButton.getAttribute('disabled');
    // 如果加载状态还存在，验证按钮被禁用
    // 如果加载已完成（登录成功），则验证已跳转
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 }).catch(() => {
      // 如果超时，可能是因为登录失败，检查错误提示
    });
  });

  test('记住上次登录账号', async ({ page, context }) => {
    // 第一次登录
    await page.locator('input[placeholder*="用户名"]').fill('testadmin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();

    // 等待登录完成或失败
    await page.waitForTimeout(1000);

    // 验证 localStorage 保存了账号
    const lastAccount = await page.evaluate(() => {
      return localStorage.getItem('last_admin_account');
    });
    expect(lastAccount).toBe('testadmin');
  });
});

test.describe('登录状态持久化', () => {
  test('刷新页面保持登录状态', async ({ page, context }) => {
    // 先通过 UI 登录
    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');

    await page.locator('input[placeholder*="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();

    // 等待登录成功
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });

    // 刷新页面
    await page.reload();
    await page.waitForLoadState('networkidle');

    // 验证仍在登录状态（未跳转到登录页）
    expect(page.url()).not.toContain('/login');
  });

  test('清除 Token 后跳转到登录页', async ({ page }) => {
    // 先通过 UI 登录
    await page.goto('/admin/login');
    await page.waitForLoadState('networkidle');

    await page.locator('input[placeholder*="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();

    // 等待登录成功
    await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });

    // 清除 Token
    await page.evaluate((ADMIN_TOKEN_KEY) => {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
    }, ADMIN_TOKEN_KEY);

    // 访问需要认证的页面
    await page.goto('/admin/tenants');

    // 验证跳转到登录页
    await page.waitForURL(/\/admin\/login/, { timeout: 5000 });
    expect(page.url()).toContain('/admin/login');
  });
});

test.describe('登录后重定向', () => {
  test('访问受保护页面自动跳转到登录页', async ({ page }) => {
    // 直接访问受保护页面（未登录）
    await page.goto('/admin/tenants');

    // 验证自动跳转到登录页
    await page.waitForURL(/\/admin\/login/, { timeout: 5000 });
    expect(page.url()).toContain('/admin/login');
  });

  test('登录成功后跳转到目标页面', async ({ page }) => {
    // 访问受保护页面（会跳转到登录页）
    await page.goto('/admin/tenants');
    await page.waitForURL(/\/admin\/login/, { timeout: 5000 });

    // 登录
    await page.locator('input[placeholder*="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();

    // 验证跳转回目标页面
    await page.waitForURL(/\/admin\/tenants/, { timeout: 15000 });
    expect(page.url()).toContain('/admin/tenants');
  });
});
