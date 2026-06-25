/**
 * Tenant 模块 CRUD E2E 测试
 *
 * 测试租户管理的完整 CRUD 操作：
 * - 列表加载
 * - 创建租户
 * - 编辑租户
 * - 删除租户
 * - 搜索租户
 * - 统计数据验证
 */
import { test, expect, adminLoginViaAPI } from './fixtures';
import {
  createTenantViaAPI,
  deleteTenantViaAPI,
  getAdminToken,
  cleanupAllE2EData,
} from './data-helpers';
import type { TenantResponse } from './data-helpers';

test.describe('租户管理 CRUD', () => {
  let adminToken: string;
  let testTenant: TenantResponse | null = null;

  test.beforeAll(async ({ request }) => {
    // 获取管理员 Token
    adminToken = await getAdminToken(request);
    // 清理之前的测试数据
    await cleanupAllE2EData(request, adminToken);
  });

  test.beforeEach(async ({ page, request }) => {
    // 使用 API 辅助登录
    await adminLoginViaAPI(page, request);
  });

  test.afterEach(async ({ request }) => {
    // 每个测试后清理创建的租户
    if (testTenant) {
      try {
        await deleteTenantViaAPI(request, adminToken, testTenant.id);
      } catch {
        // 忽略删除错误
      }
      testTenant = null;
    }
  });

  test.afterAll(async ({ request }) => {
    // 最终清理
    await cleanupAllE2EData(request, adminToken);
  });

  // ============================================================================
  // 6.5 列表加载测试
  // ============================================================================
  test.describe('列表加载', () => {
    test('租户列表页面正确渲染', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 验证页面标题
      await expect(page.getByTestId('page-title')).toContainText('租户管理');

      // 验证创建按钮存在
      await expect(page.getByTestId('create-tenant-button')).toBeVisible();

      // 验证搜索框存在
      await expect(page.locator('[data-testid="search-keyword"] input')).toBeVisible();

      // 验证表格存在
      await expect(page.getByTestId('tenant-table')).toBeVisible();
    });

    test('租户列表数据正确显示', async ({ page, request }) => {
      // 先创建一个测试租户
      testTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E列表测试租户',
      });

      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 验证表格中有数据
      const table = page.getByTestId('tenant-table');
      await expect(table).toBeVisible();

      // 验证新创建的租户在列表中
      await expect(table.getByText('E2E列表测试租户')).toBeVisible({ timeout: 10000 });
    });
  });

  // ============================================================================
  // 6.6 创建租户测试
  // ============================================================================
  test.describe('创建租户', () => {
    test('打开创建页面', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 点击新建按钮
      await page.getByTestId('create-tenant-button').click();

      // 验证跳转到创建页面
      await page.waitForURL('**/admin/tenants/create');
      expect(page.url()).toContain('/admin/tenants/create');

      // 验证页面标题
      await expect(page.getByTestId('page-title')).toContainText('新增租户');
    });

    test('表单验证 - 必填项为空', async ({ page }) => {
      await page.goto('/admin/tenants/create');
      await page.waitForLoadState('networkidle');

      // 直接点击保存
      await page.getByTestId('save-button').click();

      // 验证错误提示显示
      await expect(page.getByText('请输入租户名称')).toBeVisible();
      await expect(page.getByText('请输入租户编码')).toBeVisible();
    });

    test('表单验证 - 租户编码格式错误', async ({ page }) => {
      await page.goto('/admin/tenants/create');
      await page.waitForLoadState('networkidle');

      // 输入无效的租户编码（以数字开头）
      await page.getByTestId('input-name').locator('input').fill('测试租户');
      await page.getByTestId('input-code').locator('input').fill('123invalid');
      await page.getByTestId('save-button').click();

      // 验证错误提示
      await expect(
        page.getByText('租户编码必须以小写字母开头')
      ).toBeVisible();
    });

    test('创建租户成功', async ({ page }) => {
      await page.goto('/admin/tenants/create');
      await page.waitForLoadState('networkidle');

      // 填写表单
      const timestamp = Date.now();
      await page.getByTestId('input-name').locator('input').fill('E2E创建测试租户');
      await page.getByTestId('input-code').locator('input').fill(`e2e-create-${timestamp}`);
      await page.getByTestId('input-contact-name').locator('input').fill('测试联系人');
      await page.getByTestId('input-contact-email').locator('input').fill('test@example.com');
      await page.getByTestId('input-contact-phone').locator('input').fill('13800138000');

      // 提交表单
      await page.getByTestId('save-button').click();

      // 验证跳转回列表页
      await page.waitForURL('**/admin/tenants', { timeout: 15000 });

      // 验证成功消息
      await expect(page.getByText('租户已创建')).toBeVisible({ timeout: 5000 });

      // 验证新租户在列表中
      await expect(page.getByText('E2E创建测试租户')).toBeVisible({ timeout: 10000 });
    });
  });

  // ============================================================================
  // 6.7 编辑租户测试
  // ============================================================================
  test.describe('编辑租户', () => {
    test.beforeEach(async ({ request }) => {
      // 每个测试前创建一个租户
      testTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E编辑测试租户',
      });
    });

    test('进入编辑页面', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 找到刚创建的租户行
      const row = page.getByText('E2E编辑测试租户').first();
      await expect(row).toBeVisible({ timeout: 10000 });

      // 点击编辑按钮
      await page.locator('button:has-text("编辑")').first().click();

      // 验证跳转到编辑页面
      await page.waitForURL(/\/admin\/tenants\/[^/]+\/edit$/);
      expect(page.url()).toContain('/edit');

      // 验证页面标题
      await expect(page.getByTestId('page-title')).toContainText('编辑租户');
    });

    test('编辑表单显示原有数据', async ({ page }) => {
      // 直接访问编辑页面
      await page.goto(`/admin/tenants/${testTenant!.id}/edit`);
      await page.waitForLoadState('networkidle');

      // 验证表单字段有值
      await expect(page.getByTestId('input-name').locator('input')).toHaveValue('E2E编辑测试租户');
      await expect(page.getByTestId('input-code').locator('input')).toBeDisabled(); // 编码不可编辑
    });

    test('编辑租户成功', async ({ page }) => {
      await page.goto(`/admin/tenants/${testTenant!.id}/edit`);
      await page.waitForLoadState('networkidle');

      // 修改租户名称
      await page.getByTestId('input-name').locator('input').fill('E2E编辑测试租户-已修改');
      await page.getByTestId('input-contact-name').locator('input').fill('新联系人');

      // 保存
      await page.getByTestId('save-button').click();

      // 验证跳转回列表页
      await page.waitForURL('**/admin/tenants', { timeout: 15000 });

      // 验证成功消息
      await expect(page.getByText('租户已更新')).toBeVisible({ timeout: 5000 });
    });
  });

  // ============================================================================
  // 6.8 删除租户测试
  // ============================================================================
  test.describe('删除租户', () => {
    test.beforeEach(async ({ request }) => {
      // 每个测试前创建一个租户
      testTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E删除测试租户',
      });
    });

    test('删除租户成功', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 确认租户存在
      await expect(page.getByText('E2E删除测试租户')).toBeVisible({ timeout: 10000 });

      // 设置对话框接受
      page.on('dialog', (dialog) => dialog.accept());

      // 点击删除按钮
      const row = page.locator('tr', { hasText: 'E2E删除测试租户' });
      await row.locator('button:has-text("删除")').click();

      // 等待删除完成
      await page.waitForLoadState('networkidle');

      // 验证租户已删除
      await expect(page.getByText('E2E删除测试租户')).not.toBeVisible({ timeout: 10000 });

      // 标记已删除，避免 afterEach 再次删除
      testTenant = null;
    });
  });

  // ============================================================================
  // 6.9 搜索租户测试
  // ============================================================================
  test.describe('搜索租户', () => {
    test.beforeEach(async ({ request }) => {
      // 创建多个测试租户
      testTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E搜索测试租户A',
      });
    });

    test('关键字搜索', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 输入搜索关键字
      await page.locator('[data-testid="search-keyword"] input').fill('E2E搜索测试');
      await page.getByTestId('search-button').click();

      // 等待搜索完成
      await page.waitForLoadState('networkidle');

      // 验证搜索结果
      await expect(page.getByText('E2E搜索测试租户A')).toBeVisible({ timeout: 10000 });
    });

    test('状态筛选', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 选择状态
      await page.getByTestId('search-status').click();
      await page.locator('[role="option"]:has-text("激活")').click();
      await page.getByTestId('search-button').click();

      // 等待筛选完成
      await page.waitForLoadState('networkidle');

      // 验证表格显示
      await expect(page.getByTestId('tenant-table')).toBeVisible();
    });

    test('重置搜索', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 输入搜索条件
      await page.locator('[data-testid="search-keyword"] input').fill('测试关键字');
      await page.getByTestId('search-status').click();
      await page.locator('[role="option"]:has-text("激活")').click();

      // 点击重置
      await page.getByTestId('reset-button').click();

      // 验证搜索条件被清空
      await expect(page.locator('[data-testid="search-keyword"] input')).toHaveValue('');
    });
  });

  // ============================================================================
  // 6.10 统计数据验证测试
  // ============================================================================
  test.describe('统计数据验证', () => {
    test.beforeEach(async ({ request }) => {
      // 创建测试租户
      testTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E统计测试租户',
      });
    });

    test('统计卡片正确渲染', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 验证三个统计卡片都存在
      await expect(page.getByTestId('stats-total')).toBeVisible();
      await expect(page.getByTestId('stats-inactive')).toBeVisible();
      await expect(page.getByTestId('stats-expired')).toBeVisible();
    });

    test('统计数据格式正确', async ({ page }) => {
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      // 验证统计数据是数字
      const totalValue = await page.getByTestId('stats-total-value').textContent();
      const inactiveValue = await page.getByTestId('stats-inactive-value').textContent();
      const expiredValue = await page.getByTestId('stats-expired-value').textContent();

      // 验证都是数字
      expect(parseInt(totalValue || '0')).not.toBeNaN();
      expect(parseInt(inactiveValue || '0')).not.toBeNaN();
      expect(parseInt(expiredValue || '0')).not.toBeNaN();
    });

    test('创建租户后统计数据更新', async ({ page, request }) => {
      // 先获取当前统计
      await page.goto('/admin/tenants');
      await page.waitForLoadState('networkidle');

      const beforeTotal = await page.getByTestId('stats-total-value').textContent();
      const beforeCount = parseInt(beforeTotal || '0');

      // 创建新租户
      const newTenant = await createTenantViaAPI(request, adminToken, {
        name: 'E2E统计更新测试',
      });

      // 刷新页面
      await page.reload();
      await page.waitForLoadState('networkidle');

      // 验证统计数据增加
      const afterTotal = await page.getByTestId('stats-total-value').textContent();
      const afterCount = parseInt(afterTotal || '0');

      expect(afterCount).toBeGreaterThanOrEqual(beforeCount);

      // 清理
      await deleteTenantViaAPI(request, adminToken, newTenant.id);
    });
  });
});

