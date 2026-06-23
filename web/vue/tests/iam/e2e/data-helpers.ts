/**
 * IAM 模块 E2E 测试数据管理辅助函数
 *
 * 提供统一的测试数据创建、删除和清理功能，避免测试间数据污染。
 *
 * ## 设计原则
 *
 * 1. **幂等性**: 重复调用不会产生副作用
 * 2. **命名约定**: 自动添加 `e2e-` 前缀，便于识别和清理
 * 3. **向后兼容**: 清理时同时匹配 `e2e-` 和 `e2e_` 两种前缀
 * 4. **错误容错**: 删除操作失败不阻塞清理流程
 * 5. **类型安全**: 完整的 TypeScript 类型定义
 *
 * ## 认证说明
 *
 * IAM Admin API 需要：
 * - 管理员 Token（从 tenant admin 获取）
 * - X-Tenant-Id header（从 IAM 用户登录获取）
 *
 * ## 使用示例
 *
 * ```typescript
 * import { createRoleViaAPI, deleteRoleViaAPI, getIamAdminAuth } from './data-helpers';
 *
 * test.describe('角色管理', () => {
 *   let testRoleId: string;
 *   let token: string;
 *   let tenantId: string;
 *
 *   test.beforeAll(async ({ request }) => {
 *     const auth = await getIamAdminAuth(request);
 *     token = auth.token;
 *     tenantId = auth.tenantId;
 *     const role = await createRoleViaAPI(request, token, tenantId);
 *     testRoleId = role.id;
 *   });
 *
 *   test.afterAll(async ({ request }) => {
 *     await deleteRoleViaAPI(request, token, tenantId, testRoleId);
 *   });
 * });
 * ```
 */
import { type APIRequestContext } from '@playwright/test';
import { getAdminToken } from '../../tenant/e2e/data-helpers';

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 角色创建参数
 */
export interface RoleCreateData {
  code?: string;
  name?: string;
  description?: string;
}

/**
 * 组织创建参数
 */
export interface OrganizationCreateData {
  name?: string;
  code?: string;
  parent_id?: string;
  sort_order?: number;
  description?: string;
}

/**
 * 用户创建参数
 */
export interface IamUserCreateData {
  username?: string;
  password?: string;
  email?: string;
  phone?: string;
  nickname?: string;
}

/**
 * 角色响应
 */
export interface RoleResponse {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_system: boolean;
  created_at: string;
}

/**
 * 组织响应
 */
export interface OrganizationResponse {
  id: string;
  name: string;
  code?: string;
  parent_id?: string;
  sort_order: number;
  status: string;
  created_at: string;
}

/**
 * 用户响应
 */
export interface IamUserResponse {
  id: string;
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  status: string;
  created_at: string;
}

/**
 * IAM 管理员认证信息
 */
