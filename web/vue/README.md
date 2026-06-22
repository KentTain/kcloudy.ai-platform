# AI Platform Web Frontend (Vue)

AI Platform AI 助手平台前端应用（Vue 版本），基于 Vue 3 + TypeScript + Vite 构建。

## 技术栈

- **框架**: Vue 3.5 + TypeScript 5.8
- **构建工具**: Vite 6.x
- **路由**: Vue Router 4.x
- **状态管理**: Pinia 3.x
- **UI 组件库**: shadcn-vue
- **无样式原语**: Radix Vue
- **样式**: Tailwind CSS v4
- **HTTP 客户端**: Axios
- **代码质量**: Biome
- **测试**: Vitest + @vue/test-utils

## 环境要求

- Node.js >= 22.0.0
- pnpm >= 10.0.0

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 生产构建
pnpm build

# 预览生产构建
pnpm preview

# 类型检查
pnpm type-check

# 代码检查和格式化
pnpm check          # 检查
pnpm check:fix      # 检查并自动修复

# 测试
pnpm test:unit              # 运行测试（监听模式）
pnpm test:unit -- --run     # 运行一次
pnpm test:unit -- --coverage # 运行并生成覆盖率报告
```

## 项目结构

```text
web/vue/
├── src/                       # 源码目录
│   ├── demo/                  # Demo 业务模块
│   ├── framework/             # Framework UI框架模块
│   ├── components/            # 通用组件
│   │   └── ui/                # shadcn-vue 组件
│   ├── composables/           # 组合式函数
│   ├── App.vue                # 根组件
│   └── main.ts                # 应用入口
├── tests/                     # 测试目录
│   ├── demo/                  # Demo 模块测试
│   └── framework/             # Framework 模块测试
├── public/                    # 静态文件
├── biome.jsonc                # Biome 配置
├── vite.config.ts             # Vite 配置
├── vitest.config.ts           # Vitest 测试配置
├── tsconfig.json              # TypeScript 配置
└── package.json               # 项目配置
```

## 开发说明

### 登录用户信息获取

项目中经常需要获取当前登录用户的详细信息（用户信息、角色、权限、菜单等）。以下是标准用法：

#### 普通用户信息

**数据来源**：`/iam/console/v1/users/me` 接口

**状态管理**：`framework/stores/user.ts` → `useUserStore()`

**使用示例**：

```typescript
import { useUserStore } from '@/framework/stores'

const userStore = useUserStore()

// 获取用户基本信息
const userId = userStore.userInfo?.id
const username = userStore.userInfo?.username
const nickname = userStore.userInfo?.nickname

// 权限检查
const canEdit = userStore.hasPermission('demo:dataset:write')
const isAdmin = userStore.hasRole('admin')

// 当前租户信息
const currentTenant = userStore.currentTenant
const tenantId = userStore.userInfo?.tenantId

// 租户列表
const tenants = userStore.tenants
```

**返回数据结构**：

```typescript
interface UserInfo {
  id: string
  username: string
  nickname: string
  avatar?: string
  email?: string
  phone?: string
  roles: string[]          // 角色编码列表
  permissions: string[]    // 权限编码列表
  tenantId?: string
  tenantName?: string
  tenantCode?: string
  tenants?: TenantInfo[]   // 用户所属租户列表
}
```

#### 管理员信息

**数据来源**：`/tenant/admin/v1/admin/me` 接口

**状态管理**：`tenant/stores/adminAuth.ts` → `useAdminAuthStore()`

**使用示例**：

```typescript
import { useAdminAuthStore } from '@/tenant/stores/adminAuth'

const adminAuthStore = useAdminAuthStore()

// 获取管理员基本信息
const adminId = adminAuthStore.adminInfo?.id
const username = adminAuthStore.username

// 权限检查（支持通配符）
const canManage = adminAuthStore.hasPermission('tenant:module:write')
const isSuperAdmin = adminAuthStore.hasPermission('*:*:*')  // 超级管理员

// 角色检查
const isDefaultAdmin = adminAuthStore.hasRole('superAdmin')

// 菜单数据（登录时已获取）
const menus = adminAuthStore.menus
```

**返回数据结构**：

```typescript
interface AdminInfo {
  id: string
  username: string
  role: string              // 角色编码
  permissions: string[]     // 权限编码列表
  menus: AdminMenuItem[]    // 菜单树
  is_default: boolean
  is_active: boolean
}
```

#### 菜单数据

菜单数据在登录时从 `/me` 接口一并获取，无需额外请求。

**普通用户菜单**：

```typescript
import { useMenuStore } from '@/framework/stores/menu'

const menuStore = useMenuStore()
const menus = menuStore.userMenus  // 用户导航菜单
```

**管理员菜单**：

```typescript
import { useAdminMenuStore } from '@/tenant/stores/adminMenu'

const adminMenuStore = useAdminMenuStore()
const menus = adminMenuStore.adminMenus  // 管理员菜单树
```

#### 数据流说明

```
登录流程：
1. 调用登录接口 → 获取 token
2. 调用 /me 接口 → 获取用户信息 + 菜单数据
3. 存储到 Pinia Store + localStorage

页面刷新：
1. 路由守卫检测到 token 存在但 userInfo 为空
2. 自动调用 /me 接口恢复用户信息 + 菜单数据
```

### API 代理

开发服务器配置了 API 代理，所有 `/api` 和 `/health` 请求会被转发到 `http://127.0.0.1:8000`。

确保后端服务在 8000 端口运行后，即可进行前后端联调。

## 测试

项目使用 Vitest 进行单元测试，测试文件位于 `tests/` 目录。

详细测试说明见 [tests/CLAUDE.md](tests/CLAUDE.md)。

## 开发指南

详细开发指南见 [CLAUDE.md](CLAUDE.md)。

## 推荐的 IDE 设置

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

## License

Copyright © 2025 Moles. All Rights Reserved.
