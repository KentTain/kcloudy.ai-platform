# 用户角色权限前后端连接实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现前后端角色权限连接，使前端 `hasRole()` 和 `hasPermission()` 正确工作。

**架构：** 后端 `/me` 接口扩展返回 `roles` 和 `permissions` 数组；前端正确接收并存储到用户状态；更新路由和组件使用新角色名。

**技术栈：** Python/FastAPI/Pydantic (后端), TypeScript/Vue/Pinia (前端)

---

## 变更文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `server/python/src/iam/schemas/user.py` | 修改 | 扩展 UserVo 添加 roles/permissions |
| `server/python/src/iam/controllers/user_controller.py` | 修改 | /me 接口返回角色和权限 |
| `web/vue/src/iam/types/index.ts` | 修改 | User 类型添加 roles/permissions |
| `web/vue/src/iam/stores/auth.ts` | 修改 | convertToUserInfo 正确映射角色权限 |
| `web/vue/src/tenant/router/index.ts` | 修改 | 角色名 tenant_admin → admin |
| `web/vue/src/tenant/pages/tenants/TenantList.vue` | 修改 | hasRole 参数更新 |
| `web/vue/src/tenant/CLAUDE.md` | 修改 | 文档更新角色名 |

---

### 任务 1：扩展后端 UserVo 添加角色和权限字段

**文件：**
- 修改：`server/python/src/iam/schemas/user.py:132-150`
- 测试：`tests/iam/unit/test_user_vo.py`（新建）

- [ ] **步骤 1：编写失败的测试**

```python
# tests/iam/unit/test_user_vo.py
"""UserVo 角色权限字段测试"""

import pytest
from iam.schemas.user import UserVo


def test_user_vo_has_roles_and_permissions():
    """UserVo 应包含 roles 和 permissions 字段"""
    user_vo = UserVo(
        id="test-id",
        tenant_id="tenant-id",
        username="testuser",
        email="test@example.com",
        phone=None,
        nickname="Test User",
        avatar=None,
        status="active",
        profile_completed=True,
        is_email_verified=False,
        is_phone_verified=False,
        last_login_at=None,
        created_at="2024-01-01T00:00:00Z",
        roles=["admin", "viewer"],
        permissions=["iam:user:read", "iam:role:read"],
    )
    assert user_vo.roles == ["admin", "viewer"]
    assert user_vo.permissions == ["iam:user:read", "iam:role:read"]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/iam/unit/test_user_vo.py -v`
预期：FAIL，报错 "UserVo() got an unexpected keyword argument 'roles'"

- [ ] **步骤 3：编写最少实现代码**

```python
# server/python/src/iam/schemas/user.py
# 在 UserVo 类中添加两个字段（约第 148 行后）

class UserVo(BaseModel):
    """用户视图对象"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    username: str
    email: str | None
    phone: str | None
    nickname: str | None
    avatar: str | None
    status: str
    profile_completed: bool
    is_email_verified: bool
    is_phone_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    roles: list[str] = Field(default_factory=list, description="用户角色编码列表")
    permissions: list[str] = Field(default_factory=list, description="用户权限编码列表")
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/iam/unit/test_user_vo.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/schemas/user.py tests/iam/unit/test_user_vo.py
git commit -m "feat(iam): UserVo 添加 roles 和 permissions 字段"
```

---

### 任务 2：修改 /me 接口返回角色和权限

**文件：**
- 修改：`server/python/src/iam/controllers/user_controller.py:86-102`
- 测试：`tests/iam/unit/test_user_controller.py`（新建或修改现有）

- [ ] **步骤 1：编写失败的测试**

