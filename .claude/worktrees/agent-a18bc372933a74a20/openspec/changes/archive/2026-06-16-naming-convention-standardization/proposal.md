## 为什么

当前项目中前后端通信对象（DTO/类型）的命名缺乏统一规范：后端同时存在 `Vo`/`CreateRequest`/`Response` 等多种后缀，前端使用 `Params`/`QueryParams` 等非标准后缀。这导致开发者在不同模块间切换时产生认知负担，新成员需要额外学习成本。

本次变更为全项目统一命名规范，提升代码可读性和一致性。

## 变更内容

### 请求/参数类命名规范

| 操作 | 命名模式 | 示例 |
|------|----------|------|
| 查询（列表/分页） | `{Entity}Query` | `TenantQuery` |
| 新增（创建） | `{Entity}Create` | `TenantCreate` |
| 编辑（更新） | `{Entity}Update` | `TenantUpdate` |
| 保存（新增或编辑） | `{Entity}Save` | `ConfigSave` |
| 导入 | `{Entity}Import` | `UserImport` |
| 导出 | `{Entity}Export` | `UserExport` |

### 响应/返回类命名规范

| 类型 | 命名模式 | 示例 |
|------|----------|------|
| 基本类型 | `{Entity}Response` | `TenantResponse` |
| 列表响应 | `{Entity}ListResponse` | `TenantListResponse` |
| 树结构响应 | `{Entity}TreeResponse` | `ModuleMenuTreeResponse` |
| 属性/配置响应 | `{Entity}PropertyResponse` | `CachePropertyResponse` |

### 具体变更

- **BREAKING**: 后端 `*Vo` 统一重命名为 `*Response`
- **BREAKING**: 后端 `*CreateRequest`/`*UpdateRequest` 去掉 `Request` 后缀
- **BREAKING**: 前端 `Create*Params`/`Update*Params`/`*QueryParams` 统一使用标准后缀
- 更新 `server/CLAUDE.md` 和 `web/CLAUDE.md` 记录新规范
- 更新所有引用旧类名的 API 函数、Store、页面

## 功能 (Capabilities)

### 新增功能
- `naming-convention`: 统一定义前后端通信对象命名规范，记录在 CLAUDE.md

### 修改功能
<!-- 无已有规范变更 -->

## 影响

- **后端文件**: `server/python/src/tenant/schemas/`、`server/python/src/iam/schemas/`、`server/python/src/demo/schemas/`
- **前端文件**: `web/vue/src/tenant/types/`、`web/vue/src/iam/types/`、`web/vue/src/demo/types/` 及对应 API/Store/Pages
- **文档**: `server/CLAUDE.md`、`web/CLAUDE.md`
- **兼容性**: 纯重命名变更，不涉及业务逻辑修改，但需更新所有引用处