export interface IamAdminAuth {
  token: string;
  tenantId: string;
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
export const E2E_PREFIX = 'e2e-';

/**
 * 默认角色创建参数
 */
const DEFAULT_ROLE_DATA: RoleCreateData = {
  code: `e2e-role-${Date.now()}`,
  name: 'E2E测试角色',
  description: 'E2E测试角色描述',
};

/**
 * 默认组织创建参数
 */
const DEFAULT_ORGANIZATION_DATA: OrganizationCreateData = {
  name: 'E2E测试组织',
  code: `e2e-org-${Date.now()}`,
  sort_order: 0,
};

/**
 * 默认用户创建参数
 */
const DEFAULT_IAM_USER_DATA: IamUserCreateData = {
  username: `e2e-iam-user-${Date.now()}`,
  password: 'Test123456!',
  email: `e2e-iam-${Date.now()}@test.com`,
  nickname: 'E2E测试用户',
};

// ============================================================================
// 认证辅助函数
// ============================================================================

/**
 * 获取 IAM 管理员认证信息
 *
 * 返回管理员 Token 和租户 ID，供 IAM Admin API 调用使用。
 *
 * @param request Playwright APIRequestContext
 * @param username 用户名，默认 'admin'
 * @param password 密码，默认 'admin123'
 * @returns { token, tenantId } 管理员认证信息
 */
export async function getIamAdminAuth(
  request: APIRequestContext,
  username = 'admin',
  password = 'admin123'
): Promise<IamAdminAuth> {
  // 1. 获取管理员 Token
  const token = await getAdminToken(request, username, password);

  // 2. 获取租户 ID（从管理员信息或 IAM 用户登录）
  const meResponse = await request.get('/api/tenant/admin/v1/admin/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!meResponse.ok()) {
    throw new Error(`获取管理员信息失败 (HTTP ${meResponse.status()})`);
  }

  const meData = await meResponse.json();
  // 从管理员信息中获取租户 ID
  const tenantId = meData?.data?.tenant_id;

  if (!tenantId) {
    // 备选：尝试通过 IAM 用户登录获取
    const loginResponse = await request.post('/api/iam/console/v1/auth/login', {
      data: { account: username, password },
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const iamTenantId = loginData?.data?.tenant_id;
      if (iamTenantId) {
        return { token, tenantId: iamTenantId };
      }
    }

    throw new Error('无法获取租户 ID');
  }

  return { token, tenantId };
}

// ============================================================================
// 角色管理辅助函数
// ============================================================================

/**
 * 通过 API 创建角色
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param data 角色创建参数（可选）
 * @returns 创建的角色信息
 */
export async function createRoleViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  data?: RoleCreateData
): Promise<RoleResponse> {
  const payload = {
    ...DEFAULT_ROLE_DATA,
    ...data,
    code: data?.code || `e2e-role-${Date.now()}`,
    name: data?.name || DEFAULT_ROLE_DATA.name,
  };

  const response = await request.post('/api/iam/admin/v1/roles', {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
    data: payload,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `创建角色失败 (HTTP ${response.status()}): ${errorText}`
    );
  }

  const result: ApiResponse<RoleResponse> = await response.json();
  const role = result?.data;

  if (!role?.id) {
    throw new Error(
      `创建角色失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return role;
}

/**
 * 通过 API 删除角色
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param id 角色 ID
 */
export async function deleteRoleViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  id: string
): Promise<void> {
  const response = await request.delete(`/api/iam/admin/v1/roles/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
  });

  if (!response.ok() && response.status() !== 404) {
    const errorText = await response.text();
    console.warn(
      `删除角色失败 (ID: ${id}, HTTP ${response.status()}): ${errorText}`
    );
  }
}

// ============================================================================
// 组织管理辅助函数
// ============================================================================

/**
 * 通过 API 创建组织
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param data 组织创建参数（可选）
 * @returns 创建的组织信息
 */
export async function createOrganizationViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  data?: OrganizationCreateData
): Promise<OrganizationResponse> {
  const payload = {
    ...DEFAULT_ORGANIZATION_DATA,
    ...data,
    code: data?.code || `e2e-org-${Date.now()}`,
    name: data?.name || DEFAULT_ORGANIZATION_DATA.name,
  };

  const response = await request.post('/api/iam/admin/v1/organizations', {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
    data: payload,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `创建组织失败 (HTTP ${response.status()}): ${errorText}`
    );
  }

  const result: ApiResponse<OrganizationResponse> = await response.json();
  const organization = result?.data;

  if (!organization?.id) {
    throw new Error(
      `创建组织失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return organization;
}

/**
 * 通过 API 删除组织
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param id 组织 ID
 */
export async function deleteOrganizationViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  id: string
): Promise<void> {
  const response = await request.delete(`/api/iam/admin/v1/organizations/${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-Id': tenantId,
    },
  });

  if (!response.ok() && response.status() !== 404) {
    const errorText = await response.text();
    console.warn(
      `删除组织失败 (ID: ${id}, HTTP ${response.status()}): ${errorText}`
    );
  }
}

// ============================================================================
// 用户管理辅助函数
// ============================================================================

