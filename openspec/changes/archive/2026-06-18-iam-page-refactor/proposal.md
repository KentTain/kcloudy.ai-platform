## 为什么

现有 IAM 模块的部门管理、人员管理、账户管理、权限管理、角色管理五个页面功能简陋、布局落后（平铺表格、无组织树交互、无 Tabs 详情面板、无人员选择器），参照 kbhub 项目对应页面的成熟交互模式进行全面改造，使页面达到生产可用水平。同时后端 API 存在多处接口缺失（批量操作、按部门筛选、统计聚合等），需要先补全后端接口再改造前端。

## 变更内容

- 重写部门管理页面（DepartmentPage.vue）：左侧 300px 组织树 + 右侧 Tabs（组织信息、下级组织、直属成员）
- 重写人员管理页面（UserList.vue）：顶部统计卡片 + 左侧部门树筛选 + 右侧带多条件筛选的人员表格
- 重写账户管理页面（Profile.vue）：头像展示 + Tabs（个人信息、安全设置）+ 密码修改弹窗
- 重写权限管理页面（PermissionList.vue）：左右布局 + Tabs（角色列表、菜单列表）
- 重写角色管理页面（RoleList.vue）：左侧角色列表 + 右侧 Tabs（角色成员、权限列表）
- 新增通用人员选择器组件 PeopleSelectDialog（含组织树、三态复选、搜索、懒加载）
- 新增部门创建/编辑弹窗 CreateDepartmentDialog
- 新增用户创建/编辑弹窗 UserFormDialog
- 补全后端 API：部门批量操作、按部门筛选用户、用户统计、角色成员管理、菜单分配等
- 更新前端 API 函数和 TypeScript 类型定义以对齐新增后端接口

## 功能 (Capabilities)

### 新增功能
- `people-select-dialog`: 通用人员选择器弹窗组件（组织树+三态复选+搜索+懒加载），放置于 src/components/common/
- `department-form-dialog`: 部门创建/编辑弹窗组件
- `user-form-dialog`: 用户创建/编辑弹窗组件（含角色分配 Checkbox）
- `iam-department-page-refactor`: 部门管理页面改造（左右布局+Tabs 详情面板+搜索高亮+骨架屏）
- `iam-user-list-refactor`: 人员管理页面改造（统计卡片+部门树筛选+多条件搜索+行内操作）
- `iam-profile-refactor`: 账户管理页面改造（头像+Tabs 布局+密码修改弹窗）
- `iam-permission-page-refactor`: 权限管理页面改造（左右布局+角色/菜单 Tabs）
- `iam-role-page-refactor`: 角色管理页面改造（左列表+右侧成员/权限 Tabs）

### 修改功能
- `iam-api`: 后端 API 补充（部门批量成员操作、用户统计、按部门筛选、角色成员管理、菜单分配接口）
- `iam-types`: 前端 TypeScript 类型定义更新（对齐新增后端接口响应字段）

## 影响

- **前端页面**：DepartmentPage.vue、UserList.vue、Profile.vue、PermissionList.vue、RoleList.vue 全部重写
- **前端组件**：新增 PeopleSelectDialog、CreateDepartmentDialog、UserFormDialog 等组件
- **前端 API**：iam/api/ 下的 user.ts、department.ts、role.ts、menu.ts 需新增接口函数
- **前端类型**：iam/types/index.ts 需新增类型定义（UserStats、RoleOption、DepartmentDetail 等）
- **后端控制器**：iam/controllers/admin/ 下的 department_controller.py、user_controller.py、role_controller.py、menu_controller.py 需新增端点
- **后端服务**：iam/services/ 下的 department_service.py、user_service.py、role_service.py 需新增方法
- **后端 Schema**：iam/schemas/ 需新增请求/响应模型
- **数据库**：无结构变更，仅需补充查询逻辑
- **依赖**：前端需确认 vee-validate + zod 已安装；后端无新依赖