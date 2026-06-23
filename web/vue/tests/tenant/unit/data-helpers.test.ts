/**
 * 测试数据管理辅助函数单元测试
 */
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import {
  createTenantViaAPI,
  deleteTenantViaAPI,
  createModuleViaAPI,
  deleteModuleViaAPI,
  createUserViaAPI,
  deleteUserViaAPI,
  cleanupAllE2EData,
  generateE2EId,
  isE2EData,
  E2E_PREFIX,
} from '../e2e/data-helpers';
import type { APIRequestContext, APIResponse } from '@playwright/test';

// ============================================================================
// Mock 工具函数
// ============================================================================

/**
 * 创建 Mock APIResponse
 */
function createMockResponse(
  ok: boolean,
  status: number,
  data?: unknown
): APIResponse {
  return {
    ok: () => ok,
    status: () => status,
    json: async () => data || {},
    text: async () => JSON.stringify(data || {}),
  } as APIResponse;
}

/**
 * 创建 Mock APIRequestContext
 */
function createMockRequest(
  responses: Record<string, { ok: boolean; status: number; data?: unknown }>
): APIRequestContext {
  return {
    post: vi.fn(async (url: string) => {
      const key = Object.keys(responses).find((k) => url.includes(k));
      const response = responses[key || 'default'] || { ok: false, status: 404 };
      return createMockResponse(response.ok, response.status, response.data);
    }),
    get: vi.fn(async (url: string) => {
      const key = Object.keys(responses).find((k) => url.includes(k));
      const response = responses[key || 'default'] || { ok: false, status: 404 };
      return createMockResponse(response.ok, response.status, response.data);
    }),
    delete: vi.fn(async (url: string) => {
      const key = Object.keys(responses).find((k) => url.includes(k));
      const response = responses[key || 'default'] || { ok: false, status: 404 };
      return createMockResponse(response.ok, response.status, response.data);
    }),
  } as unknown as APIRequestContext;
}

// ============================================================================
// 测试
// ============================================================================

