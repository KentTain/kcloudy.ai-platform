# 插件资源管理架构完善设计文档

**文档版本：** 1.0
**创建日期：** 2026-06-25
**作者：** Claude Code
**状态：** 待审查

---

## 1. 背景与目标

### 1.1 当前状态

项目已完成插件资源管理架构的基础迁移（commit 1d6090d），实现了：

- ✅ AI 模块旧模型清理（Plugin、PluginDeclaration、PluginInstallation）
- ✅ AI 模块迁移到 Provider + DTO 架构
- ✅ Tenant 模块基础表结构创建
- ✅ AI 模块新增 PluginConfig 和 PluginRuntimeState 模型

### 1.2 待完善内容

根据设计方案 `docs/designs/3.插件与模型资源管理 Tenant 统一管理设计方案.md`，仍需补充：

1. **数据结构补充**
   - `declaration` 字段（合并 `remote_declaration`）
   - `PluginInstallationDTO` 字段补充

2. **事件驱动机制**
   - AI 模块事件发布逻辑
   - Tenant 模块事件监听器
   - 跨 Schema 事务一致性保障

3. **测试验证**
   - 单元测试覆盖
   - 集成测试
   - 端到端测试

### 1.3 设计目标

- 完整实现设计方案中的数据结构
- 建立事件驱动的一致性保障机制
- 提供全面的测试覆盖

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI 模块（使用面）                          │
│                                                                  │
│  PluginManager.install_plugin()                                 │
│  ├── 1. 解析插件包 → declaration                               │
│  ├── 2. 创建 Tenant 侧记录（通过 Provider）                     │
│  ├── 3. 创建 AI 侧配置（PluginConfig）                         │
│  ├── 4. 创建 AI 侧状态（PluginRuntimeState）                   │
│  └── 5. 失败时发布事件 → PluginInstallationFailed              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                   PluginInstallationDTO
                   (包含 declaration 字段)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Tenant 模块（管理面）                         │
│                                                                  │
│  PluginInstallationProvider                                     │
│  ├── create_installation(dto)                                  │
│  │   ├── 创建 plugin_definitions (declaration)                │
│  │   └── 创建 plugin_installations                            │
│  └── update_installation()                                     │
│                                                                  │
│  事件监听器                                                      │
│  └── PluginInstallationFailedHandler                           │
│      └── 更新状态为 FAILED                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
插件安装流程：

1. AI 模块解析插件包
   └─→ PluginConfig (包含完整声明)

2. AI 模块准备 DTO
   └─→ PluginInstallationDTO(declaration=PluginConfig.model_dump())

3. AI 模块调用 Provider
   └─→ provider.create_installation(dto)

4. Tenant 模块创建记录
   ├── 创建/更新 plugin_definitions (declaration)
   └── 创建 plugin_installations

5. AI 模块创建配置
   ├── 创建 plugin_configs (AI Schema)
   └── 创建 plugin_runtime_states (AI Schema)

6. AI 模块更新状态
   └→ provider.update_installation(status="ACTIVE")

异常流程：

E1. AI 侧步骤 5 失败
    └─→ 发布 PluginInstallationFailed 事件
        └─→ Tenant 监听器更新状态为 FAILED