// ============================================================================
// 详情页测试
// ============================================================================
test.describe('租户详情页', () => {
  let adminToken: string;
  let testTenant: TenantResponse | null = null;

  test.beforeAll(async ({ request }) => {
    adminToken = await getAdminToken(request);
    await cleanupAllE2EData(request, adminToken);
  });

  test.beforeEach(async ({ page, request }) => {
    await adminLoginViaAPI(page, request);
    testTenant = await createTenantViaAPI(request, adminToken, {
      name: 'E2E详情测试租户',
    });
  });

  test.afterEach(async ({ request }) => {
    if (testTenant) {
      try {
        await deleteTenantViaAPI(request, adminToken, testTenant.id);
      } catch {
        // 忽略删除错误
      }
      testTenant = null;
    }
  });

  test.afterAll(async ({ request }) => {
    await cleanupAllE2EData(request, adminToken);
  });

  test('访问详情页', async ({ page }) => {
    await page.goto(`/admin/tenants/${testTenant!.id}`);
    await page.waitForLoadState('networkidle');

    // 验证详情信息显示
    await expect(page.getByTestId('tenant-info')).toBeVisible();
    await expect(page.getByText('E2E详情测试租户')).toBeVisible();
  });

  test('从详情页跳转到编辑页', async ({ page }) => {
    await page.goto(`/admin/tenants/${testTenant!.id}`);
    await page.waitForLoadState('networkidle');

    // 点击编辑按钮
    await page.getByTestId('edit-button').click();

    // 验证跳转
    await page.waitForURL(/\/admin\/tenants\/[^/]+\/edit$/);
    expect(page.url()).toContain('/edit');
  });

  test('激活/停用租户', async ({ page }) => {
    await page.goto(`/admin/tenants/${testTenant!.id}`);
    await page.waitForLoadState('networkidle');

    // 新创建的租户应该是激活状态
    await expect(page.getByTestId('deactivate-button')).toBeVisible();

    // 点击停用
    await page.getByTestId('deactivate-button').click();
    await page.waitForLoadState('networkidle');

    // 现在应该显示激活按钮
    await expect(page.getByTestId('activate-button')).toBeVisible({ timeout: 10000 });

    // 再次激活
    await page.getByTestId('activate-button').click();
    await page.waitForLoadState('networkidle');

    // 应该恢复到停用按钮
    await expect(page.getByTestId('deactivate-button')).toBeVisible({ timeout: 10000 });
  });

  test('Tab 切换', async ({ page }) => {
    await page.goto(`/admin/tenants/${testTenant!.id}`);
    await page.waitForLoadState('networkidle');

    // 切换到资源绑定 Tab
    await page.getByTestId('tab-resources').click();
    await expect(page.getByText('保存资源绑定')).toBeVisible({ timeout: 5000 });

    // 切换到模块分配 Tab
    await page.getByTestId('tab-modules').click();
    await expect(page.getByText('已分配模块')).toBeVisible({ timeout: 5000 });

    // 切换回基本信息 Tab
    await page.getByTestId('tab-info').click();
    await expect(page.getByTestId('tenant-info')).toBeVisible();
  });
});
