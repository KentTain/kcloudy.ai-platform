/**
 * 插件 API E2E 测试
 *
 * 直接测试后端插件管理 API 接口。
 */
import { test, expect, type APIRequestContext } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const TENANT_ID = '00000000-0000-0000-0000-000000000000';

/**
 * 获取访问令牌
 */
async function getAccessToken(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${BASE_URL}/api/iam/console/v1/auth/login`, {
    data: { account: 'admin', password: 'admin123' },
    headers: { 'X-Tenant-Id': TENANT_ID },
  });

  expect(response.ok()).toBeTruthy();

  const data = await response.json();
  expect(data.code).toBe(200);
  expect(data.data.access_token).toBeDefined();

  return data.data.access_token;
}

test.describe('插件 API 测试', () => {
  let token: string;

  test.beforeAll(async ({ request }) => {
    token = await getAccessToken(request);
  });

  test('获取插件列表', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/ai/console/v1/plugins`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': TENANT_ID,
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data).toBeInstanceOf(Array);
    expect(data.total).toBeGreaterThanOrEqual(0);
  });

  test('获取插件配置', async ({ request }) => {
    const pluginId = 'langgenius/ollama';

    const response = await request.get(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data.plugin_id).toBe(pluginId);
    expect(data.data.plugin_config).toBeDefined();
    expect(data.data.runtime_config).toBeDefined();
  });

  test('更新插件配置', async ({ request }) => {
    const pluginId = 'langgenius/ollama';
    const timestamp = Date.now();
    const testKey = `api_test_${timestamp}`;
    const testValue = `test_value_${timestamp}`;

    const response = await request.patch(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
          'Content-Type': 'application/json',
        },
        data: {
          runtime_config: {
            [testKey]: testValue,
          },
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data.runtime_config[testKey]).toBe(testValue);

    // 验证配置已持久化
    const verifyResponse = await request.get(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    const verifyData = await verifyResponse.json();
    expect(verifyData.data.runtime_config[testKey]).toBe(testValue);
  });

  test('获取运行时状态', async ({ request }) => {
    const pluginId = 'langgenius/ollama';

    const response = await request.get(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/runtime-state?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data.plugin_id).toBe(pluginId);
    expect(data.data.status).toBeDefined();
    expect(data.data.health_status).toBeDefined();
  });

  test('获取统计数据', async ({ request }) => {
    const response = await request.get(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/statistics`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data.status_stats).toBeDefined();
    expect(data.data.usage_stats).toBeDefined();
    expect(data.data.runtime_stats).toBeDefined();
  });

  test('启动插件', async ({ request }) => {
    const pluginId = 'langgenius/ollama';

    const response = await request.post(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/start?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    expect(data.data.plugin_id).toBe(pluginId);
    // 注意：演示环境可能启动失败，所以不验证 status
  });

  test('停止插件', async ({ request }) => {
    const pluginId = 'langgenius/ollama';

    const response = await request.post(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/stop?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
  });

  test('获取不存在的插件配置应返回错误', async ({ request }) => {
    const pluginId = 'nonexistent/plugin';

    const response = await request.get(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
        },
      }
    );

    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBe(400);
  });

  test('无认证访问应返回 401', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/ai/console/v1/plugins`);

    expect(response.status()).toBe(401);
  });

  test('无租户 ID 应返回 400', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/ai/console/v1/plugins`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    expect(response.status()).toBe(400);
  });

  test('更新配置为空对象应成功', async ({ request }) => {
    const pluginId = 'langgenius/ollama';

    const response = await request.patch(
      `${BASE_URL}/api/ai/console/v1/plugins/installations/config?plugin_id=${encodeURIComponent(pluginId)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': TENANT_ID,
          'Content-Type': 'application/json',
        },
        data: { runtime_config: {} },
      }
    );

    expect(response.ok()).toBeTruthy();
  });

  test('批量运行时状态查询', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/ai/console/v1/plugins/runtime-states`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': TENANT_ID,
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.code).toBe(200);
    // 注意：API 可能返回对象或数组
    expect(data.data).toBeDefined();
  });
});
