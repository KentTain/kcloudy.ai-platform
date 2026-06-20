# 统一 Schema 基类

## 为什么

当前项目中存在两套 Pydantic Schema 基类使用方式：部分代码使用 `framework.schemas.BaseModel`（增强版），大部分代码直接使用 `pydantic.BaseModel` 并手动配置 `model_config`。这种不一致性导致：

1. **代码冗余**：每个 Schema 都需要重复配置 `from_attributes=True`
2. **行为不一致**：不同模块的 Schema 可能使用不同的配置组合
3. **维护成本高**：新人开发者不清楚应该使用哪种方式，Code Review 难以统一标准

现在是架构治理的合适时机，因为项目处于早期阶段，迁移成本相对较低。

## 变更内容

1. **统一使用 `framework.schemas.BaseModel`**
   - 所有业务模块（iam、tenant、ai、demo）的 Schema 类必须继承 `framework.schemas.BaseModel`
   - 删除冗余的 `model_config = ConfigDict(from_attributes=True)` 配置
   - 清理未使用的 `ConfigDict` 导入

2. **更新开发规范**
   - 在 `server/python/CLAUDE.md` 中明确 Schema 层开发规范
   - 添加基类选择指南和豁免情况说明

3. **添加 CI 检查**
   - 创建检查脚本，自动拦截违规代码

4. **保持豁免**
   - `ai_plugin/sdk/*` 继续使用 `pydantic.BaseModel`（独立 SDK，保持零依赖）

## 功能 (Capabilities)

### 新增功能

- `schema-base-class`: 统一的 Schema 基类使用规范，包括基类选择指南、配置约定和豁免情况

### 修改功能

无。此变更不影响规范层面的行为，仅涉及实现细节的统一。

## 影响

### 受影响的代码

| 模块 | 文件数 | Schema 类数 | 迁移复杂度 |
|------|--------|------------|----------|
| iam/schemas/ | 10 | ~50 | 中 |
| tenant/schemas/ | 5 | ~30 | 低 |
| ai/schemas/ | 5 | ~20 | 低 |
| demo/schemas/ | 2 | ~5 | 低 |
| **合计** | **22** | **~105** | **中** |

### 豁免文件

- `ai_plugin/sdk/schemas/*` (3 个文件) — 独立 SDK，不依赖 framework

### API 端点

无影响。此变更仅涉及内部实现细节，不影响 API 契约。

### 兼容性

- **向后兼容**：所有现有功能保持不变
- **破坏性变更**：无

### 迁移策略

采用渐进式迁移策略，按模块分批次进行：

1. **阶段 1**：更新规范文档（CLAUDE.md）
2. **阶段 2**：迁移 tenant 模块（最底层，无业务依赖）
3. **阶段 3**：迁移 iam 模块
4. **阶段 4**：迁移 ai 和 demo 模块
5. **阶段 5**：验证与清理，添加 CI 检查

每个阶段完成后立即运行测试，确保功能正常。

### 风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| `validate_default=True` 可能暴露隐藏问题 | 中 | 完整测试覆盖 |
| 遗漏文件未迁移 | 低 | 创建 CI 检查脚本 |
| 新代码继续使用旧方式 | 低 | 更新规范文档 + Code Review |

### 依赖项

- 需要完整的测试套件支持
- 需要 Ruff 进行代码格式化和未使用导入清理
