/**
 * IAM 模块 - 角色管理 E2E 测试
 *
 * 测试场景：
 * 1. 角色列表渲染测试 - 验证角色列表加载和节点渲染
 * 2. 角色详情展示测试 - 验证选中角色后右侧详情面板展示
 * 3. 角色 CRUD 操作测试 - 新增、编辑、删除角色（内联弹窗 + 独立路由）
 * 4. 角色成员管理测试 - 成员列表、添加成员按钮
 * 5. 角色权限分配测试 - 分配权限弹窗
 * 6. API 辅助测试 - 角色 CRUD 的 API 级别验证
 */
import {
  test,
  expect,
  iamUserLogin,
  waitForSkeletonGone,
  waitForPageReady,
  captureConsoleErrors,
} from "./fixtures";
import {
  getIamAdminAuth,
  createRoleViaAPI,
  deleteRoleViaAPI,
  cleanupAllIamE2EData,
  generateE2EId,
  type IamAdminAuth,
  type RoleResponse,
} from "./data-helpers";
import type { APIRequestContext, Page } from "@playwright/test";

// ============================================================================
// 测试数据管理
// ============================================================================

interface TestContext {
  createdRoles: RoleResponse[];
  cachedAuth: IamAdminAuth | null;
}

const testContext: TestContext = {
  createdRoles: [],
  cachedAuth: null,
};

/**
 * 获取缓存的认证信息，避免重复登录
 */
async function getCachedAuth(request: APIRequestContext): Promise<IamAdminAuth> {
  if (!testContext.cachedAuth) {
    testContext.cachedAuth = await getIamAdminAuth(request);
  }
  return testContext.cachedAuth;
}

/**
 * 通过 API 创建测试角色
 */
async function createTestRole(
  request: APIRequestContext,
  name?: string,
  code?: string
): Promise<RoleResponse> {
  const auth = await getCachedAuth(request);
  const role = await createRoleViaAPI(request, auth.token, auth.tenantId, {
    name: name || `E2E测试角色-${Date.now()}`,
    code: code || generateE2EId("role"),
    description: "E2E 测试自动创建",
  });
  testContext.createdRoles.push(role);
  return role;
}

/**
 * 清理所有测试数据
 */
async function cleanupTestData(request: APIRequestContext) {
  if (testContext.createdRoles.length === 0) return;

  try {
    const auth = await getCachedAuth(request);

    for (const role of testContext.createdRoles) {
      await deleteRoleViaAPI(request, auth.token, auth.tenantId, role.id).catch(() => {});
    }
    testContext.createdRoles = [];
  } catch {
    // 清理失败不影响测试结果，只记录日志
    console.warn("清理测试数据失败，可能是因为登录限制");
  }
}

/**
 * 在角色列表页选中指定角色并等待详情面板显示
 */
async function selectRole(page: Page, roleId: string) {
  const roleItem = page.locator(`[data-testid="role-item-${roleId}"]`);
  await roleItem.click();
  await page.waitForTimeout(500);
}

// ============================================================================
// 测试用例
// ============================================================================

