## 1. 基础设施 - API 辅助登录

- [x] 1.1 重构 `tests/tenant/e2e/fixtures.ts`，实现 `adminLoginViaAPI()` 函数
- [x] 1.2 实现 `userLoginViaAPI()` 函数，支持 IAM 用户端登录
- [x] 1.3 定义 Token 存储常量（`ADMIN_TOKEN_KEY` 等），与源码保持一致
- [x] 1.4 添加错误处理和明确的异常消息

## 2. 基础设施 - 测试数据管理

- [x] 2.1 实现 `createTenantViaAPI()` 和 `deleteTenantViaAPI()` 辅助函数
- [x] 2.2 实现 `createModuleViaAPI()` 和 `deleteModuleViaAPI()` 辅助函数
- [x] 2.3 实现 `createUserViaAPI()` 和 `deleteUserViaAPI()` 辅助函数
- [x] 2.4 实现 `cleanupAllE2EData()` 批量清理函数
- [x] 2.5 编写数据辅助函数的单元测试（22 个测试用例）

## 3. 基础设施 - 缺失检测脚本

- [x] 3.1 创建 `scripts/e2e-check-coverage.ts` 脚本
- [x] 3.2 实现登录获取 Token 的逻辑
- [x] 3.3 实现从 `/me` 接口获取菜单数据
- [x] 3.4 实现扫描 `tests/**/*.spec.ts` 文件并提取测试名称
- [x] 3.5 实现菜单与测试覆盖对比分析逻辑
- [x] 3.6 实现生成 `docs/tests/test-lose-item-{date}.md` 报告
- [x] 3.7 在 `package.json` 中添加 `test:coverage:check` 脚本命令

## 4. Tenant 模块 - 冒烟测试

- [x] 4.1 创建 `tests/tenant/e2e/smoke.spec.ts`
- [x] 4.2 实现菜单遍历测试（访问所有可见菜单路径）
- [x] 4.3 实现页面基础渲染验证（骨架屏消失、内容可见）
- [x] 4.4 实现统计卡片渲染验证
- [x] 4.5 实现资源配置页面 Tab 切换验证

## 5. Tenant 模块 - 登录页面测试

- [x] 5.1 创建独立的 `tests/tenant/e2e/login.spec.ts`，保留 UI 登录测试
- [x] 5.2 验证 UI 登录成功流程
- [x] 5.3 验证 UI 登录失败流程（错误提示显示）

## 6. Tenant 模块 - 租户管理 CRUD

- [x] 6.1 创建 `tests/tenant/e2e/tenants-crud.spec.ts`
- [x] 6.2 为 `TenantList.vue` 添加 `data-testid` 属性（16 个）
- [x] 6.3 为 `TenantForm.vue` 添加 `data-testid` 属性（10 个）
- [x] 6.4 为 `TenantDetail.vue` 添加 `data-testid` 属性（9 个）
- [x] 6.5 实现租户列表加载测试
- [x] 6.6 实现创建租户测试（表单填写、提交、验证）
- [x] 6.7 实现编辑租户测试
- [x] 6.8 实现删除租户测试
- [x] 6.9 实现搜索租户测试
- [x] 6.10 实现统计数据验证测试

## 7. Tenant 模块 - 资源配置 CRUD

> **实现说明**：合并为统一的 `resources-crud.spec.ts`，通过 Tab 切换覆盖全部 5 种资源类型。

- [x] 7.1 创建 `tests/tenant/e2e/resources-crud.spec.ts`（统一测试文件）
- [x] 7.2 为 `ResourceConfigList.vue` 添加 `data-testid`（19 个）
- [x] 7.3 实现数据库配置列表加载测试
- [x] 7.4 实现数据库配置 CRUD 测试
- [x] 7.5 实现存储配置 CRUD 测试
- [x] 7.6 实现缓存配置 CRUD 测试
- [x] 7.7 实现队列配置 CRUD 测试
- [x] 7.8 实现发布订阅配置 CRUD 测试

## 8. Tenant 模块 - 模块管理 CRUD

- [x] 8.1 创建 `tests/tenant/e2e/modules-crud.spec.ts`
- [x] 8.2 为 `ModuleList.vue` 添加 `data-testid`（7 个）
- [x] 8.3 为 `ModuleForm.vue` 添加 `data-testid`（11 个）
- [x] 8.4 为 `ModuleDetail.vue` 添加 `data-testid`（6 个）
- [x] 8.5 实现模块列表加载测试
- [x] 8.6 实现创建模块测试
- [x] 8.7 实现编辑模块测试
- [x] 8.8 实现删除模块测试
- [x] 8.9 实现模块详情查看测试（Tabs 切换）
- [x] 8.10 实现搜索筛选测试

## 9. IAM 模块 - 基础设施

- [x] 9.1 创建 `tests/iam/e2e/fixtures.ts`
- [x] 9.2 实现 IAM 用户端 API 辅助登录（复用 `userLoginViaAPI`）
- [x] 9.3 实现测试数据管理辅助函数（角色/组织/用户 CRUD）

## 10. IAM 模块 - 冒烟测试

- [x] 10.1 创建 `tests/iam/e2e/smoke.spec.ts`
- [x] 10.2 实现菜单遍历测试
- [x] 10.3 实现页面基础渲染验证

## 11. IAM 模块 - 组织管理测试

- [x] 11.1 创建 `tests/iam/e2e/organizations.spec.ts`
- [x] 11.2 为 `OrganizationPage.vue` 添加 `data-testid`（25 个）
- [x] 11.3 实现组织树渲染测试
- [x] 11.4 实现组织详情展示测试
- [x] 11.5 实现新增/编辑/删除组织测试
- [x] 11.6 实现组织成员管理测试

## 12. IAM 模块 - 角色管理测试

- [x] 12.1 创建 `tests/iam/e2e/roles.spec.ts`
- [x] 12.2 为 `RoleList.vue`（20 个）和 `RoleForm.vue`（7 个）添加 `data-testid`
- [x] 12.3 实现角色列表渲染测试
- [x] 12.4 实现角色 CRUD 测试
- [x] 12.5 实现角色权限分配测试

## 13. IAM 模块 - 用户管理测试

- [x] 13.1 创建 `tests/iam/e2e/users.spec.ts`
- [x] 13.2 为 `UserList.vue`、`UserForm.vue`、`UserDetail.vue` 添加 `data-testid`
- [x] 13.3 实现用户列表渲染测试
- [x] 13.4 实现用户 CRUD 测试
- [x] 13.5 实现用户状态管理测试
- [x] 13.6 实现用户角色分配测试
- [x] 13.7 实现重置密码测试

## 14. IAM 模块 - 菜单管理测试

- [x] 14.1 创建 `tests/iam/e2e/menus.spec.ts`
- [x] 14.2 为 `MenuList.vue` 添加 `data-testid`（11 个）
- [x] 14.3 实现菜单树渲染测试
- [x] 14.4 实现菜单详情展示测试

## 15. IAM 模块 - 权限管理测试

- [x] 15.1 创建 `tests/iam/e2e/permissions.spec.ts`
- [x] 15.2 为 `PermissionList.vue` 添加 `data-testid`（20 个）
- [x] 15.3 实现权限列表渲染测试
- [x] 15.4 实现权限关联展示测试

## 16. 集成与验证

- [x] 16.1 运行完整测试套件，确保所有测试通过（需后端服务运行）
- [x] 16.2 运行缺失检测脚本，验证报告生成（需后端服务运行）
- [x] 16.3 更新 `tests/CLAUDE.md` 和 `tests/README.md` 文档
- [x] 16.4 编写测试运行指南（`tests/README.md`）
