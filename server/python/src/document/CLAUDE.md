# Document 模块开发指南

本文件为 Claude Code 在 `src/document/` 文档库管理模块中工作时提供指导。

## 模块定位

Document 模块负责企业知识库的文档管理，包括文件夹树、文件上传/下载、元数据管理、切片索引、回收站和资源权限。它是业务模块，可以依赖 framework 和 tenant 模块。

### 三层权限架构

Document 模块遵循三层权限架构，由 IAM 统一管控：

| 层级 | 说明 | 检查时机 |
|------|------|----------|
| IAM 角色权限 | 用户是否有 `document:file:read` 等模块权限 | 请求入口 |
| Document 资源权限 | 用户是否被授权访问特定文件夹/文件 | Service 层 |
| IAM Policy 策略 | 组织/租户级 deny 优先策略 | 策略求值器 |

AI 模块通过 `document/inner/v1/files/check-permission` inner 接口回查源文件权限，不放大权限。

## 依赖边界

```
document ──▶ framework（基础设施）
document ──▶ tenant（通过 inner 接口获取租户信息）
document ──▶ iam（通过 inner 接口获取权限、Policy 求值结果）
```

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 文件夹、文件、元数据、切片、回收站、资源权限等业务逻辑 |
| models/ | 文档库数据库模型与枚举 |
| schemas/ | 请求、响应等 Pydantic 模型 |
| migrations/ | 数据库迁移与种子数据 |
| listeners/ | 消息监听器（权限缓存失效等） |
| tasks/ | 定时任务（切片重建、回收站清理等） |

## 接口分层

Document 模块 API 路由遵循 `/{模块}/{类型}/v1/{功能}` 格式：

| 类型 | 路由前缀 | 用途 | 权限 |
|------|---------|------|------|
| admin | `/document/admin/v1/folders` | 管理后台文档管理 | JWT Token + 管理员权限 |
| console | `/document/console/v1/folders` | 用户端文档接口 | JWT Token |
| inner | `/document/inner/v1/files` | 内部接口，供模块间调用 | 无认证 |

### 完整路由表

#### 文件夹管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/document/console/v1/folders` | 获取文件夹列表 |
| POST | `/document/console/v1/folders` | 创建文件夹 |
| GET | `/document/console/v1/folders/{id}` | 获取文件夹详情 |
| PUT | `/document/console/v1/folders/{id}` | 更新文件夹 |
| DELETE | `/document/console/v1/folders/{id}` | 删除文件夹（移入回收站） |

#### 文件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/document/console/v1/files` | 获取文件列表 |
| POST | `/document/console/v1/files/upload` | 上传文件 |
| GET | `/document/console/v1/files/{id}` | 获取文件详情 |
| DELETE | `/document/console/v1/files/{id}` | 删除文件（移入回收站） |
| GET | `/document/console/v1/files/{id}/download` | 下载文件 |

#### 回收站

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/document/console/v1/trash` | 获取回收站列表 |
| POST | `/document/console/v1/trash/{id}/restore` | 恢复文件/文件夹 |
| DELETE | `/document/console/v1/trash/{id}` | 永久删除 |

#### inner 接口（供 AI 模块调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/document/inner/v1/files/check-permission` | 批量检查文件访问权限 |
| GET | `/document/inner/v1/files/{id}` | 内部接口：获取文件详情 |

## 数据库模型

| 模型 | 说明 | Schema |
|------|------|--------|
| Folder | 文件夹（树形结构） | document.folders |
| File | 文件实体 | document.files |
| FileMetadata | 文件元数据 | document.file_metadata |
| FileChunk | 文件切片索引 | document.file_chunks |
| ResourcePermission | 资源权限授权 | document.resource_permissions |
| TrashItem | 回收站条目 | document.trash_items |

## 核心能力

| 能力 | 说明 |
|------|------|
| 文件夹树 | 继承 `TreeNodeMixin`，支持多级文件夹 |
| 文件上传/下载 | 通过 framework storage 对接 MinIO/OSS |
| 元数据管理 | 文件标签、描述、分类等扩展信息 |
| 切片索引 | 文档切片与向量索引，供 AI RAG 检索 |
| 回收站 | 软删除 + 定时清理，支持恢复 |
| 资源权限 | 文件夹/文件级别授权，支持用户和角色授权 |

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- Folder 模型继承 `TreeNodeMixin`，树字段由 Mixin 自动维护
- 资源权限变更后发布 `PermissionCacheEvent` 失效缓存
- inner 接口不鉴权，但必须校验调用方身份（通过 header 或配置）

## 测试

```bash
uv run pytest tests/document/ -v
```