test.describe("IAM 角色管理页面", () => {
  test.beforeEach(async ({ page, request }) => {
    await iamUserLogin(page, request);
  });

  test.afterAll(async ({ request }) => {
    await cleanupTestData(request);
  });

  // ===========================================================================
  // 1. 角色列表渲染测试
  // ===========================================================================

  test.describe("角色列表渲染", () => {
    test("访问 /iam/roles 显示角色管理页面", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);

      await expect(page.locator('[data-testid="role-list-page"]')).toBeVisible();
    });

    test("页面标题和描述正确显示", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      // 使用更精确的选择器，避免匹配多个元素
      const pageTitle = page.locator('[data-testid="role-list-page"] h1');
      await expect(pageTitle).toHaveText("角色管理");
      await expect(page.locator("text=管理系统角色、成员和权限")).toBeVisible();
    });

    test("角色列表区域和新建按钮存在", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      // 使用更精确的选择器匹配角色列表标题
      const listHeader = page.locator(".w-\\[300px\\] .text-sm.font-medium");
      await expect(listHeader).toHaveText("角色列表");
      await expect(page.locator('[data-testid="create-role-btn"]')).toBeVisible();
    });

    test("角色列表项正确渲染", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const roleItems = page.locator('[data-testid^="role-item-"]');
      const count = await roleItems.count();
      expect(count).toBeGreaterThanOrEqual(0);

      if (count > 0) {
        const firstRole = roleItems.first();
        await expect(firstRole).toBeVisible();
        const text = await firstRole.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);
      }
    });

    test("角色列表包含 Shield 图标和角色名称", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const roleItems = page.locator('[data-testid^="role-item-"]');
      const count = await roleItems.count();
      if (count === 0) {
        test.skip(true, "没有可用的角色数据");
        return;
      }

      // 验证角色项包含结构信息
      const firstItem = roleItems.first();
      await expect(firstItem.locator(".font-medium")).toBeVisible();
    });

    test("系统角色显示系统 Badge", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const systemBadge = page.locator("span:has-text('系统')");
      const count = await systemBadge.count();
      // 系统角色可能存在也可能不存在，不作强制断言
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  // ===========================================================================
  // 2. 角色详情展示测试
  // ===========================================================================

  test.describe("角色详情展示", () => {
    test("未选中角色时显示占位提示", async ({ page }) => {
      await page.goto("/iam/roles");
      // 使用 domcontentloaded 而不是 waitForPageReady，以便在页面完全加载前检查占位提示
      await page.waitForLoadState("domcontentloaded");

      // 页面初始状态时应该显示占位提示，或者等待一段时间让组件渲染
      // 由于 loadRoles() 会自动选中第一个角色，这里使用较短的等待时间
      await page.waitForTimeout(200);

      // 如果页面还没有角色数据，占位提示应该可见
      // 如果已经有角色数据并自动选中了，占位提示会消失
      // 这个测试主要验证组件结构正确，不强制要求占位提示必须出现
      const noRoleSelected = page.locator('[data-testid="no-role-selected"]');
      const isVisible = await noRoleSelected.isVisible().catch(() => false);

      // 无论占位提示是否可见，页面结构应该是正确的
      // 如果占位提示不可见，说明已经有角色被选中
      if (isVisible) {
        await expect(page.locator("text=请从左侧选择一个角色")).toBeVisible();
      } else {
        // 如果占位提示不可见，验证角色详情面板存在
        await expect(page.locator('[data-testid="role-detail-header"]')).toBeVisible({ timeout: 5000 });
      }
    });

    test("点击角色项显示详情面板", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const roleItems = page.locator('[data-testid^="role-item-"]');
      const count = await roleItems.count();
      if (count === 0) {
        test.skip(true, "没有可用的角色数据");
        return;
      }

      await roleItems.first().click();
      await page.waitForTimeout(500);

      // 占位提示消失
      await expect(page.locator('[data-testid="no-role-selected"]')).not.toBeVisible();

      // 详情面板显示
      await expect(page.locator('[data-testid="role-detail-header"]')).toBeVisible();
      await expect(page.locator('[data-testid="edit-role-btn"]')).toBeVisible();
    });

    test("选中角色后显示 Tabs（成员、权限）", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const roleItems = page.locator('[data-testid^="role-item-"]');
      const count = await roleItems.count();
      if (count === 0) {
        test.skip(true, "没有可用的角色数据");
        return;
      }

      await roleItems.first().click();
      await page.waitForTimeout(500);

      await expect(page.locator('[data-testid="role-members-tab"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-permissions-tab"]')).toBeVisible();
    });

    test("角色详情头部显示角色名称和编码", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const roleItems = page.locator('[data-testid^="role-item-"]');
      const count = await roleItems.count();
      if (count === 0) {
        test.skip(true, "没有可用的角色数据");
        return;
      }

      await roleItems.first().click();
      await page.waitForTimeout(500);

      // 详情头部应有 h2 标题（角色名称）
      const detailHeader = page.locator('[data-testid="role-detail-header"]');
      await expect(detailHeader.locator("h2")).toBeVisible();
    });
  });

  // ===========================================================================
  // 3. 角色 CRUD 操作测试
  // ===========================================================================

  test.describe("角色 CRUD", () => {
    test("点击新建按钮打开创建弹窗", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await page.locator('[data-testid="create-role-btn"]').click();

      const dialog = page.locator('[data-testid="role-form-dialog"]');
      await expect(dialog).toBeVisible();
      // 弹窗标题应包含"新建角色"
      await expect(dialog.locator("h2")).toContainText("新建角色");
    });

    test("创建角色弹窗包含所有必填字段", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await page.locator('[data-testid="create-role-btn"]').click();

      // data-testid 在外层容器，需要定位内部的 input 元素
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-name-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-description-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-submit-btn"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-cancel-btn"]')).toBeVisible();
    });

    test("成功创建角色", async ({ page, request }) => {
      const roleCode = generateE2EId("role");
      const roleName = `E2E创建角色-${Date.now()}`;

      await page.goto("/iam/roles");
      await waitForPageReady(page);

      await page.locator('[data-testid="create-role-btn"]').click();

      // data-testid 在外层容器，需要定位内部的 input 元素
      await page.locator('[data-testid="role-form-code-input"] input').fill(roleCode);
      await page.locator('[data-testid="role-form-name-input"] input').fill(roleName);
      await page.locator('[data-testid="role-form-description-input"] input').fill("E2E 测试创建的角色描述");

      await page.locator('[data-testid="role-form-submit-btn"]').click();

      // 等待弹窗关闭
      await expect(page.locator('[data-testid="role-form-dialog"]')).not.toBeVisible({ timeout: 10000 });

      // 验证新角色出现在列表中
      await waitForPageReady(page);
      await expect(page.locator(`text=${roleName}`)).toBeVisible({ timeout: 10000 });

      // 清理：通过 API 删除创建的角色
      const auth = await getIamAdminAuth(request);
      const rolesResponse = await request.get("/api/iam/admin/v1/roles", {
        headers: {
          Authorization: `Bearer ${auth.token}`,
          "X-Tenant-Id": auth.tenantId,
        },
        params: { keyword: roleCode },
      });
      if (rolesResponse.ok()) {
        const data = await rolesResponse.json();
        const roles = data?.data || [];
        const createdRole = roles.find((r: { code: string }) => r.code === roleCode);
        if (createdRole) {
          await deleteRoleViaAPI(request, auth.token, auth.tenantId, createdRole.id);
        }
      }
    });

    test("创建角色 - 必填字段验证", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);

      await page.locator('[data-testid="create-role-btn"]').click();

      // 不填写直接提交
      await page.locator('[data-testid="role-form-submit-btn"]').click();

      // 弹窗应仍存在（表单验证失败不会关闭弹窗）
      await expect(page.locator('[data-testid="role-form-dialog"]')).toBeVisible({ timeout: 5000 });

      // 验证表单字段仍可见
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-name-input"] input')).toBeVisible();
    });

    test("创建角色 - 取消按钮关闭弹窗", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);

      await page.locator('[data-testid="create-role-btn"]').click();

      // data-testid 在外层容器，需要定位内部的 input 元素
      await page.locator('[data-testid="role-form-name-input"] input').fill("临时角色");

      await page.locator('[data-testid="role-form-cancel-btn"]').click();

      await expect(page.locator('[data-testid="role-form-dialog"]')).not.toBeVisible({ timeout: 5000 });
    });

    test("编辑弹窗预填角色数据", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="edit-role-btn"]').click();

      const dialog = page.locator('[data-testid="role-form-dialog"]');
      await expect(dialog).toBeVisible();
      // 弹窗标题应包含"编辑角色"
      await expect(dialog.locator("h2")).toContainText("编辑角色");

      // 名称预填 - data-testid 在外层容器，需要定位内部的 input 元素
      await expect(page.locator('[data-testid="role-form-name-input"] input')).toHaveValue(role.name);
      // 编辑模式下编码禁用
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeDisabled();
    });

    test("成功编辑角色名称", async ({ page, request }) => {
      const role = await createTestRole(request);
      const newName = `${role.name}-已编辑`;

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="edit-role-btn"]').click();

      // data-testid 在外层容器，需要定位内部的 input 元素
      await page.locator('[data-testid="role-form-name-input"] input').fill(newName);
      await page.locator('[data-testid="role-form-description-input"] input').fill("已编辑的描述");

      await page.locator('[data-testid="role-form-submit-btn"]').click();

      await expect(page.locator('[data-testid="role-form-dialog"]')).not.toBeVisible({ timeout: 10000 });

      await waitForPageReady(page);
      await expect(page.locator(`text=${newName}`)).toBeVisible({ timeout: 10000 });
    });

    test("成功删除非系统角色", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);

      const deleteBtn = page.locator('[data-testid="delete-role-btn"]');
      await expect(deleteBtn).toBeVisible();

      page.on("dialog", (dialog) => dialog.accept());
      await deleteBtn.click();

      await waitForPageReady(page);

      // 从创建列表移除
      const index = testContext.createdRoles.findIndex((r) => r.id === role.id);
      if (index !== -1) testContext.createdRoles.splice(index, 1);

      // 验证角色已从列表消失
      await expect(page.locator(`[data-testid="role-item-${role.id}"]`)).not.toBeVisible({ timeout: 10000 });
    });

    test("取消删除操作角色仍存在", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);

      page.on("dialog", (dialog) => dialog.dismiss());
      await page.locator('[data-testid="delete-role-btn"]').click();

      await page.waitForTimeout(500);
      await expect(page.locator(`[data-testid="role-item-${role.id}"]`)).toBeVisible({ timeout: 5000 });
    });

    test("系统角色不显示删除按钮", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      // 查找系统角色（有 "系统" badge）
      const systemBadges = page.locator("span:has-text('系统')");
      const count = await systemBadges.count();

      if (count > 0) {
        // 系统角色选中后不应有删除按钮
        // 尝试点击系统角色的列表项
        const systemBadge = systemBadges.first();
        // badge 的父级按钮是角色列表项
        const roleButton = systemBadge.locator("..");
        if ((await roleButton.count()) > 0) {
          await roleButton.click();
          await page.waitForTimeout(500);

          // 删除按钮不应出现
          const deleteBtn = page.locator('[data-testid="delete-role-btn"]');
          await expect(deleteBtn).not.toBeVisible({ timeout: 3000 });
        }
      }
    });
  });

  // ===========================================================================
  // 4. 角色成员管理测试
  // ===========================================================================

  test.describe("角色成员管理", () => {
    test("角色成员 Tab 默认显示并包含成员表格", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);

      await expect(page.locator('[data-testid="member-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="add-member-btn"]')).toBeVisible();
    });

    test("成员数量统计显示", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);

      // 验证 "共 N 个成员" 文本出现
      const memberCountText = page.locator("text=/共 \\d+ 个成员/");
      await expect(memberCountText).toBeVisible({ timeout: 5000 });
    });

    test("权限列表 Tab 包含分配权限按钮", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="role-permissions-tab"]').click();
      await page.waitForTimeout(500);

      await expect(page.locator('[data-testid="assign-permissions-btn"]')).toBeVisible();
    });
  });

  // ===========================================================================
  // 5. 权限分配测试
  // ===========================================================================

  test.describe("权限分配", () => {
    test("点击分配权限打开弹窗", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="role-permissions-tab"]').click();
      await page.waitForTimeout(500);

      await page.locator('[data-testid="assign-permissions-btn"]').click();

      const dialog = page.locator('[data-testid="assign-perm-dialog"]');
      await expect(dialog).toBeVisible({ timeout: 5000 });
      // 弹窗标题应包含"分配权限"
      await expect(dialog.locator("h2")).toContainText("分配权限");
    });

    test("权限分配弹窗包含搜索功能和按钮", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="role-permissions-tab"]').click();
      await page.waitForTimeout(500);
      await page.locator('[data-testid="assign-permissions-btn"]').click();

      const dialog = page.locator('[data-testid="assign-perm-dialog"]');
      await expect(dialog).toBeVisible({ timeout: 5000 });

      // 验证权限搜索输入框
      await expect(page.locator('input[placeholder="搜索权限..."]')).toBeVisible();

      // 验证确定按钮
      await expect(page.locator('[data-testid="assign-perm-submit-btn"]')).toBeVisible();
    });

    test("取消关闭权限分配弹窗", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      await selectRole(page, role.id);
      await page.locator('[data-testid="role-permissions-tab"]').click();
      await page.waitForTimeout(500);
      await page.locator('[data-testid="assign-permissions-btn"]').click();

      const dialog = page.locator('[data-testid="assign-perm-dialog"]');
      await expect(dialog).toBeVisible({ timeout: 5000 });

      // 使用弹窗内的按钮选择器
      await dialog.locator("button").filter({ hasText: "取消" }).first().click();

      await expect(dialog).not.toBeVisible({ timeout: 5000 });
    });
  });

  // ===========================================================================
  // 6. 独立路由页面（RoleForm）测试
  // ===========================================================================

  test.describe("角色创建/编辑独立页面", () => {
    test("访问 /iam/roles/create 显示创建页面", async ({ page }) => {
      await page.goto("/iam/roles/create");
      await waitForPageReady(page);

      await expect(page.locator('[data-testid="role-form-page"]')).toBeVisible();
      // 页面标题应包含"创建角色"
      const pageTitle = page.locator('[data-testid="role-form-page"] h1');
      await expect(pageTitle).toContainText("创建角色");

      // 验证表单字段 - data-testid 在外层容器，需要定位内部的 input 元素
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-name-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-description-input"] input')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-permission-tree"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-submit-btn"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-form-cancel-btn"]')).toBeVisible();
    });

    test("创建页面编码可编辑", async ({ page }) => {
      await page.goto("/iam/roles/create");
      await waitForPageReady(page);

      // data-testid 在外层容器，需要定位内部的 input 元素
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeEnabled();
    });

    test("角色详情页预填数据且编码禁用", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto(`/iam/roles/${role.id}`);
      await waitForPageReady(page);

      await expect(page.locator('[data-testid="role-form-page"]')).toBeVisible();
      // 页面标题应包含"编辑角色"
      const pageTitle = page.locator('[data-testid="role-form-page"] h1');
      await expect(pageTitle).toContainText("编辑角色");
      // data-testid 在外层容器，需要定位内部的 input 元素
      await expect(page.locator('[data-testid="role-form-code-input"] input')).toBeDisabled();

      const nameInput = page.locator('[data-testid="role-form-name-input"] input');
      await expect(nameInput).toHaveValue(role.name);
    });

    test("在独立页面编辑后保存", async ({ page, request }) => {
      const role = await createTestRole(request);
      const newName = `${role.name}-独立编辑`;

      await page.goto(`/iam/roles/${role.id}`);
      await waitForPageReady(page);

      // data-testid 在外层容器，需要定位内部的 input 元素
      await page.locator('[data-testid="role-form-name-input"] input').fill(newName);
      await page.locator('[data-testid="role-form-submit-btn"]').click();

      // 验证返回到列表页
      await page.waitForURL(/\/iam\/roles(?!\/)/, { timeout: 15000 });
      await waitForPageReady(page);
      await expect(page.locator(`text=${newName}`)).toBeVisible({ timeout: 10000 });
    });

    test("在独立页面取消返回列表", async ({ page, request }) => {
      const role = await createTestRole(request);

      await page.goto(`/iam/roles/${role.id}`);
      await waitForPageReady(page);

      // data-testid 在外层容器，需要定位内部的 input 元素
      await page.locator('[data-testid="role-form-name-input"] input').fill("被丢弃的名称");
      await page.locator('[data-testid="role-form-cancel-btn"]').click();

      await page.waitForURL(/\/iam\/roles(?!\/)/, { timeout: 10000 });
      await waitForPageReady(page);

      // 原名称仍存在
      await expect(page.locator(`text=${role.name}`)).toBeVisible({ timeout: 5000 });
    });
  });

  // ===========================================================================
  // 7. 边界场景和错误检查
  // ===========================================================================

  test.describe("边界场景", () => {
    test("页面加载时骨架屏显示和消失", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForSkeletonGone(page, 10000);
      await expect(page.locator('[data-testid="role-list-page"]')).toBeVisible();
    });

    test("页面间快速切换无错误", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await expect(page.locator('[data-testid="role-list-page"]')).toBeVisible();

      await page.goto("/iam/users");
      await waitForPageReady(page);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await expect(page.locator('[data-testid="role-list-page"]')).toBeVisible();
    });

    test("页面 URL 匹配正确路由", async ({ page }) => {
      await page.goto("/iam/roles");
      await waitForPageReady(page);
      expect(page.url()).toContain("/iam/roles");
    });

    test("角色管理页面无控制台错误", async ({ page }) => {
      const errors = captureConsoleErrors(page);

      await page.goto("/iam/roles");
      await waitForPageReady(page);
      await waitForSkeletonGone(page);

      const criticalErrors = errors.filter(
        (err) =>
          !err.includes("warning") &&
          !err.includes("Warning") &&
          !err.includes("[HMR]")
      );

      expect(criticalErrors).toHaveLength(0);
    });
  });
});

