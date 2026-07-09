# 插件自动化处理流程设计文档

## 概述

本文档描述插件自动化处理流程的设计，实现在后端启动后自动执行插件的解析、安装、配置、启动和验证全流程。

## 目标

- 支持开发环境自检、演示环境初始化、生产环境部署等多种场景
- 通过配置控制哪些插件需要自动处理及其凭证配置
- 验证失败时可配置处理策略（警告/降级/失败）

## 架构设计

### 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| `PluginAutoSetupService` | 自动设置编排服务 | `tenant/services/plugin_auto_setup_service.py` |
| `PluginAutoSetupConfig` | 配置模型 | `tenant/schemas/plugin_auto_setup.py` |
| `PluginVerificationService` | 模型验证服务 | `ai/services/plugin_verification_service.py` |

### 数据流

```
启动 → 扫描 → 安装 → 配置 → 启动 → 服务就绪
                           ↓
                     后台验证 → 更新状态
```

### 状态流转

```
PENDING → INSTALLING → INSTALLED → CONFIGURING → CONFIGURED → STARTING → ACTIVE
                                                           ↓
                                                      (后台验证)
                                                           ↓
                                              ┌────────────┼────────────┐
                                              ↓            ↓            ↓
                                           ACTIVE      DEGRADED    FAILED
                                          (验证成功)   (验证失败)   (启动失败)
```

## 配置结构

在 `application.yml` 中新增 `plugin.auto_setup` 配置节：

```yaml
plugin:
  scan_on_startup: true
  scan_directory: "server/plugins"

  auto_setup:
    enabled: true
    plugins:
      - plugin_id: "langgenius-tongyi"
        auto_install: true
        auto_start: true
        credentials:
          api_key: "${TONGYI_API_KEY:}"
      - plugin_id: "langgenius-gpustack"
        auto_install: true
        auto_start: true
        credentials:
          api_key: "${GPUSTACK_API_KEY:}"
          endpoint: "${GPUSTACK_ENDPOINT:https://llm-stack.flydiysz.cn}"
      - plugin_id: "langgenius-siliconflow"
        auto_install: true
        auto_start: true
        credentials:
          api_key: "${SILICONFLOW_API_KEY:}"
      - plugin_id: "langgenius-deepseek"
        auto_install: true
        auto_start: true
        credentials:
          api_key: "${DEEPSEEK_API_KEY:}"

    verification:
      enabled: true
      timeout: 10
      on_failure: "warn"
```

### 配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | bool | 总开关，控制整个自动设置流程 |
| `plugins[].plugin_id` | str | 插件 ID |

**租户配置**：使用现有的 `tenant.default-tenant-id` 配置项，在 `application.yml` 中定义：

```yaml
tenant:
  default-tenant-id: "00000000-0000-0000-0000-000000000000"
```
| `plugins[].auto_install` | bool | 是否自动安装 |
| `plugins[].auto_start` | bool | 是否自动启动 |
| `plugins[].credentials` | dict | 凭证配置，支持环境变量 |
| `verification.enabled` | bool | 是否启用验证 |
| `verification.timeout` | int | 验证超时时间（秒） |
| `verification.on_failure` | str | 失败策略：warn/degrade/fail |

### 验证失败策略

| 策略 | 行为 |
|------|------|
| `warn` | 记录警告日志，插件状态保持 ACTIVE |
| `degrade` | 插件状态设为 DEGRADED，前端提示降级 |
| `fail` | 记录错误日志，视为启动失败（不阻止应用） |

## 启动流程集成

### 流程顺序

```
1. 基础组件初始化（数据库、Redis）
2. 数据库迁移验证
3. 模块定义同步
4. 数据初始化
5. 插件目录扫描（已有）
5.5. 插件自动设置（新增，同步）
6. 监听器初始化
7. 数据完整性验证
8. 后台验证任务（新增，异步）
```

### 关键设计决策

1. **职责分离**：
   - `tenant` 模块：负责安装、配置、启动（管理面）
   - `ai` 模块：负责验证、运行时状态（运行面）

2. **幂等性**：
   - 所有操作支持重复执行
   - 已安装的插件跳过安装
   - 已配置的凭证更新配置

3. **事务边界**：
   - 安装操作使用独立事务
   - 验证失败不回滚安装记录

4. **租户 ID 处理**：
   - 使用现有的 `tenant.default-tenant-id` 配置项
   - 启动时设置租户上下文，确保所有操作在正确的租户下执行

5. **安装流程复用**：
   - 复用现有的安装任务流程（`InstallTaskService`、`InstallTaskManager`）
   - 同步执行安装任务，避免队列异步处理的复杂性
   - 直接调用安装核心逻辑，跳过 Redis 队列入队

## 错误处理策略

| 阶段 | 失败行为 | 日志级别 | 影响范围 |
|------|----------|----------|----------|
| 配置加载失败 | 记录错误，跳过自动设置 | ERROR | 禁用自动设置 |
| 插件定义不存在 | 记录警告，跳过该插件 | WARNING | 单个插件 |
| 安装失败 | 记录错误，继续处理其他插件 | ERROR | 单个插件 |
| 配置凭证失败 | 记录错误，插件状态保持 INACTIVE | ERROR | 单个插件 |
| 启动失败 | 记录错误，插件状态为 FAILED | ERROR | 单个插件 |
| 验证失败 | 根据策略：warn/degrade/fail | WARNING/ERROR | 单个插件 |

**核心原则**：
- 单个插件失败不影响其他插件
- 自动设置失败不阻止应用启动
- 所有错误都记录详细日志便于排查

## 实现文件清单

| 文件 | 说明 |
|------|------|
| `tenant/schemas/plugin_auto_setup.py` | 配置模型定义 |
| `tenant/services/plugin_auto_setup_service.py` | 自动设置编排服务 |
| `ai/services/plugin_verification_service.py` | 模型验证服务 |
| `application_web.py` | 启动流程集成 |
| `demo/configs/settings.py` | 配置模型更新 |

## 测试验证

### 验证标准

1. **配置加载**：正确解析配置文件和环境变量
2. **插件安装**：未安装的插件自动安装
3. **凭证配置**：API Key 正确保存到数据库
4. **插件启动**：插件状态变为 ACTIVE
5. **模型验证**：发送测试请求验证模型可用性
6. **失败处理**：根据策略正确处理验证失败

### 测试场景

| 场景 | 预期行为 |
|------|----------|
| 首次启动 | 扫描 → 安装 → 配置 → 启动 → 验证 |
| 重复启动 | 跳过已安装插件，更新配置 |
| 插件定义不存在 | 跳过该插件，记录警告 |
| API Key 无效 | 验证失败，根据策略处理 |
| 网络超时 | 验证失败，根据策略处理 |
