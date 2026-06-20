# 统一 Schema 基类 - 技术设计

## 上下文

### 当前状态

项目中存在两套 Schema 基类使用方式：

```
framework/schemas/base.py 提供的增强 BaseModel：
┌─────────────────────────────────────────────────────────────┐
│  model_config = ConfigDict(                                 │
│      from_attributes=True,      # 自动从 ORM 模型转换       │
│      populate_by_name=True,     # 别名支持                  │
│      use_enum_values=True,      # 枚举值序列化              │
│      validate_default=True,     # 默认值验证                │
│      str_strip_whitespace=True, # 字符串去空格              │
│      extra="ignore",            # 忽略额外字段              │
│  )                                                           │
└─────────────────────────────────────────────────────────────┘

实际使用情况：
• framework.schemas.BaseModel：1 处（ai/components/plugin）
• pydantic.BaseModel：27 个文件（iam/tenant/ai/demo schemas）
• 手动配置 ConfigDict(from_attributes=True)：7 处
```

### 约束

1. **零停机**：迁移过程中服务必须保持可用
2. **向后兼容**：所有现有 API 行为保持不变
3. **渐进式**：支持分批次迁移，每批次可独立验证
4. **可回滚**：每个模块迁移后可独立回滚

### 利益相关者

- **后端开发者**：需要了解新的编码规范
- **Code Reviewer**：需要检查是否使用正确的基类
- **QA**：需要验证迁移后功能正常

## 目标 / 非目标

**目标：**

1. 统一所有业务模块 Schema 使用 `framework.schemas.BaseModel`
2. 减少代码冗余，删除重复的 `model_config` 配置
3. 更新开发规范文档，明确基类选择指南
4. 添加 CI 检查，防止新代码违规

**非目标：**

1. 不修改 `ai_plugin/sdk/*`（独立 SDK，保持零依赖）
2. 不修改 framework 自身的 Schema 定义
3. 不改变任何 API 契约或业务逻辑
4. 不进行大规模重构或优化

## 决策

### 决策 1：使用渐进式迁移策略

**选择**：按模块分批次迁移（tenant → iam → ai → demo）

**理由**：

- 每个模块可独立验证和回滚
- 降低风险，避免"大爆炸"式变更
- 符合依赖方向（tenant 无依赖，iam 依赖 tenant）

**替代方案**：

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 一次性迁移 | 快速完成 | 风险高，难以定位问题 | ❌ 不采用 |
| 渐进式迁移 | 风险可控，可回滚 | 耗时较长 | ✅ 采用 |
| 仅新代码使用新规范 | 改动最小 | 存量代码不一致 | ❌ 不采用 |

### 决策 2：使用半自动迁移脚本

**选择**：脚本处理重复性工作 + 人工审查关键变更

**理由**：

- 27 个文件、~105 个 Schema 类，手动迁移易出错
- 脚本可保证一致性
- 人工审查确保正确性

**实现方式**：

```python
# 迁移脚本核心逻辑
def migrate_file(file_path: Path) -> bool:
    content = file_path.read_text(encoding="utf-8")

    # 1. 替换 import 语句
    content = re.sub(
        r'from pydantic import (.*)BaseModel(.*)',
        r'from framework.schemas import BaseModel\2',
        content
    )

    # 2. 删除冗余的 model_config
    content = re.sub(
        r'\s*model_config\s*=\s*ConfigDict\(from_attributes=True\)\s*\n',
        '\n',
        content
    )

    # 3. 保留其他 ConfigDict 用法的行（不删除）
    # 例如：model_config = ConfigDict(from_attributes=True, extra="forbid")

    return content != original
```

### 决策 3：豁免 ai_plugin/sdk 的迁移

**选择**：`ai_plugin/sdk/*` 继续使用 `pydantic.BaseModel`

**理由**：

- ai_plugin 是独立的插件 SDK，可能被外部项目使用
- 保持 SDK 的零依赖特性，不依赖 framework
- 避免破坏外部依赖者的使用

### 决策 4：删除 vs 保留 `model_config`

**选择**：删除冗余配置，依赖 framework 基类的默认配置

**理由**：

