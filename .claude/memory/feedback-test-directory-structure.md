---
name: feedback-test-directory-structure
description: 测试目录分层规范（以 demo 模块为例）
metadata:
  type: feedback
---

测试目录按功能模块组织，每个模块下包含 fixtures（测试数据）、unit（单元测试）、integration（集成测试）三个子目录。

**Why:** 清晰的测试目录结构便于定位测试代码，fixtures 集中管理测试数据，unit/integration 分离测试类型。

**How to apply:**

以 `tests/demo/` 为例：

```
tests/demo/
├── fixtures/                # 测试夹具和数据
│   ├── data/               # 测试数据文件（JSON/YAML）
│   │   ├── dataset.json    # 数据集测试数据
│   │   └── tenant.json     # 租户测试数据
│   └── helpers.py          # 测试辅助函数
│
├── unit/                   # 单元测试（使用mock隔离依赖）
│   ├── cache/             # Redis缓存测试
│   ├── config/            # 配置管理测试
│   ├── model/             # Pydantic模型测试
│   ├── services/          # 服务层测试
│   └── utils/             # 工具函数测试
│
└── integration/            # 集成测试（真实服务交互）
    ├── test_tenant_api.py # API集成测试
    └── test_tenant_isolation.py # 数据库集成测试
```

1. **fixtures/data/**：存放 JSON/YAML 格式的测试数据，按业务实体命名
2. **fixtures/helpers.py**：提供数据生成、Mock工具、断言辅助等函数
3. **unit/**：每个源码目录对应一个测试目录，测试文件命名为 `test_*.py`
4. **integration/**：跨组件测试放在模块根目录的 integration/ 下