```

---

## 3. 详细设计

### 3.1 数据结构补充

#### 3.1.1 TenantPluginDefinition 模型更新

**文件：** `server/python/src/tenant/models/plugin_definition.py`

**变更：**
- 新增 `declaration` 字段（JSONB，必需）
- 删除 `remote_declaration` 字段（已合并）

**字段定义：**

```python
declaration: Mapped[dict] = mapped_column(
    JSONB,
    nullable=False,
    comment="完整声明内容（manifest + 工具/模型声明）。"
            "local类型从插件包解析，remote类型从远程获取。"
            "包含：configuration、tools_configuration、"
            "models_configuration、agent_strategies_configuration",
)
```

**数据结构：**

```json
{
  "configuration": {
    "author": "alon",
    "name": "tongyi",
    "version": "1.0.0",
    "description": "通义千问插件"
  },
  "tools_configuration": [
    {
      "name": "search",
      "description": "搜索工具",
      "parameters": {...}
    }
  ],
  "models_configuration": [...],
  "agent_strategies_configuration": [...]
}
```

#### 3.1.2 PluginInstallationDTO 字段补充

**文件：** `server/python/src/framework/tenant/plugin_protocols.py`

**新增字段：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `declaration` | `dict` | 必需 | 完整声明内容 |
| `installed_at` | `datetime \| None` | `None` | 安装完成时间 |
| `install_config` | `dict \| None` | `None` | 安装配置（依赖版本、环境信息等） |
| `source` | `str \| None` | `None` | 来源（package, marketplace） |
| `meta` | `dict \| None` | `None` | 元数据（marketplace 记录） |

**完整定义：**

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PluginInstallationDTO:
    """安装记录 DTO
    
    用于 Tenant 模块与 AI 模块之间传递插件安装信息。
    """
    
    tenant_id: str
    plugin_id: str
    plugin_unique_identifier: str
    declaration: dict  # 完整声明内容
    status: str = "PENDING"
    auto_start: bool = False
    freeze_threshold_hours: int = 24
    plugin_type: str | None = None
    runtime_type: str | None = None
    installed_at: datetime | None = None
    install_config: dict | None = None
    source: str | None = None
    meta: dict | None = None
```

#### 3.1.3 数据库迁移

**文件：** `server/python/src/tenant/migrations/versions/003_add_declaration_field.py`

```python
"""补充 declaration 字段并移除 remote_declaration

Revision ID: 003_add_declaration_field
Revises: 002_tenant_plugins
Create Date: 2026-06-25
"""

def upgrade() -> None:
    # 添加 declaration 字段
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "declaration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="完整声明内容",
        ),
        schema="tenant",
    )
    
    # 删除 remote_declaration 字段
    op.drop_column("plugin_definitions", "remote_declaration", schema="tenant")


def downgrade() -> None:
    # 回滚：恢复 remote_declaration
    op.add_column(
        "plugin_definitions",
        sa.Column(
            "remote_declaration",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="远程声明",
        ),
        schema="tenant",
    )
    
    # 删除 declaration
    op.drop_column("plugin_definitions", "declaration", schema="tenant")
```

---

### 3.2 事件驱动机制

#### 3.2.1 AI 模块事件发布

**文件：** `server/python/src/ai/components/plugin/engine/core/plugin_manager.py`

**修改方法：** `_save_plugin_installation_to_database`

**核心逻辑：**

```python
async def _save_plugin_installation_to_database(...):
    """保存插件安装信息到数据库（事件驱动）"""
    from framework.events.publisher import get_event_publisher
    from framework.events.domain_events import PluginInstallationFailed
    
    provider = get_plugin_installation_provider()
    event_publisher = get_event_publisher()
    
    # 准备 declaration 数据
    declaration = plugin_config.model_dump(mode="json")
    
    # 准备 DTO（包含 declaration）
    installation_dto = PluginInstallationDTO(
        tenant_id=self.tenant_id,
        plugin_id=plugin_id,
        plugin_unique_identifier=plugin_unique_identifier,
        declaration=declaration,
        status="PENDING",
        auto_start=auto_start,
        installed_at=datetime.now(),
        install_config=install_info,
        source="package",
    )

    try:
        # 1. 创建 Tenant 侧记录
        installation = await provider.create_installation(
            self.tenant_id, 
            installation_dto
        )

        # 2. 创建 AI 侧配置和状态
        ai_config = AIPluginConfig(...)
        session.add(ai_config)
        
        runtime_state = PluginRuntimeState(...)
        session.add(runtime_state)
        await session.flush()

        # 3. 更新状态为 ACTIVE
        await provider.update_installation(
            self.tenant_id, 
            plugin_id, 
            {"status": "ACTIVE"}
        )

    except Exception as e:
        # 发布失败事件
        await event_publisher.publish_with_retry(
            PluginInstallationFailed(
                tenant_id=self.tenant_id,
                plugin_id=plugin_id,
                error_message=str(e),
            ),
            max_retries=3,
        )
        raise
```

