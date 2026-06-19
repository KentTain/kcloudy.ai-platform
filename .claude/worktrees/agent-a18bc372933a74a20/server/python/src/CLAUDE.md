# Python 源码开发指南

本文件为 Claude Code 在 `server/python/src/` 源码目录中工作时提供指导。

## 目录定位

`src/` 按顶级模块组织源码。模块是 `src/{module}/`，功能是模块内的子域；不要把功能域提升为新的顶级目录。

## 顶级模块

| 模块 | 定位 | Schema | 详细文档 |
|------|------|--------|----------|
| framework | 底层基础设施模块 | - | [framework/CLAUDE.md](framework/CLAUDE.md) |
| tenant | 租户管理模块 | tenant | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| iam | 身份认证与权限模块 | iam | [iam/CLAUDE.md](iam/CLAUDE.md) |
| ai | AI 能力模块 | ai | [ai/CLAUDE.md](ai/CLAUDE.md) |
| demo | AI 助手平台演示模块 | demo | [demo/CLAUDE.md](demo/CLAUDE.md) |

## 依赖边界

```
demo / iam / ai ──▶ framework
demo / iam ──▶ tenant
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 `framework`
- `framework` 禁止依赖业务模块
- 可复用基础能力优先放入 `framework`

## 入口文件

| 文件 | 用途 |
|------|------|
| application_web.py | FastAPI Web 应用装配入口（动态模块扫描） |
| application_task.py | 定时任务调度器入口 |
| application_listener.py | 消息监听器入口 |

## 模块结构规范

每个业务模块必须包含：

```
src/{module}/
├── module.py           # 模块声明（必需）
├── app.py              # 独立应用工厂
├── models/
│   └── __init__.py     # 使用 create_module_base("{module}") 创建 Base
├── migrations/
│   └── env.py          # 配置 version_table_schema="{module}"
├── controllers/        # API 控制器
├── services/           # 业务逻辑层
└── schemas/            # Pydantic 模型
```

## 开发约束

- 新模块放在 `src/{module}/`，不要放在 `src/core/`、`src/common/` 等跨模块目录
- 必须在 `module.py` 实现 `ModuleDescriptor` 协议
- 必须使用 `create_module_base(schema)` 创建模块级 Base
- Controller 不直接写复杂业务逻辑
- Service 是主要业务逻辑入口
- Model 字段使用 SQLAlchemy 2.0 声明式类型：`Mapped[...] = mapped_column(...)`
- 跨模块数据引用不使用外键约束，改用应用层一致性检查