```python
# tests/iam/unit/test_user_controller.py（添加到现有文件或新建）
"""用户控制器测试 - /me 接口返回角色权限"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_get_current_user_returns_roles_and_permissions():
    """get_current_user 应返回用户的角色和权限"""

    # Mock user
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.tenant_id = "tenant-123"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.phone = None
    mock_user.nickname = "Test"
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.profile_completed = True
    mock_user.is_email_verified = False
    mock_user.is_phone_verified = False
    mock_user.last_login_at = None
    mock_user.created_at = "2024-01-01T00:00:00Z"

    # Mock services
    with patch("iam.controllers.user_controller.user_service.get_by_id", new_callable=AsyncMock) as mock_get_user:
        with patch("iam.controllers.user_controller.user_roles_service.get_user_roles", new_callable=AsyncMock) as mock_get_roles:
            with patch("iam.controllers.user_controller.permission_check_service.get_user_permissions", new_callable=AsyncMock) as mock_get_perms:
                mock_get_user.return_value = mock_user
                mock_get_roles.return_value = [MagicMock(code="admin"), MagicMock(code="viewer")]
                mock_get_perms.return_value = ["iam:user:read", "iam:role:read"]

                from iam.controllers.user_controller import get_current_user
                from fastapi.responses import ORJSONResponse

                result = await get_current_user("user-123")
                assert isinstance(result, ORJSONResponse)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/iam/unit/test_user_controller.py::test_get_current_user_returns_roles_and_permissions -v`
预期：FAIL 或功能未实现

- [ ] **步骤 3：修改 get_current_user 控制器**

```python
# server/python/src/iam/controllers/user_controller.py
# 找到 get_current_user 函数（约第 86 行），修改为：

@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)) -> ORJSONResponse:
    """
    获取当前用户信息

    返回当前登录用户的详细信息，包括角色和权限。
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取用户角色
    roles = await user_roles_service.get_user_roles(user_id)
    role_codes = [r.code for r in roles]

    # 获取用户权限
    permissions = await permission_check_service.get_user_permissions(user_id)

    # 构建响应
    user_vo = UserVo.model_validate(user)
    user_vo.roles = role_codes
    user_vo.permissions = permissions

    return ORJSONResponse(
        content={
            "code": 200,
            "msg": "success",
            "data": user_vo.model_dump(),
        }
    )
```

- [ ] **步骤 4：添加必要的导入**

```python
# server/python/src/iam/controllers/user_controller.py
# 在文件顶部的导入区域添加：

from iam.services import permission_check_service
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/iam/unit/test_user_controller.py -v`
预期：PASS

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/iam/controllers/user_controller.py tests/iam/unit/test_user_controller.py
git commit -m "feat(iam): /me 接口返回用户角色和权限"
```

---

### 任务 3：更新前端 User 类型定义

**文件：**
- 修改：`web/vue/src/iam/types/index.ts:1-35`

- [ ] **步骤 1：更新 User 接口添加 roles 和 permissions**

```typescript
// web/vue/src/iam/types/index.ts
// 找到 User 接口（约第 9-23 行），添加 roles 和 permissions：

// 用户类型
export interface User {
  id: string;
  tenant_id: string;
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  status: "active" | "inactive" | "locked";
  profile_completed: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  last_login_at?: string;
  created_at: string;
  roles: string[];        // 新增
  permissions: string[];  // 新增
}
```

- [ ] **步骤 2：验证类型检查通过**

运行：`cd web/vue && pnpm check`
预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/iam/types/index.ts
git commit -m "feat(iam): User 类型添加 roles 和 permissions 字段"
```

---

### 任务 4：修改前端 convertToUserInfo 正确映射角色权限

**文件：**
- 修改：`web/vue/src/iam/stores/auth.ts:18-26`

- [ ] **步骤 1：修改 convertToUserInfo 函数**

```typescript
// web/vue/src/iam/stores/auth.ts
// 找到 convertToUserInfo 函数（约第 18 行），修改为：

/**
 * 将 IAM User 转换为 Framework UserInfo
 */
const convertToUserInfo = (user: User): UserInfo => ({
  id: user.id,
  username: user.username,
  nickname: user.nickname || user.username,
  avatar: user.avatar,
  email: user.email,
  roles: user.roles || [],           // 使用后端返回的角色
  permissions: user.permissions || [], // 使用后端返回的权限
});
```

- [ ] **步骤 2：验证类型检查通过**

运行：`cd web/vue && pnpm check`
预期：无类型错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/iam/stores/auth.ts
git commit -m "fix(iam): convertToUserInfo 正确映射角色和权限"
```

---

### 任务 5：更新前端路由角色名

**文件：**
- 修改：`web/vue/src/tenant/router/index.ts:91,97,103,109`

- [ ] **步骤 1：批量替换路由中的角色名**

```typescript
// web/vue/src/tenant/router/index.ts
// 将所有 roles: ["tenant_admin"] 替换为 roles: ["admin"]