#### 3.2.2 Tenant Provider 实现

**文件：** `server/python/src/tenant/services/plugin_provider.py`

**关键修改：**

```python
async def create_installation(
    self, 
    tenant_id: str, 
    data: PluginInstallationDTO,
) -> PluginInstallationDTO:
    """创建插件安装记录
    
    Args:
        tenant_id: 租户 ID
        data: 安装记录 DTO（包含 declaration）
    """
    async with get_task_session() as session:
        # 确保插件定义已存在（使用 DTO 中的 declaration）
        definition = await self._ensure_plugin_definition(session, data)

        installation = TenantPluginInstallation(...)
        session.add(installation)
        await session.flush()

        return self._to_dto(installation)


async def _ensure_plugin_definition(
    self, 
    session, 
    data: PluginInstallationDTO,
) -> TenantPluginDefinition:
    """确保插件定义存在"""
    definition = await TenantPluginDefinition.one_by_field(
        session, "plugin_unique_identifier", data.plugin_unique_identifier
    )

    if definition:
        # 引用计数递增
        definition.refers += 1
        await session.flush()
    else:
        # 使用 DTO 中的 declaration 创建新定义
        definition = TenantPluginDefinition(
            plugin_id=data.plugin_id,
            plugin_unique_identifier=data.plugin_unique_identifier,
            declaration=data.declaration,  # 从 DTO 获取
            install_type=data.plugin_type or "local",
            refers=1,
        )
        session.add(definition)
        await session.flush()
    
    return definition
```

#### 3.2.3 Tenant 事件监听器

**目录结构：**

```
server/python/src/tenant/listeners/
├── __init__.py
├── handlers/
│   ├── __init__.py
│   └── plugin_handler.py
└── setup.py
```

**文件：** `server/python/src/tenant/listeners/handlers/plugin_handler.py`

```python
"""插件事件处理器"""

from loguru import logger
from framework.events.base import DomainEvent
from framework.events.domain_events import (
    PluginInstallationFailed,
    PluginUninstallFailed,
)
from framework.queue.handler import QueueHandler
from tenant.services.plugin_provider import plugin_installation_provider_impl

_logger = logger.bind(name=__name__)


class PluginInstallationFailedHandler(QueueHandler):
    """插件安装失败事件处理器"""

    async def handle(self, event: DomainEvent) -> None:
        """处理插件安装失败事件
        
        将 Tenant 侧的安装记录状态更新为 FAILED。
        """
        if not isinstance(event, PluginInstallationFailed):
            _logger.warning(f"事件类型不匹配: {type(event)}")
            return

        _logger.info(
            f"处理插件安装失败事件: tenant_id={event.tenant_id}, "
            f"plugin_id={event.plugin_id}"
        )

        try:
            provider = plugin_installation_provider_impl
            
            # 更新安装记录状态为 FAILED
            await provider.update_installation(
                event.tenant_id,
                event.plugin_id,
                {
                    "status": "FAILED",
                    "meta": {"error": event.error_message},
                },
            )
            
            _logger.info(f"插件安装记录已标记为失败: {event.plugin_id}")

        except Exception as e:
            _logger.exception(f"处理插件安装失败事件失败")
            raise  # 触发重试机制


class PluginUninstallFailedHandler(QueueHandler):
    """插件卸载失败事件处理器"""

    async def handle(self, event: DomainEvent) -> None:
        """处理插件卸载失败事件
        
        记录失败日志，便于后续排查。
        """
        if not isinstance(event, PluginUninstallFailed):
            return

        _logger.error(
            f"插件卸载失败: tenant_id={event.tenant_id}, "
            f"plugin_id={event.plugin_id}, error={event.error_message}"
        )
```

