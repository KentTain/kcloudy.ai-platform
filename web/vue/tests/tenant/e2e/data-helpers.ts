/**
 * E2E 测试数据管理辅助函数
 *
 * 提供统一的测试数据创建、删除和清理功能，避免测试间数据污染。
 *
 * ## 设计原则
 *
 * 1. **幂等性**: 重复调用不会产生副作用
 * 2. **命名约定**: 自动添加 `e2e_` 前缀，便于识别和清理
 * 3. **错误容错**: 删除操作失败不阻塞清理流程
 * 4. **类型安全**: 完整的 TypeScript 类型定义
 *
 * ## 使用示例
 *
 * ```typescript
 * import { createTenantViaAPI, deleteTenantViaAPI, cleanupAllE2EData } from './data-helpers';
 *
 * test.describe('租户管理', () => {
 *   let testTenantId: string;
 *
 *   test.beforeAll(async ({ request }) => {
 *     const token = await getAdminToken(request);
 *     const tenant = await createTenantViaAPI(request, token);
 *     testTenantId = tenant.id;
 *   });
 *
 *   test.afterAll(async ({ request }) => {
 *     const token = await getAdminToken(request);
 *     await deleteTenantViaAPI(request, token, testTenantId);
 *   });
 * });
 * ```
 */
import { type APIRequestContext } from '@playwright/test';

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 租户创建参数
 */
export interface TenantCreateData {
  name?: string;
  code?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
}

/**
 * 模块创建参数
 */
export interface ModuleCreateData {
  name?: string;
  code?: string;
  description?: string;
}

/**
 * 用户创建参数
 */
export interface UserCreateData {
  username?: string;
  password?: string;
  email?: string;
  phone?: string;
  nickname?: string;
}

/**
 * 租户响应
 */
export interface TenantResponse {
  id: string;
  name: string;
  code: string;
  status: string;
}

/**
 * 模块响应
 */
export interface ModuleResponse {
  id: string;
  name: string;
  code: string;
}

/**
 * 用户响应
 */
export interface UserResponse {
  id: string;
  username: string;
  email?: string;
  phone?: string;
}

/**
 * API 响应包装
 */
interface ApiResponse<T> {
  data?: T;
  message?: string;
}

// ============================================================================
// 常量
// ============================================================================

/**
 * E2E 测试数据前缀
 */
export const E2E_PREFIX = 'e2e_';

/**
 * 默认租户创建参数
 */
const DEFAULT_TENANT_DATA: TenantCreateData = {
  name: 'E2E测试租户',
  code: `e2e_tenant_${Date.now()}`,
  contact_name: 'E2E测试联系人',
  contact_email: 'e2e@test.com',
};

/**
 * 默认模块创建参数
 */
const DEFAULT_MODULE_DATA: ModuleCreateData = {
  name: 'E2E测试模块',
  code: `e2e_module_${Date.now()}`,
  description: 'E2E测试模块描述',
};

/**
 * 默认用户创建参数
 */
const DEFAULT_USER_DATA: UserCreateData = {
  username: `e2e_user_${Date.now()}`,
  password: 'Test123456!',
  email: `e2e_${Date.now()}@test.com`,
  nickname: 'E2E测试用户',
};

// ============================================================================
// 租户管理辅助函数
// ============================================================================

/**
 * 通过 API 创建租户
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param data 租户创建参数（可选）
 * @returns 创建的租户信息
 * @throws 创建失败时抛出异常
 */
export async function createTenantViaAPI(
  request: APIRequestContext,
  token: string,
  data?: TenantCreateData
): Promise<TenantResponse> {
  const payload = {
    ...DEFAULT_TENANT_DATA,
    ...data,
    code: data?.code || `e2e_tenant_${Date.now()}`,
    name: data?.name || DEFAULT_TENANT_DATA.name,
  };

  const response = await request.post('/api/tenant/admin/v1/tenants', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: payload,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `创建租户失败 (HTTP ${response.status()}): ${errorText}`
    );
  }

  const result: ApiResponse<TenantResponse> = await response.json();
  const tenant = result?.data;

  if (!tenant?.id) {
    throw new Error(
      `创建租户失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return tenant;
}

/**
 * 通过 API 删除租户
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param id 租户 ID
 * @throws 删除失败时抛出异常
 */
export async function deleteTenantViaAPI(
  request: APIRequestContext,
  token: string,
  id: string
): Promise<void> {
  const response = await request.delete(`/api/tenant/admin/v1/tenants/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok() && response.status() !== 404) {
    const errorText = await response.text();
    console.warn(
      `删除租户失败 (ID: ${id}, HTTP ${response.status()}): ${errorText}`
    );
  }
}

// ============================================================================
// 模块管理辅助函数
// ============================================================================

/**
 * 通过 API 创建模块
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param data 模块创建参数（可选）
 * @returns 创建的模块信息
 * @throws 创建失败时抛出异常
 */