export const tenantRoutes: RouteRecordRaw[] = [
  {
    path: "tenants",
    name: "TenantManagement",
    component: () => import("@/tenant/pages/tenants/TenantList.vue"),
    meta: { title: "租户管理", icon: "tenant", requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/create",
    name: "TenantCreate",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "创建租户", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/:id",
    name: "TenantDetail",
    component: () => import("@/tenant/pages/tenants/TenantDetail.vue"),
    meta: { title: "租户详情", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/:id/edit",
    name: "TenantEdit",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "编辑租户", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
];
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/router/index.ts
git commit -m "refactor(tenant): 路由角色名 tenant_admin 改为 admin"
```

---

### 任务 6：更新 TenantList 组件角色检查

**文件：**
- 修改：`web/vue/src/tenant/pages/tenants/TenantList.vue:105-106`

- [ ] **步骤 1：修改 hasRole 参数**

```typescript
// web/vue/src/tenant/pages/tenants/TenantList.vue
// 找到第 105-106 行，修改为：

const canCreate = computed(() => frameworkUserStore.hasRole('admin'))
const canEdit = computed(() => frameworkUserStore.hasRole('admin'))
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/pages/tenants/TenantList.vue
git commit -m "refactor(tenant): hasRole 参数从 tenant_admin 改为 admin"
```

---

### 任务 7：更新 CLAUDE.md 文档

**文件：**
- 修改：`web/vue/src/tenant/CLAUDE.md:32-35,53`

- [ ] **步骤 1：更新文档中的角色名**

```markdown
## 路由配置

| 路径 | 组件 | 权限 |
|------|------|------|
| /tenants | TenantList | admin |
| /tenants/create | TenantForm | admin |
| /tenants/:id | TenantDetail | admin |
| /tenants/:id/edit | TenantForm | admin |

...

## 开发规则

- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架
- 权限检查使用 `frameworkUserStore.hasRole('admin')`
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/CLAUDE.md
git commit -m "docs(tenant): 更新角色名文档"
```

---

### 任务 8：集成测试验证

**文件：**
- 测试：手动测试

- [ ] **步骤 1：Rebuild 后端数据库**

运行：
```bash
cd server/python
uv run python manage.py db rebuild --module iam,tenant
```

预期：数据库重建成功，模块定义同步创建 admin/viewer 角色

- [ ] **步骤 2：启动后端服务**

运行：
```bash
cd server/python
uv run python manage.py runserver
```

- [ ] **步骤 3：启动前端服务**

运行：
```bash
cd web/vue
pnpm dev
```

- [ ] **步骤 4：验证登录流程**

1. 使用 admin/admin123 登录
2. 打开浏览器开发者工具，检查 `/api/v1/me` 响应
3. 验证响应中包含 `roles: ["admin"]` 和权限列表
4. 验证前端控制台无错误

- [ ] **步骤 5：验证权限检查**

1. 访问租户管理页面
2. 验证"新建租户"按钮可见
3. 验证编辑/删除按钮可见

---

## 变更摘要

| 组件 | 变更 |
|------|------|
| 后端 UserVo | 添加 `roles` 和 `permissions` 字段 |
| 后端 /me 接口 | 查询并返回用户角色和权限 |
| 前端 User 类型 | 添加 `roles` 和 `permissions` 字段 |
| 前端 convertToUserInfo | 使用后端返回的角色和权限 |
| 前端路由 | 角色名 `tenant_admin` → `admin` |
| 前端组件 | hasRole 参数更新 |

---

## 数据流

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   登录      │────▶│   /me API   │────▶│  前端 Store │
│             │     │             │     │             │
│ 获取 token  │     │ 返回 user + │     │ 存储 roles  │
│             │     │ roles/perms │     │ + perms     │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  hasRole()  │
                                        │  hasPerm()  │
                                        │             │
                                        │  正确工作!  │
                                        └─────────────┘
```