**文件：** `server/python/src/tenant/listeners/setup.py`

```python
"""Tenant 模块监听器生命周期管理"""

from framework.queue.consumer import QueueConsumer
from framework.events.base import EventStream
from tenant.listeners.handlers.plugin_handler import (
    PluginInstallationFailedHandler,
    PluginUninstallFailedHandler,
)

_consumers: list[QueueConsumer] = []


async def setup_listeners():
    """启动事件监听器"""
    global _consumers
    
    # 插件安装失败事件监听
    consumer1 = QueueConsumer(
        stream_name=EventStream.PLUGIN_INSTALLATION_FAILED,
        group_name="tenant_plugin_handlers",
        consumer_name="tenant_plugin_handler_1",
        handler=PluginInstallationFailedHandler(),
    )
    await consumer1.start()
    _consumers.append(consumer1)
    
    # 插件卸载失败事件监听
    consumer2 = QueueConsumer(
        stream_name=EventStream.PLUGIN_UNINSTALL_FAILED,
        group_name="tenant_plugin_handlers",
        consumer_name="tenant_plugin_handler_1",
        handler=PluginUninstallFailedHandler(),
    )
    await consumer2.start()
    _consumers.append(consumer2)


async def shutdown_listeners():
    """停止事件监听器"""
    global _consumers
    for consumer in _consumers:
        await consumer.stop()
    _consumers.clear()
```

---

### 3.3 测试验证

#### 3.3.1 单元测试

**测试文件：**

```
tests/tenant/unit/
├── test_plugin_provider.py          # Provider 实现测试
└── test_dto_conversion.py            # DTO 转换测试

tests/ai/unit/components/plugin/
├── test_plugin_manager_install.py    # 安装流程测试
└── test_event_publishing.py          # 事件发布测试
```

**测试用例清单：**

| 测试项 | 测试文件 | 关键断言 |
|--------|---------|---------|
| 创建安装记录（含 declaration） | `test_plugin_provider.py` | `assert result.plugin_id == expected` |
| 引用计数递增 | `test_plugin_provider.py` | `assert definition.refers == 2` |
| 更新安装状态 | `test_plugin_provider.py` | `assert result.status == "ACTIVE"` |
| DTO 转换正确性 | `test_dto_conversion.py` | `assert dto.tenant_id == expected` |
| 事件发布成功 | `test_event_publishing.py` | `mock_publish.assert_called_once()` |
| 事件重试机制 | `test_event_publishing.py` | `assert retry_count == 3` |

#### 3.3.2 集成测试

**文件：** `tests/ai/integration/test_plugin_lifecycle.py`

**测试场景：**

1. **插件安装成功**
   - 验证 Tenant 侧记录状态为 ACTIVE
   - 验证 declaration 字段正确存储
   - 验证 AI 侧配置和状态正确创建

2. **插件安装失败（AI 侧失败）**
   - 模拟 AI 配置创建失败
   - 验证事件发布
   - 验证 Tenant 侧状态更新为 FAILED

3. **插件卸载流程**
   - 验证记录删除正确

#### 3.3.3 端到端测试

**文件：** `tests/ai/e2e/test_plugin_api.py`

**测试场景：**

1. POST `/ai/console/v1/plugins/install` - 安装插件
2. GET `/ai/console/v1/plugins` - 查询插件列表
3. DELETE `/ai/console/v1/plugins/{id}` - 卸载插件

#### 3.3.4 测试覆盖率目标

| 模块 | 目标覆盖率 | 测试重点 |
|------|-----------|---------|
| Provider 实现 | > 85% | CRUD、引用计数、DTO 转换 |
| 事件监听器 | > 80% | 事件处理、重试机制、异常处理 |
| PluginManager | > 80% | 安装/卸载流程、事件发布 |
| API 接口 | > 70% | 正常流程、异常处理 |