/**
 * 通过 API 创建 IAM 测试用户
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param data 用户创建参数（可选）
 * @returns 创建的用户信息
 */
export async function createTestUserViaAPI(
  request: APIRequestContext,
  token: string,
  tenantId: string,
  data?: IamUserCreateData
): Promise<IamUserResponse> {
  const payload = {
    ...DEFAULT_IAM_USER_DATA,
    ...data,
    username: data?.username || `e2e-iam-user-${Date.now()}`,
    password: data?.password || DEFAULT_IAM_USER_DATA.password,
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

  const result: ApiResponse<IamUserResponse> = await response.json();
  const user = result?.data;

  if (!user?.id) {
    throw new Error(
      `创建用户失败: 响应中未找到 data.id 字段 (响应: ${JSON.stringify(result)})`
    );
  }

  return user;
}

/**
 * 通过 API 删除 IAM 测试用户
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 * @param id 用户 ID
 */
export async function deleteTestUserViaAPI(
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
 * 清理 IAM 模块所有 E2E 测试数据
 *
 * 根据命名约定识别并删除所有测试数据。
 * 同时匹配 `e2e-` 和 `e2e_` 两种前缀，确保清理所有历史数据。
 *
 * @param request Playwright APIRequestContext
 * @param token 管理员 Token
 * @param tenantId 租户 ID
 */
export async function cleanupAllIamE2EData(
  request: APIRequestContext,
  token: string,
  tenantId: string
): Promise<void> {
  // 1. 清理角色数据
  try {
    const rolesResponse = await request.get('/api/iam/admin/v1/roles', {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
      params: {
        keyword: 'e2e',
      },
    });

    if (rolesResponse.ok()) {
      const rolesResult = await rolesResponse.json();
      const roles = rolesResult?.data || [];

      for (const role of roles) {
        if (role.code && isE2EData(role.code)) {
          await deleteRoleViaAPI(request, token, tenantId, role.id);
        }
      }
    }
  } catch (error) {
    console.warn('清理角色数据时出错:', error);
  }

  // 2. 清理组织数据
  try {
    const orgsResponse = await request.get('/api/iam/admin/v1/organizations', {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
      params: {
        keyword: 'e2e',
      },
    });

    if (orgsResponse.ok()) {
      const orgsResult = await orgsResponse.json();
      const organizations = orgsResult?.data || [];

      for (const org of organizations) {
        if (org.code && isE2EData(org.code)) {
          await deleteOrganizationViaAPI(request, token, tenantId, org.id);
        }
      }
    }
  } catch (error) {
    console.warn('清理组织数据时出错:', error);
  }

  // 3. 清理用户数据
  try {
    const usersResponse = await request.get('/api/iam/admin/v1/users', {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Tenant-Id': tenantId,
      },
      params: {
        keyword: 'e2e',
      },
    });

    if (usersResponse.ok()) {
      const usersResult = await usersResponse.json();
      const users = usersResult?.data || [];

      for (const user of users) {
        if (user.username && isE2EData(user.username)) {
          await deleteTestUserViaAPI(request, token, tenantId, user.id);
        }
      }
    }
  } catch (error) {
    console.warn('清理用户数据时出错:', error);
  }
}

// ============================================================================
// 工具函数
// ============================================================================

/**
 * 生成带 E2E 前缀的唯一标识符
 *
 * @param prefix 标识符前缀（如 'role', 'user', 'org'）
 * @returns 格式为 `e2e-{prefix}-{timestamp}` 的唯一标识符
 */
export function generateE2EId(prefix: string): string {
  return `${E2E_PREFIX}${prefix}-${Date.now()}`;
}

/**
 * 检查标识符是否为 E2E 测试数据
 * 同时匹配 `e2e-` 和 `e2e_` 两种前缀
 *
 * @param identifier 标识符
 * @returns 是否为 E2E 测试数据
 */
export function isE2EData(identifier: string): boolean {
  return identifier.startsWith('e2e-') || identifier.startsWith('e2e_');
}
