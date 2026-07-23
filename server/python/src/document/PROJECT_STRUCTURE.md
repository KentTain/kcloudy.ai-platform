# Document 模块项目结构

## 后端模块结构

```text
server/python/src/document/
├── __init__.py                    # 模块初始化
├── models/                        # 数据库模型
│   └── __init__.py
├── schemas/                       # DTO 模型
│   └── __init__.py
├── services/                      # 业务逻辑层
│   └── __init__.py
├── controllers/                   # API 控制器
│   ├── __init__.py
│   ├── admin/                     # 管理端 API
│   ├── console/                   # 用户端 API
│   └── inner/                     # 内部接口
├── migrations/                    # 数据库迁移
│   ├── versions/                  # 迁移版本
│   └── seeds/                     # 种子数据
├── listeners/                     # 消息监听器
│   ├── setup.py                   # 生命周期管理
│   └── services/
│       ├── pubsub/                # PubSub 处理器
│       └── queue/                 # Queue 处理器
├── tasks/                         # 定时任务
│   ├── setup.py                   # 调度器管理
│   └── services/                  # 任务函数
├── middlewares/                   # 模块级中间件
├── utils/                         # 工具函数
└── common/                        # 模块公共定义
```

## 前端模块结构

```text
web/vue/src/document/
├── index.ts                       # 模块入口
├── types/                         # 类型定义
│   └── index.ts
├── api/                           # API 函数
│   └── index.ts
├── stores/                        # 状态管理
│   └── index.ts
├── composables/                   # 组合式函数
│   └── index.ts
├── router/                        # 路由配置
│   └── index.ts
├── pages/                         # 页面组件
└── components/                    # 模块专用组件
```

## 测试目录结构

```text
web/vue/tests/document/
├── unit/                          # 单元测试
│   ├── stores/
│   └── composables/
└── e2e/                           # E2E 测试
```

## 核心功能模块

### 文档库管理
- 个人和团队文档库
- 文件夹和文件管理
- 成员和权限管理

### 知识库管理
- 知识库 CRUD
- 文档入库管理
- 检索测试

### 入库审核
- 入库申请提交
- 审核流程管理
- 站内消息通知

### 智能问答
- 跨知识库检索
- 引用追溯
- 问答反馈

### 组织与标签
- 组织架构管理
- 标签管理
- 权限依赖关系
