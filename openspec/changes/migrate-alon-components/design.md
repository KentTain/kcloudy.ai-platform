## 上下文

本项目 AI 模块（`server/python/src/ai/components/`）目前仅有 model、plugin 两个组件。Alon 项目（`D:\Project\ai\Alon`）中有 4 个成熟的 AI 组件可供迁移，且这些组件在 Alon 内部已是高内聚、低耦合的设计：

- **encryption**：10 个文件，仅依赖配置模型
- **datasource**：15 个文件，仅依赖一个异常类
- **code_executor**：13 个文件，仅依赖配置注入
- **graphrag**：457 个文件，完全自包含（微软 GraphRAG 改造版）

**关键约束**：
- 本项目使用 langchain 1.3.0 + langgraph 1.2.0（Alon 使用 langchain 0.3.27 + langgraph 0.6.0）
- graphrag 不依赖 langchain/langgraph，版本差异无影响
- 本项目 framework 模块已有 database、storage、cache、pubsub、lock 基础设施

## 目标 / 非目标

**目标：**
- 迁移 4 个组件至本项目，保持功能完整性
- 适配本项目的配置体系和异常体系
- 补齐各组件的单元测试
- 添加 sandbox 服务至 Docker Compose

**非目标：**
- 不迁移 retriever 组件（强 ORM 耦合）
- 不修改组件核心业务逻辑
- 不新增 HTTP 端点（本次仅迁移组件能力）

## 决策

### D1: 配置适配策略

**决策**：将 Alon 的 `alon.configs.infrastructure.encryption.EncryptionSettings` 迁移至本项目 `framework/configs/` 目录，保持 Pydantic 模型结构不变。

**理由**：
- 本项目 framework 已有 configs 模块，基础设施配置应统一管理
- Alon 的配置模型继承自 `pydantic_settings.BaseSettings`，与本项目一致
- 迁移配置模型比修改组件代码更简单

**替代方案**：
- 直接在组件内定义配置（拒绝理由：破坏配置集中管理原则）

### D2: 异常类适配策略

**决策**：在 `framework/common/exceptions.py` 中添加 `BadRequestError` 异常类，供 datasource 组件使用。

**理由**：
- 本项目已有异常体系框架
- 仅需补充一个异常类，改动最小

### D3: 导入路径重写策略

**决策**：使用字符串替换批量重写导入路径：
- `alon.components.X` → `ai.components.X`
- `alon.configs.infrastructure.encryption` → `framework.configs.encryption`
- `alon.common.exceptions` → `framework.common.exceptions`

**理由**：
- 4 个组件共约 495 个文件，手动修改易遗漏
- 字符串替换可验证、可回滚

### D4: 单元测试策略

**决策**：为每个组件创建独立测试目录，按功能模块划分测试文件：

```
tests/ai/unit/components/
├── encryption/
│   ├── test_aes_encryption.py
│   ├── test_rsa_encryption.py
│   └── test_encryption_manager.py
├── datasource/
│   ├── test_base_connector.py
│   └── test_rdbms_connectors.py
├── code_executor/
│   ├── test_code_executor.py
│   └── test_template_transformers.py
└── graphrag/
    ├── test_client.py
    └── test_llm_base.py
```

**理由**：
- 遵循本项目现有测试结构
- 各组件独立，便于并行开发和测试

### D5: Sandbox 服务配置

**决策**：在 `docker/docker-compose.backend.yml` 添加 sandbox 服务，使用 `langgenius/dify-sandbox:0.2.12` 镜像。

**配置要点**：
- 容器名：`kcloudy-sandbox`
- 端口：8194
- 网络：`kcloudy-network`
- 去掉 Alon 原有的 ssrf_proxy 配置（本项目不需要）

## 风险 / 权衡

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 外部包版本冲突 | 低 | 中 | 先检查 pyproject.toml，缺失包使用最新稳定版 |
| 配置注入时机错误 | 低 | 高 | encryption 需在应用启动时初始化，验证 startup 事件 |
| graphrag 体量大导致 IDE 卡顿 | 中 | 低 | 可考虑拆分为子包，但本次保持完整迁移 |
| sandbox 服务网络隔离 | 低 | 中 | 确保 sandbox 与 backend 在同一 Docker 网络 |

## 迁移计划

### Phase 1: 基础设施准备
1. 创建 `framework/configs/encryption.py` — 加密配置模型
2. 补充 `framework/common/exceptions.py` — BadRequestError
3. 更新 `pyproject.toml` — 添加 pycryptodome、datashaper、tiktoken 等依赖
4. 更新 `docker/docker-compose.backend.yml` — 添加 sandbox 服务

### Phase 2: 组件迁移（按依赖顺序）
1. **encryption** — 10 文件，无依赖，最先迁移
2. **datasource** — 15 文件，依赖 exceptions
3. **code_executor** — 13 文件，依赖配置
4. **graphrag** — 457 文件，自包含，最后迁移

### Phase 3: 测试补齐
1. 为每个组件编写单元测试
2. 验证 sandbox 服务连通性
3. 验证加密配置加载正确

## 开放问题

1. **graphrag 的 Web 服务端点**：graphrag 组件内含 webserver 子模块，是否需要暴露 HTTP 端点？如需要，应在哪个 API 路径下？
   - **建议**：本次暂不暴露，后续如有需要再通过 `/api/v1/graphrag/` 暴露

2. **encryption 配置热更新**：是否需要支持运行时热更新加密密钥？
   - **建议**：暂不支持，密钥变更需要重启服务
