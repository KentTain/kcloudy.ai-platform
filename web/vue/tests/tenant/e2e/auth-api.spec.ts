/**
 * API 辅助登录功能验证测试
 *
 * 注意：运行此测试需要后端服务正常运行
 * 运行方式：pnpm test:e2e tests/tenant/e2e/auth-api.spec.ts
 */
import { test, expect, adminLoginViaAPI, userLoginViaAPI } from './fixtures';

test.describe('API 辅助登录功能', () => {
  test.describe('管理员 API 登录', () => {
    test('使用正确的凭据登录成功', async ({ page, request }) => {
      // 调用 API 登录
      await adminLoginViaAPI(page, request, 'admin', 'admin123');

      // 验证 Token 已注入 localStorage
      const token = await page.evaluate(() => localStorage.getItem('admin_token'));
      expect(token).toBeTruthy();

      // 验证管理员信息已注入
      const adminInfo = await page.evaluate(() => localStorage.getItem('admin_info'));
      expect(adminInfo).toBeTruthy();
      const adminData = JSON.parse(adminInfo!);
      expect(adminData.username).toBe('admin');

      // 验证页面可以正常访问受保护资源
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 验证未跳转到登录页
      expect(page.url()).not.toContain('/login');
    });

    test('使用错误的凭据登录失败', async ({ page, request }) => {
      // 调用 API 登录（错误凭据）
      await expect(
        adminLoginViaAPI(page, request, 'wronguser', 'wrongpass')
      ).rejects.toThrow(/管理员登录失败/);
    });
  });

  test.describe('IAM 用户端 API 登录', () => {
    test('使用正确的凭据登录成功', async ({ page, request }) => {
      // 调用 API 登录
      await userLoginViaAPI(page, request, 'admin', 'admin123');

      // 验证 Token 已注入 localStorage
      const token = await page.evaluate(() => localStorage.getItem('token'));
      expect(token).toBeTruthy();

      // 验证 tenant_id 已注入
      const tenantId = await page.evaluate(() => localStorage.getItem('tenant_id'));
      expect(tenantId).toBeTruthy();

      // 验证页面可以正常访问受保护资源
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // 验证未跳转到登录页
      expect(page.url()).not.toContain('/login');
    });

    test('使用错误的凭据登录失败', async ({ page, request }) => {
      // 调用 API 登录（错误凭据）
      await expect(
        userLoginViaAPI(page, request, 'wronguser', 'wrongpass')
      ).rejects.toThrow(/用户登录失败/);
    });
  });
});
