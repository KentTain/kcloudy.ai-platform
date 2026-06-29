/**
 * AI 模块插件管理 E2E 测试 Fixtures
 *
 * 提供插件管理测试所需的登录、API 辅助函数和测试数据管理。
 */
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { userLoginViaAPI, getIamUserToken } from '../../iam/e2e/fixtures';

// 重新导出 Playwright 基础工具
export { test, expect };

// ============================================================================
// 插件测试辅助函数
// ============================================================================

/**
 * 获取插件列表
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @returns 插件列表
 */
export async function getPluginList(
  request: APIRequestContext,
  token: string,
  tenantId: string
) {
  const response = await request.get('/api/ai/console/v1/plugins', {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
  });

  if (!response.ok()) {
    throw new Error(`获取插件列表失败: ${response.status()}`);
  }

  return await response.json();
}

/**
 * 获取插件配置
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @param pluginId 插件 ID
 * @returns 插件配置
 */
export async function getPluginConfig(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  pluginId: string
) {
  const response = await request.get(
    `/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
    }
  );

  if (!response.ok()) {
    throw new Error(`获取插件配置失败: ${response.status()}`);
  }

  return await response.json();
}

/**
 * 更新插件配置
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @param pluginId 插件 ID
 * @param runtimeConfig 运行时配置
 * @returns 更新后的配置
 */
export async function updatePluginConfig(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  pluginId: string,
  runtimeConfig: Record<string, any>
) {
  const response = await request.patch(
    `/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
        'Content-Type': 'application/json',
      },
      data: { runtime_config: runtimeConfig },
    }
  );

  if (!response.ok()) {
    throw new Error(`更新插件配置失败: ${response.status()}`);
  }

  return await response.json();
}

/**
 * 获取插件运行时状态
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @param pluginId 插件 ID
 * @returns 运行时状态
 */
export async function getPluginRuntimeState(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  pluginId: string
) {
  const response = await request.get(
    `/api/ai/console/v1/plugins/installations/runtime-state?plugin_id=${encodeURIComponent(pluginId)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
    }
  );

  if (!response.ok()) {
    throw new Error(`获取运行时状态失败: ${response.status()}`);
  }

  return await response.json();
}

/**
 * 获取插件统计数据
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @returns 统计数据
 */
export async function getPluginStatistics(
  request: APIRequestContext,
  token: string,
  tenantId: string
) {
  const response = await request.get(
    '/api/ai/console/v1/plugins/installations/statistics',
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
    }
  );

  if (!response.ok()) {
    throw new Error(`获取统计数据失败: ${response.status()}`);
  }

  return await response.json();
}

/**
 * 启动插件
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @param pluginId 插件 ID
 * @returns 操作结果
 */
export async function startPlugin(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  pluginId: string
) {
  const response = await request.post(
    `/api/ai/console/v1/plugins/installations/start?plugin_id=${encodeURIComponent(pluginId)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
    }
  );

  return await response.json();
}

/**
 * 停止插件
 *
 * @param request Playwright APIRequestContext
 * @param token 访问令牌
 * @param tenantId 租户 ID
 * @param pluginId 插件 ID
 * @returns 操作结果
 */
export async function stopPlugin(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  pluginId: string
) {
  const response = await request.post(
    `/api/ai/console/v1/plugins/installations/stop?plugin_id=${encodeURIComponent(pluginId)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
    }
  );

  return await response.json();
}

// ============================================================================
// 页面辅助函数
// ============================================================================

/**
 * 等待插件列表加载完成
 */
export async function waitForPluginListReady(page: Page) {
  await page.waitForLoadState('networkidle');
  // 等待表格出现
  await page.waitForSelector('[data-testid="plugin-list-table"], table', { timeout: 10000 });
  // 等待骨架屏消失
  await page.waitForSelector('.skeleton, [data-loading="true"]', { state: 'hidden', timeout: 10000 }).catch(() => {});
  // 额外等待确保渲染完成
  await page.waitForTimeout(500);
}

/**
 * 等待插件配置页面加载完成
 */
export async function waitForPluginConfigReady(page: Page) {
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('[data-testid="plugin-config-page"]', { timeout: 10000 });
  await page.waitForSelector('.skeleton, [data-loading="true"]', { state: 'hidden', timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(500);
}

/**
 * 登录并导航到插件列表页
 */
export async function loginAndGotoPluginList(
  page: Page,
  request: APIRequestContext
) {
  await userLoginViaAPI(page, request);
  await page.goto('/ai/plugins');
  await waitForPluginListReady(page);
}

/**
 * 登录并导航到插件配置页
 */
export async function loginAndGotoPluginConfig(
  page: Page,
  request: APIRequestContext,
  pluginId: string
) {
  await userLoginViaAPI(page, request);
  await page.goto(`/ai/plugins/${encodeURIComponent(pluginId)}/config`);
  await waitForPluginConfigReady(page);
}