---

## 4. 实施计划

### 4.1 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `tenant/models/plugin_definition.py` | 修改 | 新增 declaration 字段 |
| `framework/tenant/plugin_protocols.py` | 修改 | 补充 DTO 字段 |
| `tenant/migrations/versions/003_add_declaration_field.py` | 新增 | declaration 字段迁移 |
| `tenant/services/plugin_provider.py` | 修改 | 更新 DTO 处理逻辑 |
| `tenant/listeners/__init__.py` | 新增 | 监听器模块初始化 |
| `tenant/listeners/handlers/__init__.py` | 新增 | 处理器模块初始化 |
| `tenant/listeners/handlers/plugin_handler.py` | 新增 | 插件事件处理器 |
| `tenant/listeners/setup.py` | 新增 | 监听器生命周期管理 |
| `ai/components/plugin/engine/core/plugin_manager.py` | 修改 | 事件发布逻辑 |
| `tests/tenant/unit/test_plugin_provider.py` | 新增 | Provider 单元测试 |
| `tests/ai/unit/components/plugin/test_event_publishing.py` | 新增 | 事件发布测试 |
| `tests/ai/integration/test_plugin_lifecycle.py` | 新增 | 生命周期集成测试 |

### 4.2 实施步骤

**阶段 1：数据结构补充**
1. 更新 `TenantPluginDefinition` 模型
2. 补充 `PluginInstallationDTO` 字段
3. 创建数据库迁移脚本
4. 更新 `PluginInstallationProviderImpl` 实现

**阶段 2：事件驱动机制**
1. 修改 `plugin_manager.py` 事件发布逻辑
2. 创建 Tenant 事件监听器目录和文件
3. 实现事件处理器
4. 实现监听器生命周期管理

**阶段 3：测试验证**
1. 编写单元测试
2. 编写集成测试
3. 编写端到端测试
4. 验证测试覆盖率

---

## 5. 风险与缓解措施

### 5.1 数据丢失风险

**风险：** 删除 `remote_declaration` 字段可能导致历史数据丢失

**缓解措施：**
- 迁移前确认生产环境无使用 `remote_declaration` 的历史数据
- 提供回滚脚本

### 5.2 事件丢失风险

**风险：** Redis 连接失败时事件可能丢失

**缓解措施：**
- 使用 `publish_with_retry` 机制（最多重试 3 次）
- 监听器异常时自动重试

### 5.3 并发问题

**风险：** 多个租户同时安装同一插件可能导致引用计数错误

**缓解措施：**
- Provider 使用独立事务
- 数据库约束保障（unique constraint）

---

## 6. 验收标准

### 6.1 功能验收

- [ ] `declaration` 字段正确存储插件完整声明
- [ ] `PluginInstallationDTO` 包含所有必需字段
- [ ] 插件安装成功时，Tenant 和 AI 侧数据一致
- [ ] 插件安装失败时，事件正确发布并处理
- [ ] 事件监听器正确启动和停止

### 6.2 测试验收

- [ ] 单元测试覆盖率达标
- [ ] 集成测试全部通过
- [ ] 端到端测试全部通过
- [ ] 无阻塞性 bug

### 6.3 文档验收

- [ ] 代码注释完整
- [ ] 更新相关 CLAUDE.md 文档
- [ ] 迁移脚本包含详细说明

---

## 7. 参考资料

- 设计方案：`docs/designs/3.插件与模型资源管理 Tenant 统一管理设计方案.md`
- Tenant 模块文档：`server/python/src/tenant/CLAUDE.md`
- AI 模块文档：`server/python/src/ai/CLAUDE.md`
- 相关 commit：`1d6090d` (refactor(ai,tenant): 完成插件资源管理迁移及代码清理)