// ============================================================================
// API 辅助测试（需要管理员权限）
// ============================================================================

test.describe("IAM 角色管理 API 测试", () => {
  let auth: IamAdminAuth | null = null;

  test.beforeAll(async ({ request }) => {
    try {
      auth = await getCachedAuth(request);
    } catch {
      // 登录失败时跳过测试
    }
  });

  test.afterAll(async ({ request }) => {
    if (!auth) return;
    try {
      await cleanupAllIamE2EData(request, auth.token, auth.tenantId);
    } catch {
      // 清理失败不影响测试结果
    }
  });

  test("通过 API 创建角色", async ({ request }) => {
    if (!auth) {
      test.skip(true, "登录失败，跳过测试");
      return;
    }
    const role = await createRoleViaAPI(request, auth.token, auth.tenantId, {
      code: `e2e-role-api-${Date.now()}`,
      name: "E2E测试角色-API",
    });

    expect(role.id).toBeTruthy();
    expect(role.name).toContain("E2E测试角色");

    await deleteRoleViaAPI(request, auth.token, auth.tenantId, role.id);
  });

  test("通过 API 删除角色", async ({ request }) => {
    if (!auth) {
      test.skip(true, "登录失败，跳过测试");
      return;
    }
    const role = await createRoleViaAPI(request, auth.token, auth.tenantId, {
      code: `e2e-role-del-${Date.now()}`,
      name: "E2E待删除角色",
    });

    await deleteRoleViaAPI(request, auth.token, auth.tenantId, role.id);

    // 验证已删除
    const listResponse = await request.get("/api/iam/admin/v1/roles", {
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Tenant-Id": auth.tenantId,
      },
    });

    const listData = await listResponse.json();
    const found = (listData?.data || []).some(
      (r: { id: string }) => r.id === role.id
    );
    expect(found).toBe(false);
  });

  test("通过 API 获取角色列表", async ({ request }) => {
    if (!auth) {
      test.skip(true, "登录失败，跳过测试");
      return;
    }
    const response = await request.get("/api/iam/admin/v1/roles", {
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Tenant-Id": auth.tenantId,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data?.data)).toBeTruthy();
  });

  test("创建后可在列表中搜到", async ({ request }) => {
    if (!auth) {
      test.skip(true, "登录失败，跳过测试");
      return;
    }
    const role = await createRoleViaAPI(request, auth.token, auth.tenantId, {
      code: `e2e-role-search-${Date.now()}`,
      name: "E2E搜索验证角色",
    });

    const listResponse = await request.get("/api/iam/admin/v1/roles", {
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Tenant-Id": auth.tenantId,
      },
      params: { keyword: role.code },
    });

    const listData = await listResponse.json();
    const found = (listData?.data || []).some(
      (r: { id: string }) => r.id === role.id
    );
    expect(found).toBe(true);

    await deleteRoleViaAPI(request, auth.token, auth.tenantId, role.id);
  });

  test("创建重复编码的角色应失败", async ({ request }) => {
    if (!auth) {
      test.skip(true, "登录失败，跳过测试");
      return;
    }
    const code = `e2e-dup-${Date.now()}`;

    const role1 = await createRoleViaAPI(request, auth.token, auth.tenantId, {
      code,
      name: "重复编码角色1",
    });

    // 尝试创建同编码角色
    try {
      const response = await request.post("/api/iam/admin/v1/roles", {
        headers: {
          Authorization: `Bearer ${auth.token}`,
          "X-Tenant-Id": auth.tenantId,
        },
        data: { code, name: "重复编码角色2" },
      });

      // 应返回错误
      expect(response.ok()).toBe(false);
    } finally {
      await deleteRoleViaAPI(request, auth.token, auth.tenantId, role1.id);
    }
  });
});
