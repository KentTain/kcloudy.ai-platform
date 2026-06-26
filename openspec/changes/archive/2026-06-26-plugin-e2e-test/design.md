## 上下文

### 背景

插件管理系统是 AI Platform 的核心组件，支持多种 AI 模型提供商（tongyi、gpustack、openai 等）的集成。系统包含完整的生命周期管理：

```
解析导入 → 安装 → 配置凭证 → 启动运行 → 调用模型
```

当前测试覆盖仅限于 Mock 测试和单元测试，缺少对真实插件包的端到端验证。

### 当前状态

| 测试类型 | 文件 | 覆盖范围 |
|----------|------|----------|
| 单元测试 | `test_plugin_package_service.py` | 包解析逻辑 |
| 单元测试 | `test_credential_service.py` | 凭证加密/解密 |
| 集成测试 | `test_plugin_installation_api.py` | 安装 API（Mock） |
| 集成测试 | `test_plugin_runtime_api.py` | 运行时 API（Mock） |
| 集成测试 | `test_plugin_lifecycle.py` | 生命周期（Mock） |

### 可用资源

- 真实插件包：`server/plugins/` 下有 8 个插件包
- API Keys：tongyi、gpustack 密钥可用于测试

### 约束

1. E2E 测试需要外部服务依赖（PostgreSQL、Redis、MinIO）
2. 模型调用测试需要真实 API Key，且可能产生费用
3. 测试需要隔离环境，不污染生产数据

## 目标 / 非目标

**目标：**

1. 建立可重复执行的 E2E 测试框架
2. 验证插件完整生命周期的正确性
3. 验证 tongyi、gpustack 插件的真实调用能力
4. 提供测试辅助工具简化后续测试编写

**非目标：**

1. 不测试所有插件包（仅 tongyi、gpustack 作为代表）
2. 不测试性能和并发场景（属于专项测试）
3. 不修改现有生产代码

## 决策

### 1. 测试目录结构

**决策：** 在 `tests/ai/e2e/` 目录下创建 E2E 测试

**理由：**
- 与现有测试结构一致（unit、integration、e2e 三级）
- 便于通过 `pytest -m e2e` 单独运行
- 避免与现有测试混淆

**替代方案：**
- ❌ 放在 `tests/ai/integration/`：E2E 测试有外部依赖，应与集成测试分离

### 2. 测试隔离策略

**决策：** 使用独立测试租户和命名空间

```
测试租户 ID: e2e-test-{timestamp}
Redis Key 前缀: e2e:test:
OSS Bucket: e2e-test-{timestamp}
```

**理由：**
- 完全隔离，不污染现有数据
- 便于清理（测试结束后删除所有资源）
- 支持并行执行多个测试

### 3. API Key 管理

**决策：** 通过环境变量获取 API Key，无配置时跳过测试

```python
@pytest.fixture
def tongyi_api_key():
    key = os.environ.get("E2E_TONGYI_API_KEY")
    if not key:
        pytest.skip("E2E_TONGYI_API_KEY not set")
    return key
```

**理由：**
- 安全：不在代码中硬编码密钥
- 灵活：CI 环境可注入密钥，本地开发可跳过

### 4. 测试粒度划分

**决策：** 按生命周期阶段拆分测试文件

```
tests/ai/e2e/
├── conftest.py                    # 共享夹具
├── test_plugin_parse.py           # 解析导入测试
├── test_plugin_install.py         # 安装流程测试
├── test_plugin_configure.py       # 配置验证测试
├── test_plugin_runtime.py         # 运行时测试
├── test_plugin_invoke.py          # 模型调用测试
└── helpers/
    └── plugin_test_helper.py      # 测试辅助工具
```

**理由：**
- 每个文件专注一个阶段，职责清晰
- 便于定位问题和单独运行
- 辅助工具可复用

### 5. 清理策略

**决策：** 每个测试用例负责清理自己创建的资源

```python
@pytest.fixture
async def plugin_manager(db_session, test_tenant_id):
    manager = await PluginManagerFactory.get_manager(test_tenant_id, db_session)
    yield manager
    # 清理所有插件
    for plugin_id in list(manager.running_plugins.keys()):
        await manager.uninstall_plugin(plugin_id)
```

**理由：**
- 测试失败不影响后续测试
- 资源泄漏可控

## 风险 / 权衡

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| API Key 泄露 | 安全风险 | 通过环境变量注入，不提交到代码库 |
| 模型调用产生费用 | 成本增加 | 限制调用次数，使用最小模型 |
| 测试不稳定（网络、服务） | CI 失败 | 添加重试机制，超时配置 |
| 清理失败导致残留 | 资源泄漏 | 添加清理检查钩子 |
| 测试执行时间长 | CI 延迟 | 默认跳过 E2E，手动触发 |

## 迁移计划

不涉及数据库迁移和部署变更。测试框架为新增内容，无需迁移。

## 待解决问题

1. **CI 集成**：如何在 CI 环境中安全地运行 E2E 测试？
   - 方案 A：仅在主分支合并后运行
   - 方案 B：手动触发工作流
   
2. **测试数据管理**：是否需要预置测试插件包？
   - 方案 A：使用现有 `server/plugins/` 目录下的插件包
   - 方案 B：创建专用最小测试插件包