describe('测试数据管理辅助函数', () => {
  const mockToken = 'mock_admin_token';
  const mockTenantId = 'mock_tenant_id';

  describe('createTenantViaAPI', () => {
    it('成功创建租户', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: true,
          status: 201,
          data: {
            data: {
              id: 'tenant_123',
              name: 'E2E测试租户',
              code: 'e2e-tenant-test',
              status: 'active',
            },
          },
        },
      });

      const result = await createTenantViaAPI(mockRequest, mockToken);

      expect(result.id).toBe('tenant_123');
      expect(result.name).toBe('E2E测试租户');
      expect(result.code.startsWith(E2E_PREFIX)).toBe(true);
    });

    it('使用自定义参数创建租户', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: true,
          status: 201,
          data: {
            data: {
              id: 'tenant_123',
              name: '自定义租户',
              code: 'e2e-custom-tenant',
              status: 'active',
            },
          },
        },
      });

      const result = await createTenantViaAPI(mockRequest, mockToken, {
        name: '自定义租户',
        code: 'e2e-custom-tenant',
        contact_email: 'custom@test.com',
      });

      expect(result.id).toBe('tenant_123');
      expect(result.name).toBe('自定义租户');
    });

    it('创建失败时抛出异常', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: false,
          status: 400,
          data: { message: '租户编码已存在' },
        },
      });

      await expect(createTenantViaAPI(mockRequest, mockToken)).rejects.toThrow(
        '创建租户失败 (HTTP 400)'
      );
    });

    it('响应缺少 data.id 时抛出异常', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: true,
          status: 201,
          data: { data: {} },
        },
      });

      await expect(createTenantViaAPI(mockRequest, mockToken)).rejects.toThrow(
        '创建租户失败: 响应中未找到 data.id 字段'
      );
    });
  });

  describe('deleteTenantViaAPI', () => {
    it('成功删除租户', async () => {
      const mockRequest = createMockRequest({
        '/tenants/': {
          ok: true,
          status: 204,
        },
      });

      await expect(
        deleteTenantViaAPI(mockRequest, mockToken, 'tenant_123')
      ).resolves.not.toThrow();
    });

    it('404 错误不抛出异常', async () => {
      const mockRequest = createMockRequest({
        '/tenants/': {
          ok: false,
          status: 404,
        },
      });

      await expect(
        deleteTenantViaAPI(mockRequest, mockToken, 'tenant_123')
      ).resolves.not.toThrow();
    });

    it('其他错误输出警告但不抛出异常', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const mockRequest = createMockRequest({
        '/tenants/': {
          ok: false,
          status: 500,
          data: { message: '服务器错误' },
        },
      });

      await deleteTenantViaAPI(mockRequest, mockToken, 'tenant_123');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('删除租户失败')
      );

      consoleSpy.mockRestore();
    });
  });

  describe('createModuleViaAPI', () => {
    it('成功创建模块', async () => {
      const mockRequest = createMockRequest({
        '/modules': {
          ok: true,
          status: 201,
          data: {
            data: {
              id: 'module_123',
              name: 'E2E测试模块',
              code: 'e2e-module-test',
            },
          },
        },
      });

      const result = await createModuleViaAPI(mockRequest, mockToken);

      expect(result.id).toBe('module_123');
      expect(result.name).toBe('E2E测试模块');
      expect(result.code.startsWith(E2E_PREFIX)).toBe(true);
    });

    it('创建失败时抛出异常', async () => {
      const mockRequest = createMockRequest({
        '/modules': {
          ok: false,
          status: 400,
          data: { message: '模块编码已存在' },
        },
      });

      await expect(createModuleViaAPI(mockRequest, mockToken)).rejects.toThrow(
        '创建模块失败 (HTTP 400)'
      );
    });
  });

  describe('deleteModuleViaAPI', () => {
    it('成功删除模块', async () => {
      const mockRequest = createMockRequest({
        '/modules/': {
          ok: true,
          status: 204,
        },
      });

      await expect(
        deleteModuleViaAPI(mockRequest, mockToken, 'module_123')
      ).resolves.not.toThrow();
    });
  });

  describe('createUserViaAPI', () => {
    it('成功创建用户（包含 X-Tenant-Id header）', async () => {
      const mockRequest = createMockRequest({
        '/users': {
          ok: true,
          status: 201,
          data: {
            data: {
              id: 'user_123',
              username: 'e2e-user-test',
              email: 'e2e@test.com',
            },
          },
        },
      });

      const result = await createUserViaAPI(
        mockRequest,
        mockToken,
        mockTenantId
      );

      expect(result.id).toBe('user_123');
      expect(result.username.startsWith(E2E_PREFIX)).toBe(true);

      // 验证传入了正确的 headers
      const postCall = (mockRequest.post as Mock).mock.calls[0];
      expect(postCall[1]?.headers?.['X-Tenant-Id']).toBe(mockTenantId);
    });

    it('使用自定义参数创建用户', async () => {
      const mockRequest = createMockRequest({
        '/users': {
          ok: true,
          status: 201,
          data: {
            data: {
              id: 'user_123',
              username: 'e2e-custom-user',
              email: 'custom@test.com',
            },
          },
        },
      });

      const result = await createUserViaAPI(
        mockRequest,
        mockToken,
        mockTenantId,
        {
          username: 'e2e-custom-user',
          email: 'custom@test.com',
          nickname: '自定义用户',
        }
      );

      expect(result.id).toBe('user_123');
      expect(result.username).toBe('e2e-custom-user');
    });

    it('创建失败时抛出异常', async () => {
      const mockRequest = createMockRequest({
        '/users': {
          ok: false,
          status: 400,
          data: { message: '用户名已存在' },
        },
      });

      await expect(
        createUserViaAPI(mockRequest, mockToken, mockTenantId)
      ).rejects.toThrow('创建用户失败 (HTTP 400)');
    });
  });

  describe('deleteUserViaAPI', () => {
    it('成功删除用户（包含 X-Tenant-Id header）', async () => {
      const mockRequest = createMockRequest({
        '/users/': {
          ok: true,
          status: 204,
        },
      });

      await expect(
        deleteUserViaAPI(mockRequest, mockToken, mockTenantId, 'user_123')
      ).resolves.not.toThrow();

      // 验证传入了正确的 headers
      const deleteCall = (mockRequest.delete as Mock).mock.calls[0];
      expect(deleteCall[1]?.headers?.['X-Tenant-Id']).toBe(mockTenantId);
    });
  });

  describe('cleanupAllE2EData', () => {
    it('清理租户和模块数据（无 tenantId）', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: true,
          status: 200,
          data: {
            data: [
              {
                id: 'tenant_1',
                code: 'e2e-tenant-1',
                name: 'E2E租户1',
                status: 'active',
              },
              {
                id: 'tenant_2',
                code: 'prod_tenant',
                name: '生产租户',
                status: 'active',
              },
            ],
          },
        },
        '/modules': {
          ok: true,
          status: 200,
          data: {
            data: [
              {
                id: 'module_1',
                code: 'e2e-module-1',
                name: 'E2E模块1',
              },
            ],
          },
        },
        '/tenants/': {
          ok: true,
          status: 204,
        },
        '/modules/': {
          ok: true,
          status: 204,
        },
      });

      await cleanupAllE2EData(mockRequest, mockToken);

      // 验证删除了 E2E 租户
      const deleteCalls = (mockRequest.delete as Mock).mock.calls;
      const tenantDeleteCalls = deleteCalls.filter((call: unknown[]) =>
        (call[0] as string).includes('/tenants/')
      );
      expect(tenantDeleteCalls.length).toBeGreaterThan(0);
    });

    it('清理用户数据（提供 tenantId）', async () => {
      const mockRequest = createMockRequest({
        '/users': {
          ok: true,
          status: 200,
          data: {
            data: [
              {
                id: 'user_1',
                username: 'e2e-user-1',
                email: 'e2e@test.com',
              },
              {
                id: 'user_2',
                username: 'prod_user',
                email: 'prod@test.com',
              },
            ],
          },
        },
        '/tenants': {
          ok: true,
          status: 200,
          data: { data: [] },
        },
        '/modules': {
          ok: true,
          status: 200,
          data: { data: [] },
        },
        '/users/': {
          ok: true,
          status: 204,
        },
      });

      await cleanupAllE2EData(mockRequest, mockToken, mockTenantId);

      // 验证查询用户时传入了 X-Tenant-Id
      const getCalls = (mockRequest.get as Mock).mock.calls;
      const userGetCall = getCalls.find((call: unknown[]) =>
        (call[0] as string).includes('/users')
      );
      expect(userGetCall[1]?.headers?.['X-Tenant-Id']).toBe(mockTenantId);
    });

    it('清理失败时不中断流程', async () => {
      const mockRequest = createMockRequest({
        '/tenants': {
          ok: true,
          status: 200,
          data: {
            data: [
              {
                id: 'tenant_1',
                code: 'e2e-tenant-1',
                name: 'E2E租户1',
                status: 'active',
              },
            ],
          },
        },
        '/modules': {
          ok: true,
          status: 200,
          data: {
            data: [
              {
                id: 'module_1',
                code: 'e2e-module-1',
                name: 'E2E模块1',
              },
            ],
          },
        },
        '/tenants/': {
          ok: false,
          status: 500,
          data: { message: '服务器错误' },
        },
        '/modules/': {
          ok: false,
          status: 500,
          data: { message: '服务器错误' },
        },
      });

      // 清理应该完成，即使删除失败
      await expect(
        cleanupAllE2EData(mockRequest, mockToken)
      ).resolves.not.toThrow();
    });
  });

  describe('工具函数', () => {
    describe('generateE2EId', () => {
      it('生成带前缀的唯一标识符', () => {
        const id = generateE2EId('tenant');
        // 新格式：e2e-tenant-{timestamp}
        expect(id.startsWith(`${E2E_PREFIX}tenant-`)).toBe(true);
        expect(id.length).toBeGreaterThan(`${E2E_PREFIX}tenant-`.length);
      });

      it('不同调用生成不同标识符', async () => {
        const id1 = generateE2EId('user');
        await new Promise((resolve) => setTimeout(resolve, 10));
        const id2 = generateE2EId('user');
        expect(id1).not.toBe(id2);
      });
    });

    describe('isE2EData', () => {
      it('识别 e2e- 前缀的测试数据（新格式）', () => {
        expect(isE2EData('e2e-tenant-123')).toBe(true);
        expect(isE2EData('e2e-user-abc')).toBe(true);
        expect(isE2EData('e2e-module-test')).toBe(true);
      });

      it('识别 e2e_ 前缀的测试数据（旧格式，向后兼容）', () => {
        expect(isE2EData('e2e_tenant_123')).toBe(true);
        expect(isE2EData('e2e_user_abc')).toBe(true);
        expect(isE2EData('e2e_module_test')).toBe(true);
      });

      it('排除非 E2E 数据', () => {
        expect(isE2EData('prod-tenant')).toBe(false);
        expect(isE2EData('user-123')).toBe(false);
        expect(isE2EData('E2E-user')).toBe(false); // 区分大小写
        expect(isE2EData('test-tenant')).toBe(false);
      });
    });
  });
});
