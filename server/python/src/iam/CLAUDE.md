# IAM 模块开发指南

本文件为 Claude Code 在 `src/iam/` 身份认证与权限模块中工作时提供指导。

## 模块定位

IAM（Identity and Access Management）负责用户认证、角色、权限、组织架构和 OAuth 连接。它是业务模块，可以依赖 framework 和 tenant 模块。

## 依赖边界

```
IAM ──▶ framework（基础设施）
IAM ──▶ tenant（通过 inner 接口获取租户信息）
```

## 目录职责

| 目录 | 职责 |
|------|------|
| controllers/ | FastAPI 路由控制器（admin/console/inner 三层） |
| services/ | 认证、用户、部门、角色、权限、OAuth 业务逻辑 |
| models/ | IAM 数据库模型与枚举 |
| schemas/ | 请求、响应、Token、登录等 Pydantic 模型 |
| migrations/ | IAM 数据库迁移与种子数据 |

## 接口分层

| 前缀 | 用途 | 权限 |
|------|------|------|
| /admin/v1/users | 管理后台用户管理 | 系统管理员 |
| /console/v1/users | 用户端接口（个人中心） | 登录用户 |
| /inner/v1/users | 内部接口，供模块间调用 | 无 |

## 核心能力

| 能力 | 说明 |
|------|------|
| 用户认证 | 登录、密码验证、JWT 令牌 |
| 权限控制 | 基于角色的访问控制 |
| 组织架构 | 部门、用户、用户租户关系管理 |
| OAuth 集成 | 第三方 OAuth 连接与用户同步 |

## 数据库模型

| 模型 | 说明 | Schema |
|------|------|--------|
| User | 用户实体 | iam.users |
| Role | 角色 | iam.roles |
| Permission | 权限 | iam.permissions |
| Department | 部门 | iam.departments |
| UserRole | 用户-角色关联 | iam.user_roles |
| UserTenant | 用户-租户关联 | iam.user_tenants |

## 开发规则

- Controller 只处理路由、参数校验、鉴权依赖和响应封装
- Service 负责事务边界、业务校验和跨模型协作
- Department 模型继承 `TreeNodeMixin`，树字段由 Mixin 自动维护

## 测试

```bash
uv run pytest tests/iam/ -v
```
