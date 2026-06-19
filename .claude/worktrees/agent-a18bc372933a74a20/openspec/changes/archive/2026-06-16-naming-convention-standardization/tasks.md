## 1. 更新文档规范

- [x] 1.1 更新 `server/CLAUDE.md` Schema 类命名规范表
- [x] 1.2 更新 `web/CLAUDE.md` 新增前端类型命名规范

## 2. 后端 Schema 重命名

- [x] 2.1 重命名 tenant 模块 schema（TenantVo→Response、*CreateRequest→Create 等）
- [x] 2.2 重命名 tenant/resource_config schema（*ConfigResponse→*PropertyResponse）
- [x] 2.3 重命名 iam 模块 schema（UserVo→Response、LoginVo→LoginResponse 等）
- [x] 2.4 重命名 demo 模块 schema（DatasetVo→DatasetResponse）

## 3. 后端引用更新

- [x] 3.1 更新 tenant 模块控制器、services 中的旧类名引用
- [x] 3.2 更新 iam 模块控制器、services 中的旧类名引用
- [x] 3.3 更新 demo 模块控制器中的旧类名引用

## 4. 前端类型重命名

- [x] 4.1 重命名 tenant 模块类型（Params→标准后缀）
- [x] 4.2 重命名 iam 模块类型（Params→标准后缀）
- [x] 4.3 重命名 demo 模块类型（Params→标准后缀）

## 5. 前端引用更新

- [x] 5.1 更新 tenant 模块 API 函数、Store、Pages 中的类型引用
- [x] 5.2 更新 iam 模块 API 函数、Store、Pages 中的类型引用
- [x] 5.3 更新 demo 模块 API 函数、Store、Pages 中的类型引用

## 6. 验证

- [x] 6.1 运行后端 Ruff 检查和 pytest 验证
- [x] 6.2 运行前端 pnpm check 和类型检查验证
