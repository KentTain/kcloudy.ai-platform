# 统一 Schema 基类 - 任务清单

## 1. 准备工作

- [x] 1.1 更新 `server/python/CLAUDE.md`，添加 Schema 层开发规范章节
- [x] 1.2 创建迁移脚本 `server/python/scripts/migrate_schema_basemodel.py`
- [ ] 1.3 创建检测脚本 `server/python/scripts/check_schema_basemodel.sh`
- [ ] 1.4 验证 framework.schemas.BaseModel 的配置符合预期

## 2. 迁移 tenant 模块

- [ ] 2.1 迁移 `tenant/schemas/admin/tenant.py`
- [ ] 2.2 迁移 `tenant/schemas/admin/module.py`
- [ ] 2.3 迁移 `tenant/schemas/admin/resource_config.py`
- [ ] 2.4 迁移 `tenant/schemas/admin/tenant_module.py`
- [ ] 2.5 迁移 `tenant/schemas/console/tenant.py`
- [ ] 2.6 运行 tenant 模块测试：`uv run pytest tests/tenant/ -v`
- [ ] 2.7 提交变更：`git commit -m "refactor(tenant): 统一使用 framework.schemas.BaseModel"`

## 3. 迁移 iam 模块

### 3.1 第一批：核心 Schema

- [ ] 3.1.1 迁移 `iam/schemas/user.py`
- [ ] 3.1.2 迁移 `iam/schemas/role.py`
- [ ] 3.1.3 运行部分测试验证变更

### 3.2 第二批：权限和组织架构

- [ ] 3.2.1 迁移 `iam/schemas/permission.py`
- [ ] 3.2.2 迁移 `iam/schemas/department.py`
- [ ] 3.2.3 迁移 `iam/schemas/menu.py`

### 3.3 第三批：认证相关

- [ ] 3.3.1 迁移 `iam/schemas/login.py`
- [ ] 3.3.2 迁移 `iam/schemas/oauth.py`
- [ ] 3.3.3 迁移 `iam/schemas/token.py`
- [ ] 3.3.4 迁移 `iam/schemas/user_menu.py`

### 3.4 第四批：系统设置

- [ ] 3.4.1 迁移 `iam/schemas/admin/system_setting.py`
- [ ] 3.4.2 迁移 `iam/schemas/console/system_setting.py`

### 3.5 验证与提交

- [ ] 3.5.1 运行 iam 模块测试：`uv run pytest tests/iam/ -v`
- [ ] 3.5.2 提交变更：`git commit -m "refactor(iam): 统一使用 framework.schemas.BaseModel"`

## 4. 迁移 ai 模块

### 4.1 核心插件 Schema

- [ ] 4.1.1 迁移 `ai/schemas/plugin.py`
- [ ] 4.1.2 迁移 `ai/schemas/model.py`

### 4.2 对话和补全 Schema

- [ ] 4.2.1 迁移 `ai/schemas/chat.py`
- [ ] 4.2.2 迁移 `ai/schemas/completion.py`
- [ ] 4.2.3 迁移 `ai/schemas/conversation.py`

### 4.3 验证与提交

- [ ] 4.3.1 运行 ai 模块测试：`uv run pytest tests/ai/ -v`
- [ ] 4.3.2 提交变更：`git commit -m "refactor(ai): 统一使用 framework.schemas.BaseModel"`

## 5. 迁移 demo 模块

- [ ] 5.1 迁移 `demo/schemas/dataset.py`
- [ ] 5.2 迁移 `demo/schemas/__init__.py`
- [ ] 5.3 运行 demo 模块测试：`uv run pytest tests/demo/ -v`
- [ ] 5.4 提交变更：`git commit -m "refactor(demo): 统一使用 framework.schemas.BaseModel"`

## 6. 验证与清理

- [ ] 6.1 运行完整测试套件：`uv run pytest`
- [ ] 6.2 运行 Ruff 检查：`uv run ruff check src/`
- [ ] 6.3 运行 Ruff 格式化检查：`uv run ruff format --check src/`
- [ ] 6.4 清理未使用的导入：`uv run ruff check --fix --select F401 src/`
- [ ] 6.5 验证检测脚本：`bash scripts/check_schema_basemodel.sh`

## 7. 持续保障

- [ ] 7.1 将检测脚本集成到 CI 流程（可选）
- [ ] 7.2 更新项目 README.md（如有必要）
- [ ] 7.3 创建变更总结并归档

---

**预计总工作量**：3-5 天

**风险提示**：
- 任务 3.1.1（user.py）包含最多 Schema 类，需特别注意
- 任务 6.1（完整测试）可能发现 `validate_default=True` 暴露的问题
- 如发现测试失败，优先检查默认值是否符合字段约束