```python
# 迁移前
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 冗余
    id: str
    username: str

# 迁移后
class UserResponse(BaseModel):  # framework.schemas.BaseModel
    # 无需 model_config，已自动包含
    id: str
    username: str
```

**特殊情况处理**：

如果现有 Schema 有额外的 ConfigDict 配置（如 `extra="forbid"`），迁移后需要保留：

```python
# 迁移后保留额外配置
class StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 保留额外配置
    id: str
```

## 风险 / 权衡

### 风险 1：`validate_default=True` 可能暴露隐藏问题

**风险描述**：

framework.schemas.BaseModel 包含 `validate_default=True`，会验证默认值。当前大部分 Schema 未启用此选项，迁移后可能暴露之前未发现的数据问题。

**缓解措施**：

- 每个模块迁移后运行完整测试套件
- 关注测试中的 ValidationWarning 或错误
- 如发现问题，修复数据或调整默认值

### 风险 2：迁移遗漏导致行为不一致

**风险描述**：

如果某些文件未迁移，可能导致同一模块内 Schema 行为不一致。

**缓解措施**：

- 创建 CI 检查脚本，自动检测违规代码
- Code Review 时检查新增 Schema 是否使用正确的基类
- 使用 `grep` 或 AST 分析工具验证迁移完整性

### 风险 3：新代码继续使用旧方式

**风险描述**：

迁移完成后，新代码可能继续使用 `pydantic.BaseModel`。

**缓解措施**：

- 更新 `server/python/CLAUDE.md`，明确规范要求
- 在规范中添加示例代码和反例
- CI 检查脚本持续监控

### 权衡 1：迁移耗时 vs 一次性完成

渐进式迁移耗时较长（预计 3-5 天），但风险可控。一次性迁移快速（1 天），但风险高。选择渐进式迁移是值得的权衡。

### 权衡 2：自动化程度 vs 安全性

全自动脚本可以更快完成迁移，但可能引入错误。半自动脚本 + 人工审查的平衡更安全。

## 迁移计划

### 阶段 0：准备工作（0.5 天）

1. 更新 `server/python/CLAUDE.md`
2. 创建迁移脚本 `scripts/migrate_schema_basemodel.py`
3. 创建检测脚本 `scripts/check_schema_basemodel.sh`

### 阶段 1：迁移 tenant 模块（1 天）

```bash
# 迁移文件
tenant/schemas/admin/tenant.py
tenant/schemas/admin/module.py
tenant/schemas/admin/resource_config.py
tenant/schemas/admin/tenant_module.py
tenant/schemas/console/tenant.py

# 验证
uv run pytest tests/tenant/ -v
```

### 阶段 2：迁移 iam 模块（2 天）

```bash
# 迁移文件（分批）
Day 1: user.py, role.py
Day 2: permission.py, department.py, menu.py, login.py, oauth.py, token.py, user_menu.py
       admin/system_setting.py, console/system_setting.py

# 验证
uv run pytest tests/iam/ -v
```

### 阶段 3：迁移 ai 和 demo 模块（1 天）

```bash
# 迁移文件
ai/schemas/plugin.py
ai/schemas/model.py
ai/schemas/chat.py
ai/schemas/completion.py
ai/schemas/conversation.py

demo/schemas/dataset.py
demo/schemas/__init__.py

# 验证
uv run pytest tests/ai/ tests/demo/ -v
```

### 阶段 4：验证与清理（0.5 天）

```bash
# 完整测试
uv run pytest

# Ruff 检查
uv run ruff check src/
uv run ruff format --check src/

# 清理未使用的导入
uv run ruff check --fix --select F401 src/
```

### 回滚策略

每个模块迁移后创建独立提交：

```bash
git commit -m "refactor(tenant): 统一使用 framework.schemas.BaseModel"
git commit -m "refactor(iam): 统一使用 framework.schemas.BaseModel"
git commit -m "refactor(ai): 统一使用 framework.schemas.BaseModel"
git commit -m "refactor(demo): 统一使用 framework.schemas.BaseModel"
```

如发现问题，可回滚单个模块：

```bash
git revert <commit-hash>
```

## 开放问题

无待定决策或未知事项。所有关键技术决策已明确。