export async function createModuleViaAPI(
  request: APIRequestContext,
  token: string,
  data?: ModuleCreateData
): Promise<ModuleResponse> {
  const payload = {
    ...DEFAULT_MODULE_DATA,
    ...data,
    code: data?.code || `e2e_module_${Date.now()}`,
    name: data?.name || DEFAULT_MODULE_DATA.name,
  };

  const response = await request.post('/api/tenant/admin/v1/modules', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: payload,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `创建模块失败 (HTTP ${response.status()}): ${errorText}`
    );
  }

  const result: ApiResponse<ModuleResponse> = await response.json();
  const module = result?.data;

  if (!module?.id) {
    throw new Error(
      `创建模块失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return module;
}

/**
 * 通过 API 删除模块
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param id 模块 ID
 */
export async function deleteModuleViaAPI(
  request: APIRequestContext,
  token: string,
  id: string
): Promise<void> {
  const response = await request.delete(`/api/tenant/admin/v1/modules/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok() && response.status() !== 404) {
    const errorText = await response.text();
    console.warn(
      `删除模块失败 (ID: ${id}, HTTP ${response.status()}): ${errorText}`
    );
  }
}

// ============================================================================
// 用户管理辅助函数
// ============================================================================

/**
 * 通过 API 创建用户
 *
 * 注意：User API 需要 X-Tenant-Id header 进行多租户隔离
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param data 用户创建参数（可选）
 * @returns 创建的用户信息
 * @throws 创建失败时抛出异常
 */
export async function createUserViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  data?: UserCreateData
): Promise<UserResponse> {
  const payload = {
    ...DEFAULT_USER_DATA,
    ...data,
    username: data?.username || `e2e_user_${Date.now()}`,
    password: data?.password || DEFAULT_USER_DATA.password,
  };

  const response = await request.post('/api/iam/admin/v1/users', {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
    data: payload,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `创建用户失败 (HTTP ${response.status()}): ${errorText}`
    );
  }

  const result: ApiResponse<UserResponse> = await response.json();
  const user = result?.data;

  if (!user?.id) {
    throw new Error(
      `创建用户失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return user;
}

/**
 * 通过 API 删除用户
 *
 * 注意：User API 需要 X-Tenant-Id header 进行多租户隔离
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param id 用户 ID
 */
export async function deleteUserViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  id: string
): Promise<void> {
  const response = await request.delete(`/api/iam/admin/v1/users/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
  });

  if (!response.ok() && response.status() !== 404) {
    const errorText = await response.text();
    console.warn(
      `删除用户失败 (ID: ${id}, HTTP ${response.status()}): ${errorText}`
    );
  }
}

// ============================================================================
// 批量清理辅助函数
// ============================================================================

/**
 * 清理所有 E2E 测试数据
 *
 * 根据命名约定（`e2e_` 前缀）识别并删除所有测试数据。
 * 如果未提供 tenantId，仅清理租户和模块数据；
 * 如果提供 tenantId，额外清理该租户下的用户数据。
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID（可选，用于清理用户数据）
 */
export async function cleanupAllE2EData(
  request: APIRequestContext,
  token: string,
  tenantId?: string
): Promise<void> {
  // 1. 清理用户数据（如果提供了 tenantId）
  if (tenantId) {
    try {
      const usersResponse = await request.get('/api/iam/admin/v1/users', {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-Id': tenantId,
        },
        params: {
          keyword: E2E_PREFIX,
        },
      });

      if (usersResponse.ok()) {
        const usersResult = await usersResponse.json();
        const users = usersResult?.data || [];

        for (const user of users) {
          if (user.username?.startsWith(E2E_PREFIX)) {
            await deleteUserViaAPI(request, token, tenantId, user.id);
          }
        }
      }
    } catch (error) {
      console.warn('清理用户数据时出错:', error);
    }
  }

  // 2. 清理租户数据
  try {
    const tenantsResponse = await request.get('/api/tenant/admin/v1/tenants', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        keyword: E2E_PREFIX,
      },
    });

    if (tenantsResponse.ok()) {
      const tenantsResult = await tenantsResponse.json();
      const tenants = tenantsResult?.data || [];

      for (const tenant of tenants) {
        if (tenant.code?.startsWith(E2E_PREFIX)) {
          await deleteTenantViaAPI(request, token, tenant.id);
        }
      }
    }
  } catch (error) {
    console.warn('清理租户数据时出错:', error);
  }

  // 3. 清理模块数据
  try {
    const modulesResponse = await request.get('/api/tenant/admin/v1/modules', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        keyword: E2E_PREFIX,
      },
    });

    if (modulesResponse.ok()) {
      const modulesResult = await modulesResponse.json();
      const modules = modulesResult?.data || [];

      for (const module of modules) {
        if (module.code?.startsWith(E2E_PREFIX)) {
          await deleteModuleViaAPI(request, token, module.id);
        }
      }
    }
  } catch (error) {
    console.warn('清理模块数据时出错:', error);
  }
}

// ============================================================================
// 工具函数
// ============================================================================

/**
 * 生成带 E2E 前缀的唯一标识符
 *
 * @param prefix 标识符前缀（如 'tenant', 'user', 'module'）
 * @returns 格式为 `e2e_{prefix}_{timestamp}` 的唯一标识符
 */
export function generateE2EId(prefix: string): string {
  return `${E2E_PREFIX}${prefix}_${Date.now()}`;
}

/**
 * 检查标识符是否为 E2E 测试数据
 *
 * @param identifier 标识符
 * @returns 是否为 E2E 测试数据
 */
export function isE2EData(identifier: string): boolean {
  return identifier.startsWith(E2E_PREFIX);
}
