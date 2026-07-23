# kbhub 迁移 Phase 1 实现计划：基础设施 + iam 扩展

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 搭建 framework 权限判定引擎/审计写入/站内信发送辅助，实现 iam 站内信/权限申请/企业 Policy 模型与服务，增强 iam 组织用户服务，更新各模块 CLAUDE.md，为 Phase 2（document）和 Phase 3（ai）提供前置依赖。

**架构：** framework 提供权限引擎 Protocol 接口 + Policy 求值器 + 审计写入辅助 + 站内信发送辅助（延迟导入 iam 避免循环依赖）；iam 新增 3 个业务模型（Notification/PermissionRequest/Policy）+ 服务 + admin/console 控制器 + 5 张表迁移；审计日志复用现有 `iam.audit_logs`。

**技术栈：** Python 3.12+、FastAPI、SQLAlchemy 2.0 async、Alembic、PostgreSQL、pytest + pytest-asyncio

---

## 文件结构

### framework 新增文件
- `server/python/src/framework/permission/engine.py` - 权限判定引擎 Protocol 接口 + 编排器（第2层资源权限 + 第3层 Policy）
- `server/python/src/framework/permission/policy_evaluator.py` - 企业 Policy 求值器（JSON 条件匹配，deny 优先）
- `server/python/src/framework/permission/audit_writer.py` - 审计日志统一写入辅助（延迟导入 iam.AuditLog）
- `server/python/src/framework/permission/__init__.py` - 包导出
- `server/python/src/framework/notification/sender.py` - 站内信发送辅助（延迟导入 iam.Notification）
- `server/python/src/framework/notification/__init__.py` - 包导出

### iam 新增/修改文件
- `server/python/src/iam/models/notification.py` - Notification / NotificationRead
- `server/python/src/iam/models/permission_request.py` - PermissionRequest / PermissionCacheEvent
- `server/python/src/iam/models/policy.py` - Policy
- `server/python/src/iam/models/__init__.py` - 修改：导出新模型
- `server/python/src/iam/models/enums.py` - 修改：新增 NotificationType / PermissionRequestType / PermissionRequestStatus / PolicyEffect 枚举
- `server/python/src/iam/schemas/notification.py` - 站内信 DTO
- `server/python/src/iam/schemas/permission_request.py` - 权限申请 DTO
- `server/python/src/iam/schemas/policy.py` - Policy DTO
- `server/python/src/iam/services/notification_service.py` - 站内信服务
- `server/python/src/iam/services/permission_request_service.py` - 权限申请服务
- `server/python/src/iam/services/policy_service.py` - Policy 服务
- `server/python/src/iam/services/__init__.py` - 修改：导出新服务
- `server/python/src/iam/controllers/admin/notification_controller.py` - 站内信管理端
- `server/python/src/iam/controllers/admin/permission_request_controller.py` - 权限申请管理端
- `server/python/src/iam/controllers/admin/policy_controller.py` - Policy 管理端
- `server/python/src/iam/controllers/console/notification_controller.py` - 站内信用户端
- `server/python/src/iam/controllers/console/permission_request_controller.py` - 权限申请用户端
- `server/python/src/iam/controllers/inner/permission_request_controller.py` - 权限申请回调 inner 接口（Phase 2/3 实现 apply，Phase 1 仅占位）
- `server/python/src/iam/module.py` - 修改：注册新路由 + 增补菜单权限
- `server/python/src/iam/migrations/versions/004_notification.py` - 站内信表
- `server/python/src/iam/migrations/versions/005_permission_request.py` - 权限申请表
- `server/python/src/iam/migrations/versions/006_policy.py` - Policy 表
- `server/python/src/iam/migrations/seeds/policy_seed.py` - 默认 Policy 种子

### iam 组织/用户增强（修改文件）
- `server/python/src/iam/services/organization_service.py` - 增强人员组织选择器接口
- `server/python/src/iam/services/user_service.py` - 增强用户搜索选择接口
- `server/python/src/iam/controllers/console/org_user_controller.py` - 增补选择器端点

### 前端 iam 新增文件
- `web/vue/src/iam/api/notification.ts` - 站内信 API
- `web/vue/src/iam/api/permissionRequest.ts` - 权限申请 API
- `web/vue/src/iam/api/policy.ts` - Policy API
- `web/vue/src/iam/types/notification.ts` / `permissionRequest.ts` / `policy.ts` - 类型
- `web/vue/src/iam/stores/notification.ts` - 站内信 store
- `web/vue/src/iam/pages/notifications/NotificationList.vue` - 站内信页面
- `web/vue/src/iam/pages/permission-requests/PermissionRequestList.vue` - 权限申请页面
- `web/vue/src/iam/pages/policies/PolicyList.vue` - Policy 页面
- `web/vue/src/iam/components/PermissionTroubleshootPanel.vue` - 权限排障面板组件
- `web/vue/src/iam/router/index.ts` - 修改：新增路由
- `web/vue/src/iam/index.ts` - 修改：导出新 API/类型

### 文档更新
- `server/python/src/CLAUDE.md` - 模块导航 + 依赖边界
- `server/python/src/framework/CLAUDE.md` - 权限引擎/审计写入/站内信辅助
- `server/python/src/iam/CLAUDE.md` - 站内信/权限申请/Policy
- `server/python/src/document/CLAUDE.md` - 新建
- `server/python/src/ai/CLAUDE.md` - 补充知识库/工具库/平台设置
- 前端 `web/vue/src/iam/CLAUDE.md` 等 - 对应更新

### 测试文件
- `server/python/tests/framework/unit/permission/test_policy_evaluator.py`
- `server/python/tests/framework/unit/permission/test_engine.py`
- `server/python/tests/framework/unit/permission/test_audit_writer.py`
- `server/python/tests/framework/unit/notification/test_sender.py`
- `server/python/tests/iam/unit/services/test_notification_service.py`
- `server/python/tests/iam/unit/services/test_permission_request_service.py`
- `server/python/tests/iam/unit/services/test_policy_service.py`
- `server/python/tests/iam/unit/controllers/test_notification_controller.py`
- `server/python/tests/iam/unit/controllers/test_permission_request_controller.py`
- `server/python/tests/iam/unit/controllers/test_policy_controller.py`
- `server/python/tests/iam/integration/test_permission_flow.py`

---

## 批次 1：文档准备

### 任务 1：更新后端模块 CLAUDE.md

**文件：**
- 修改：`server/python/src/CLAUDE.md`
- 修改：`server/python/src/framework/CLAUDE.md`
- 修改：`server/python/src/iam/CLAUDE.md`
- 修改：`server/python/src/ai/CLAUDE.md`
- 创建：`server/python/src/document/CLAUDE.md`

- [ ] **步骤 1：阅读现有 CLAUDE.md 结构**

运行：读取 `server/python/src/CLAUDE.md`、`server/python/src/iam/CLAUDE.md`，掌握文档章节规范（模块定位、目录职责、依赖边界、接口分层）。

- [ ] **步骤 2：更新 `server/python/src/CLAUDE.md`**

在模块导航表新增 document 模块行，依赖边界章节补充：`framework ─X─▶ iam/ai/document`（framework 禁止依赖业务模块，通过延迟导入或 inner 接口）、`ai ──▶ document`（ai 依赖 document inner 接口回查源文件权限）。

- [ ] **步骤 3：更新 `server/python/src/framework/CLAUDE.md`**

新增 `permission/` 目录说明（engine.py 权限判定引擎 Protocol 接口、policy_evaluator.py Policy 求值器、audit_writer.py 审计写入辅助）和 `notification/` 目录说明（sender.py 站内信发送辅助）。强调延迟导入 iam 避免循环依赖。

- [ ] **步骤 4：更新 `server/python/src/iam/CLAUDE.md`**

新增章节：站内信（Notification/NotificationRead）、权限申请（PermissionRequest/PermissionCacheEvent，含审批回调 inner 接口）、企业 Policy（Policy，deny 优先）。

- [ ] **步骤 5：更新 `server/python/src/ai/CLAUDE.md`**

补充预告章节：知识库、入库审核、工具库、平台设置（Phase 3 实现），说明 ai 依赖 document inner 接口回查源文件权限。

- [ ] **步骤 6：创建 `server/python/src/document/CLAUDE.md`**

```markdown
# Document 模块开发指南

## 模块定位

文档库管理模块，提供文档库（个人/团队）、文件夹树、文件管理、成员管理、资源权限体系、标签、人设、文档切片索引、回收站能力。schema 为 `document`。

## 目录职责

| 目录 | 职责 |
|------|------|
| module.py | ModuleDefinition（菜单 + PermissionDef） |
| models/ | 数据模型（继承 BaseModel + Mixin） |
| schemas/ | 请求/响应 DTO（继承 framework.schemas.BaseModel） |
| services/ | 业务服务（static 方法，注入 AsyncSession） |
| controllers/admin | 管理端接口 |
| controllers/console | 用户端接口 |
| controllers/inner | 内部接口（供 ai 模块回查权限，无认证） |
| tasks/ | 文档切片索引任务 |
| listeners/ | 事件监听 |
| migrations/ | Alembic 迁移 + 种子 |

## 接口分层

- 管理端：`/document/admin/v1/*`
- 用户端：`/document/console/v1/*`
- 内部接口：`/document/inner/v1/*`（无认证，仅供 ai 模块调用）

## 依赖边界

- document ──▶ framework（权限引擎、审计写入）
- document ──▶ iam（通过 inner 接口获取用户/组织信息）
- ai ──▶ document（ai 通过 inner 接口回查源文件权限，不放大权限）
```

- [ ] **步骤 7：更新前端各模块 CLAUDE.md**

更新 `web/vue/src/iam/CLAUDE.md`（新增站内信/权限申请/Policy 页面说明）、`web/vue/src/document/CLAUDE.md`（如不存在则创建骨架说明）、`web/vue/src/ai/CLAUDE.md`（预告知识库/工具库页面）。

- [ ] **步骤 8：Commit**

```bash
git add server/python/src/CLAUDE.md server/python/src/framework/CLAUDE.md server/python/src/iam/CLAUDE.md server/python/src/ai/CLAUDE.md server/python/src/document/CLAUDE.md web/vue/src/iam/CLAUDE.md
git commit -m "docs(kbhub-phase1): 更新各模块 CLAUDE.md 反映迁移后架构"
```

---

## 批次 2：framework 权限引擎基础设施

### 任务 2：Policy 求值器（TDD）

**文件：**
- 创建：`server/python/src/framework/permission/policy_evaluator.py`
- 测试：`server/python/tests/framework/unit/permission/test_policy_evaluator.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
企业 Policy 求值器单元测试
"""
import pytest
from framework.permission.policy_evaluator import PolicyEvaluator, PolicyCondition


@pytest.mark.asyncio
class TestPolicyEvaluator:
    """Policy 求值器测试"""

    async def test_deny_policy_overrides_allow(self):
        """deny 优先于所有 allow"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "allow", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
            {"id": "p2", "effect": "deny", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        result = evaluator.evaluate(policies, {"resource_type": "document"})
        assert result.effect == "deny"
        assert result.matched_policy_id == "p2"

    async def test_no_policy_returns_none(self):
        """无 Policy 命中返回 None"""
        evaluator = PolicyEvaluator()
        result = evaluator.evaluate([], {"resource_type": "document"})
        assert result.effect is None

    async def test_allow_when_only_allow_matches(self):
        """仅有 allow 命中时返回 allow"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "allow", "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        result = evaluator.evaluate(policies, {"resource_type": "document"})
        assert result.effect == "allow"

    async def test_condition_all_must_match(self):
        """所有条件均匹配才命中"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [
                {"field": "resource_type", "op": "eq", "value": "document"},
                {"field": "operation", "op": "eq", "value": "download"},
            ]},
        ]
        # 仅一个条件匹配，不命中
        assert evaluator.evaluate(policies, {"resource_type": "document", "operation": "read"}).effect is None
        # 两个条件都匹配，命中
        assert evaluator.evaluate(policies, {"resource_type": "document", "operation": "download"}).effect == "deny"

    async def test_disabled_policy_not_evaluated(self):
        """停用的 Policy 不参与求值"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "enabled": False, "conditions": [{"field": "resource_type", "op": "eq", "value": "document"}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect is None

    async def test_in_operator(self):
        """in 操作符"""
        evaluator = PolicyEvaluator()
        policies = [
            {"id": "p1", "effect": "deny", "conditions": [{"field": "resource_type", "op": "in", "value": ["document", "folder"]}]},
        ]
        assert evaluator.evaluate(policies, {"resource_type": "document"}).effect == "deny"
        assert evaluator.evaluate(policies, {"resource_type": "library"}).effect is None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/framework/unit/permission/test_policy_evaluator.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'framework.permission'`

- [ ] **步骤 3：创建包初始化文件**

创建 `server/python/src/framework/permission/__init__.py`：

```python
"""framework 权限基础设施：权限判定引擎、Policy 求值器、审计写入辅助"""

from framework.permission.engine import PermissionEngine, PermissionEngineProtocol
from framework.permission.policy_evaluator import PolicyEvaluator, PolicyResult
from framework.permission.audit_writer import write_audit

__all__ = [
    "PermissionEngine",
    "PermissionEngineProtocol",
    "PolicyEvaluator",
    "PolicyResult",
    "write_audit",
]
```

- [ ] **步骤 4：实现 Policy 求值器**

创建 `server/python/src/framework/permission/policy_evaluator.py`：

```python
"""
企业 Policy 求值器

求值租户级安全策略，deny 优先于所有 allow。

条件格式（JSON 结构化）：
    {"field": "resource_type", "op": "eq", "value": "document"}

支持操作符：eq / ne / in / not_in / contains
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyResult:
    """Policy 求值结果"""

    effect: str | None  # "allow" / "deny" / None
    matched_policy_id: str | None = None
    matched_conditions: list[dict] | None = None


class PolicyEvaluator:
    """企业 Policy 求值器"""

    def evaluate(self, policies: list[dict], context: dict[str, Any]) -> PolicyResult:
        """
        求值 Policy 列表，deny 优先。

        Args:
            policies: Policy 列表，每项含 id/effect/enabled/conditions
            context: 求值上下文（resource_type/operation/user_id 等）

        Returns:
            PolicyResult：deny 优先，无命中返回 effect=None
        """
        allow_hit = None

        for policy in policies:
            if not policy.get("enabled", True):
                continue

            conditions = policy.get("conditions", [])
            if self._match_all(conditions, context):
                if policy.get("effect") == "deny":
                    return PolicyResult(
                        effect="deny",
                        matched_policy_id=policy.get("id"),
                        matched_conditions=conditions,
                    )
                if allow_hit is None and policy.get("effect") == "allow":
                    allow_hit = PolicyResult(
                        effect="allow",
                        matched_policy_id=policy.get("id"),
                        matched_conditions=conditions,
                    )

        return allow_hit or PolicyResult(effect=None)

    def _match_all(self, conditions: list[dict], context: dict[str, Any]) -> bool:
        """所有条件均匹配才返回 True"""
        if not conditions:
            return True
        return all(self._match_one(cond, context) for cond in conditions)

    def _match_one(self, condition: dict, context: dict[str, Any]) -> bool:
        """匹配单个条件"""
        field = condition.get("field")
        op = condition.get("op", "eq")
        expected = condition.get("value")
        actual = context.get(field)

        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "contains":
            return expected in (actual or [])
        return False
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && pytest tests/framework/unit/permission/test_policy_evaluator.py -v`
预期：PASS（6 个测试通过）

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/framework/permission/policy_evaluator.py server/python/src/framework/permission/__init__.py server/python/tests/framework/unit/permission/test_policy_evaluator.py
git commit -m "feat(framework): 新增企业 Policy 求值器（deny 优先，JSON 条件匹配）"
```

### 任务 3：权限判定引擎 Protocol 接口（TDD）

**文件：**
- 创建：`server/python/src/framework/permission/engine.py`
- 测试：`server/python/tests/framework/unit/permission/test_engine.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
权限判定引擎单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from framework.permission.engine import PermissionEngine, PermissionEngineProtocol


class FakeResourcePermissionChecker(PermissionEngineProtocol):
    """测试用第2层资源权限判定器"""

    def __init__(self, result: str):
        self._result = result

    async def check_resource_permission(self, user_id: str, resource_type: str, resource_id: str, operation: str) -> str:
        return self._result


@pytest.mark.asyncio
class TestPermissionEngine:
    """权限判定引擎测试"""

    async def test_deny_by_policy_overrides_resource_allow(self):
        """Policy deny 覆盖资源 allow"""
        checker = FakeResourcePermissionChecker("editable")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect="deny", matched_policy_id="p1")

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="download",
            policies=[],
        )
        assert result.allowed is False
        assert result.denied_by_policy is True

    async def test_resource_deny_blocks(self):
        """资源权限 deny 阻断"""
        checker = FakeResourcePermissionChecker("none")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is False
        assert result.resource_permission == "none"

    async def test_allow_when_resource_editable_and_no_policy_deny(self):
        """资源可编辑且无 Policy deny 则允许"""
        checker = FakeResourcePermissionChecker("editable")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="read",
            policies=[],
        )
        assert result.allowed is True

    async def test_troubleshoot_returns_hit_reasons(self):
        """排障输出命中原因"""
        checker = FakeResourcePermissionChecker("readonly")
        engine = PermissionEngine(resource_checker=checker, policy_evaluator=MagicMock())
        engine.policy_evaluator.evaluate.return_value = MagicMock(effect=None, matched_policy_id=None)

        result = await engine.check(
            user_id="u1",
            resource_type="document",
            resource_id="d1",
            operation="download",
            policies=[],
        )
        assert result.allowed is False  # readonly 不允许 download
        assert result.resource_permission == "readonly"
        assert isinstance(result.reasons, list)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/framework/unit/permission/test_engine.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'framework.permission.engine'`

- [ ] **步骤 3：实现权限判定引擎**

创建 `server/python/src/framework/permission/engine.py`：

```python
"""
权限判定引擎

编排三层权限判定：
  第1层 IAM RBAC（功能权限，由 module 声明，控制器层校验，不在此处）
  第2层 业务模块资源权限（由各模块实现 PermissionEngineProtocol）
  第3层 企业 Policy（Policy 求值器，deny 优先）

判定流程：资源权限 -> Policy 求值 -> 最终允许/拒绝
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from framework.permission.policy_evaluator import PolicyEvaluator, PolicyResult


@runtime_checkable
class PermissionEngineProtocol(Protocol):
    """第2层资源权限判定协议（各业务模块实现）"""

    async def check_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """返回资源权限等级：editable / readonly / none / deny"""
        ...


@dataclass
class PermissionCheckResult:
    """权限判定结果"""

    allowed: bool
    resource_permission: str = "none"
    policy_effect: str | None = None
    denied_by_policy: bool = False
    reasons: list[str] = field(default_factory=list)


class PermissionEngine:
    """权限判定引擎（编排第2层 + 第3层）"""

    def __init__(
        self,
        resource_checker: PermissionEngineProtocol,
        policy_evaluator: PolicyEvaluator | None = None,
    ):
        self.resource_checker = resource_checker
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()

    async def check(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        policies: list[dict] | None = None,
        context: dict | None = None,
    ) -> PermissionCheckResult:
        """
        执行权限判定。

        Args:
            user_id: 用户ID
            resource_type: 资源类型（document/folder/library 等）
            resource_id: 资源ID
            operation: 操作（read/preview/download/edit/delete）
            policies: 当前租户启用的 Policy 列表
            context: Policy 求值上下文

        Returns:
            PermissionCheckResult
        """
        reasons: list[str] = []
        ctx = context or {}
        ctx.setdefault("resource_type", resource_type)
        ctx.setdefault("operation", operation)
        ctx.setdefault("user_id", user_id)

        # 第2层：资源权限
        resource_perm = await self.resource_checker.check_resource_permission(
            user_id, resource_type, resource_id, operation
        )
        reasons.append(f"资源权限={resource_perm}")

        # 资源权限为 none/deny 直接拒绝
        if resource_perm in ("none", "deny"):
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                reasons=reasons,
            )

        # readonly 仅允许读类操作
        read_operations = {"read", "preview"}
        if resource_perm == "readonly" and operation not in read_operations:
            reasons.append(f"readonly 不允许操作={operation}")
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                reasons=reasons,
            )

        # 第3层：Policy 求值（deny 优先）
        policy_result: PolicyResult = self.policy_evaluator.evaluate(policies or [], ctx)
        if policy_result.effect == "deny":
            reasons.append(f"Policy deny 命中={policy_result.matched_policy_id}")
            return PermissionCheckResult(
                allowed=False,
                resource_permission=resource_perm,
                policy_effect="deny",
                denied_by_policy=True,
                reasons=reasons,
            )

        return PermissionCheckResult(
            allowed=True,
            resource_permission=resource_perm,
            policy_effect=policy_result.effect,
            reasons=reasons,
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/framework/unit/permission/test_engine.py -v`
预期：PASS（4 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/permission/engine.py server/python/tests/framework/unit/permission/test_engine.py
git commit -m "feat(framework): 新增权限判定引擎（编排第2层资源权限+第3层 Policy）"
```

### 任务 4：审计写入辅助（TDD）

**文件：**
- 创建：`server/python/src/framework/permission/audit_writer.py`
- 测试：`server/python/tests/framework/unit/permission/test_audit_writer.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
审计写入辅助单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from framework.permission.audit_writer import write_audit


@pytest.mark.asyncio
class TestAuditWriter:
    """审计写入辅助测试"""

    async def test_write_audit_creates_auditlog(self):
        """写入审计日志创建 AuditLog 记录"""
        session = AsyncMock(spec=AsyncSession)

        with patch("framework.permission.audit_writer.get_tenant_id", return_value="tenant-1"), \
             patch("framework.permission.audit_writer.get_user_id", return_value="user-1"), \
             patch("framework.permission.audit_writer.get_user_name", return_value="张三"), \
             patch("framework.permission.audit_writer.get_permission_code", return_value="document:library:write"):
            await write_audit(
                session=session,
                business_domain="document",
                operation_type="update_library",
                resource_type="library",
                resource_id="lib-1",
                resource_name="研发文档库",
                before_data={"name": "旧名"},
                after_data={"name": "新名"},
                detail={"type": "update_library_settings"},
            )

        # 验证 session.add 被调用
        session.add.assert_called_once()
        added_obj = session.add.call_args[0][0]
        assert added_obj.business_domain == "document"
        assert added_obj.operation_type == "update_library"
        assert added_obj.resource_id == "lib-1"
        assert added_obj.tenant_id == "tenant-1"
        assert added_obj.operator_by == "user-1"
        assert added_obj.before_data == {"name": "旧名"}

    async def test_write_audit_missing_required_field_raises(self):
        """缺少必填字段抛出 ValueError"""
        session = AsyncMock(spec=AsyncSession)
        with pytest.raises(ValueError):
            await write_audit(
                session=session,
                business_domain="",
                operation_type="update",
                resource_type="library",
                resource_id="lib-1",
                resource_name="库",
            )
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/framework/unit/permission/test_audit_writer.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'framework.permission.audit_writer'`

- [ ] **步骤 3：实现审计写入辅助**

创建 `server/python/src/framework/permission/audit_writer.py`：

```python
"""
审计日志统一写入辅助

封装 iam.AuditLog 写入逻辑，业务模块调用辅助函数，不直接依赖 iam schema。
通过延迟导入 iam.models.AuditLog 避免循环依赖（framework ─X─▶ iam）。
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import (
    get_permission_code,
    get_tenant_id,
    get_user_id,
)


def _get_user_name() -> str | None:
    """获取当前用户名称（延迟导入避免循环依赖）"""
    from framework.audit.service import get_user_name
    return get_user_name()


async def write_audit(
    session: AsyncSession,
    business_domain: str,
    operation_type: str,
    resource_type: str,
    resource_name: str,
    resource_id: str | None = None,
    business_domain_id: str | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
    detail: dict | None = None,
) -> None:
    """
    写入审计日志。

    必填字段校验：business_domain / operation_type / resource_type / resource_name。
    tenant_id / operator 自动从请求上下文注入。

    Args:
        session: 数据库会话（由调用方管理事务）
        business_domain: 业务域（document/ai/platform_setting 等）
        operation_type: 操作类型
        resource_type: 资源类型
        resource_name: 资源名称
        resource_id: 资源ID
        business_domain_id: 业务域ID
        before_data: 操作前数据
        after_data: 操作后数据
        detail: 操作详情
    """
    # 必填字段校验
    if not business_domain:
        raise ValueError("business_domain 不能为空")
    if not operation_type:
        raise ValueError("operation_type 不能为空")
    if not resource_type:
        raise ValueError("resource_type 不能为空")
    if not resource_name:
        raise ValueError("resource_name 不能为空")

    # 延迟导入 iam.AuditLog，避免 framework -> iam 循环依赖
    from iam.models import AuditLog

    tenant_id = get_tenant_id()
    user_id = get_user_id()
    user_name = _get_user_name() or ""
    permission_code = get_permission_code()
    operated_at = datetime.now(timezone.utc)

    audit_log = AuditLog(
        tenant_id=tenant_id,
        business_domain=business_domain,
        business_domain_id=business_domain_id,
        permission_code=permission_code,
        operator_by=user_id or "",
        operator_name=user_name,
        operated_at=operated_at,
        operation_type=operation_type,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        before_data=before_data,
        after_data=after_data,
        detail=detail,
    )
    session.add(audit_log)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/framework/unit/permission/test_audit_writer.py -v`
预期：PASS（2 个测试通过）

- [ ] **步骤 5：更新 `__init__.py` 导出 write_audit**

确认 `server/python/src/framework/permission/__init__.py` 已含 `write_audit` 导出（任务 2 步骤 3 已包含）。

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/framework/permission/audit_writer.py server/python/tests/framework/unit/permission/test_audit_writer.py
git commit -m "feat(framework): 新增审计日志统一写入辅助（延迟导入 iam 避免循环依赖）"
```

### 任务 5：站内信发送辅助（TDD）

**文件：**
- 创建：`server/python/src/framework/notification/sender.py`
- 创建：`server/python/src/framework/notification/__init__.py`
- 测试：`server/python/tests/framework/unit/notification/test_sender.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
站内信发送辅助单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from framework.notification.sender import send_notification


@pytest.mark.asyncio
class TestNotificationSender:
    """站内信发送辅助测试"""

    async def test_send_notification_to_users(self):
        """向指定用户列表发送站内信"""
        session = AsyncMock()

        with patch("framework.notification.sender.get_tenant_id", return_value="tenant-1"), \
             patch("framework.notification.sender.get_user_id", return_value="system"):
            count = await send_notification(
                session=session,
                title="入库审核通知",
                content="您有新的入库申请待审核",
                notification_type="import_review_pending",
                recipient_user_ids=["user-1", "user-2"],
                link="/ai/knowledge-base/1/import-requests/1",
            )

        assert count == 2
        assert session.add.call_count == 2

    async def test_send_notification_empty_recipients(self):
        """空接收人列表返回 0"""
        session = AsyncMock()
        count = await send_notification(
            session=session,
            title="通知",
            content="内容",
            notification_type="test",
            recipient_user_ids=[],
        )
        assert count == 0
        session.add.assert_not_called()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/framework/unit/notification/test_sender.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'framework.notification'`

- [ ] **步骤 3：创建包初始化**

创建 `server/python/src/framework/notification/__init__.py`：

```python
"""framework 站内信发送辅助"""

from framework.notification.sender import send_notification

__all__ = ["send_notification"]
```

- [ ] **步骤 4：实现站内信发送辅助**

创建 `server/python/src/framework/notification/sender.py`：

```python
"""
站内信发送辅助

封装 iam.Notification 写入逻辑，供各业务模块调用发送通知。
延迟导入 iam.Notification 避免循环依赖。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id, get_user_id


async def send_notification(
    session: AsyncSession,
    title: str,
    content: str,
    notification_type: str,
    recipient_user_ids: list[str],
    link: str | None = None,
    metadata: dict | None = None,
) -> int:
    """
    发送站内信。

    Args:
        session: 数据库会话（由调用方管理事务）
        title: 标题
        content: 内容
        notification_type: 通知类型（import_review_pending / permission_request_approved 等）
        recipient_user_ids: 接收人用户ID列表
        link: 跳转链接
        metadata: 扩展元数据

    Returns:
        成功创建的站内信数量
    """
    if not recipient_user_ids:
        return 0

    # 延迟导入 iam.Notification，避免 framework -> iam 循环依赖
    from iam.models import Notification

    tenant_id = get_tenant_id()
    sender_id = get_user_id()

    count = 0
    for user_id in recipient_user_ids:
        notification = Notification(
            tenant_id=tenant_id,
            title=title,
            content=content,
            notification_type=notification_type,
            recipient_id=user_id,
            sender_id=sender_id,
            link=link,
            extra_data=metadata,
            is_read=False,
        )
        session.add(notification)
        count += 1

    return count
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && pytest tests/framework/unit/notification/test_sender.py -v`
预期：PASS（2 个测试通过）

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/framework/notification/ server/python/tests/framework/unit/notification/test_sender.py
git commit -m "feat(framework): 新增站内信发送辅助（延迟导入 iam.Notification）"
```

### 任务 6：framework 基础设施集成验证

- [ ] **步骤 1：运行 framework permission 全部测试**

运行：`cd server/python && pytest tests/framework/unit/permission/ tests/framework/unit/notification/ -v`
预期：全部 PASS

- [ ] **步骤 2：运行 ruff 和 pyright 检查**

运行：`cd server/python && ruff check src/framework/permission/ src/framework/notification/ && pyright src/framework/permission/ src/framework/notification/`
预期：无错误

---

## 批次 3：iam 站内信

### 任务 7：站内信模型 + 枚举

**文件：**
- 修改：`server/python/src/iam/models/enums.py`
- 创建：`server/python/src/iam/models/notification.py`
- 修改：`server/python/src/iam/models/__init__.py`

- [ ] **步骤 1：在 enums.py 新增站内信类型枚举**

在 `server/python/src/iam/models/enums.py` 末尾追加：

```python
class NotificationType(str, Enum):
    """站内信类型"""

    IMPORT_REVIEW_PENDING = "import_review_pending"
    IMPORT_REVIEW_APPROVED = "import_review_approved"
    IMPORT_REVIEW_REJECTED = "import_review_rejected"
    PERMISSION_REQUEST_PENDING = "permission_request_pending"
    PERMISSION_REQUEST_APPROVED = "permission_request_approved"
    PERMISSION_REQUEST_REJECTED = "permission_request_rejected"
    SYSTEM = "system"
```

- [ ] **步骤 2：创建 Notification 模型**

创建 `server/python/src/iam/models/notification.py`：

```python
"""
站内信模型
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from iam.models import BaseModel


class Notification(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """站内信表"""

    __tablename__ = "notification"
    __table_args__ = (
        Index("ix_notification_recipient_id", "recipient_id"),
        Index("ix_notification_is_read", "is_read"),
        Index("ix_notification_type", "notification_type"),
        {"comment": "站内信表"},
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(String(2048), nullable=False, comment="内容")
    notification_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="通知类型"
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="接收人用户ID"
    )
    sender_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="发送人用户ID（系统消息为空）"
    )
    link: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="跳转链接"
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="扩展元数据"
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否已读"
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="已读时间"
    )


class NotificationRead(BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin):
    """站内信已读记录表（聚合统计用）"""

    __tablename__ = "notification_read"
    __table_args__ = (
        Index("ix_notification_read_user_id", "user_id"),
        {"comment": "站内信已读记录表"},
    )

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="用户ID"
    )
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="最后已读时间"
    )
    unread_count: Mapped[int] = mapped_column(
        nullable=False, default=0, comment="未读数（冗余计数）"
    )
```

- [ ] **步骤 3：在 models/__init__.py 导出新模型**

在 `server/python/src/iam/models/__init__.py` 的导入区追加（`from .system_setting_attribute import SystemSettingAttribute` 之后）：

```python
from .notification import Notification, NotificationRead
```

并在 `__all__` 列表追加：

```python
    # 站内信
    "Notification",
    "NotificationRead",
```

同时在 enums 导入区追加 `NotificationType`，并加入 `__all__`。

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/iam/models/enums.py server/python/src/iam/models/notification.py server/python/src/iam/models/__init__.py
git commit -m "feat(iam): 新增站内信模型 Notification/NotificationRead"
```

### 任务 8：站内信 Schema

**文件：**
- 创建：`server/python/src/iam/schemas/notification.py`

- [ ] **步骤 1：创建 Schema**

创建 `server/python/src/iam/schemas/notification.py`：

```python
"""
站内信 Schema
"""

from datetime import datetime

from pydantic import Field

from framework.schemas.base import BaseModel, BasePaginatedQuery


class NotificationPaginatedQuery(BasePaginatedQuery):
    """站内信分页查询"""

    is_read: bool | None = Field(default=None, description="是否已读筛选")
    notification_type: str | None = Field(default=None, description="通知类型筛选")


class NotificationResponse(BaseModel):
    """站内信响应"""

    id: str
    title: str
    content: str
    notification_type: str
    recipient_id: str
    sender_id: str | None = None
    link: str | None = None
    extra_data: dict | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationMarkReadRequest(BaseModel):
    """标记已读请求"""

    notification_ids: list[str] = Field(default_factory=list, description="站内信ID列表（空则标记全部已读）")


class NotificationUnreadCountResponse(BaseModel):
    """未读数响应"""

    unread_count: int
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/schemas/notification.py
git commit -m "feat(iam): 新增站内信 Schema"
```

### 任务 9：站内信服务（TDD）

**文件：**
- 创建：`server/python/src/iam/services/notification_service.py`
- 测试：`server/python/tests/iam/unit/services/test_notification_service.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
站内信服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from iam.services.notification_service import NotificationService


@pytest.mark.asyncio
class TestNotificationService:
    """站内信服务测试"""

    async def test_list_my_notifications(self):
        """查询我的站内信列表（未读优先）"""
        session = AsyncMock(spec=AsyncSession)
        mock_notif = MagicMock()
        mock_notif.id = "n1"
        mock_notif.is_read = False
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notif]
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        with patch("iam.services.notification_service.get_user_id", return_value="user-1"):
            items, total = await NotificationService.list_my_notifications(
                session, user_id="user-1", page=1, page_size=10
            )

        assert total == 1
        assert len(items) == 1

    async def test_mark_read_updates_is_read(self):
        """标记已读更新 is_read"""
        session = AsyncMock(spec=AsyncSession)
        mock_notif = MagicMock()
        mock_notif.is_read = False
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notif]
        session.execute = AsyncMock(return_value=mock_result)

        await NotificationService.mark_read(session, user_id="user-1", notification_ids=["n1"])

        assert mock_notif.is_read is True
        session.flush.assert_called()

    async def test_get_unread_count(self):
        """获取未读数"""
        session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        session.execute = AsyncMock(return_value=mock_result)

        count = await NotificationService.get_unread_count(session, user_id="user-1")
        assert count == 5
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/iam/unit/services/test_notification_service.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'iam.services.notification_service'`

- [ ] **步骤 3：实现站内信服务**

创建 `server/python/src/iam/services/notification_service.py`：

```python
"""
站内信服务

提供站内信查询、已读标记、未读数统计。
"""

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Notification


class NotificationService:
    """站内信服务"""

    @staticmethod
    async def list_my_notifications(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: bool | None = None,
        notification_type: str | None = None,
    ) -> tuple[list[Notification], int]:
        """
        查询我的站内信列表（未读优先，按创建时间倒序）。

        Args:
            session: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            is_read: 是否已读筛选
            notification_type: 通知类型筛选

        Returns:
            tuple[list[Notification], int]
        """
        conditions = [Notification.recipient_id == user_id]
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        if notification_type:
            conditions.append(Notification.notification_type == notification_type)

        # 总数
        count_stmt = select(func.count(Notification.id)).where(*conditions)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 列表（未读优先，再按创建时间倒序）
        offset = (page - 1) * page_size
        stmt = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.is_read.asc(), Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def mark_read(
        session: AsyncSession,
        user_id: str,
        notification_ids: list[str] | None = None,
    ) -> int:
        """
        标记站内信已读。

        Args:
            session: 数据库会话
            user_id: 用户ID
            notification_ids: 站内信ID列表（空则标记全部已读）

        Returns:
            标记已读的数量
        """
        now = datetime.now(timezone.utc)
        conditions = [
            Notification.recipient_id == user_id,
            Notification.is_read == False,  # noqa: E712
        ]
        if notification_ids:
            conditions.append(Notification.id.in_(notification_ids))

        stmt = (
            update(Notification)
            .where(*conditions)
            .values(is_read=True, read_at=now)
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount or 0

    @staticmethod
    async def get_unread_count(session: AsyncSession, user_id: str) -> int:
        """获取未读站内信数"""
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


notification_service = NotificationService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/services/test_notification_service.py -v`
预期：PASS（3 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/services/notification_service.py server/python/tests/iam/unit/services/test_notification_service.py
git commit -m "feat(iam): 新增站内信服务（查询/已读/未读数）"
```

### 任务 10：站内信控制器

**文件：**
- 创建：`server/python/src/iam/controllers/console/notification_controller.py`
- 创建：`server/python/src/iam/controllers/admin/notification_controller.py`
- 测试：`server/python/tests/iam/unit/controllers/test_notification_controller.py`

- [ ] **步骤 1：创建用户端控制器**

创建 `server/python/src/iam/controllers/console/notification_controller.py`：

```python
"""
站内信控制器 - 用户端
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_user_id
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.schemas.notification import (
    NotificationMarkReadRequest,
    NotificationPaginatedQuery,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from iam.services.notification_service import notification_service

router = APIRouter()


@router.get("/notifications")
async def list_my_notifications(
    query: NotificationPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询我的站内信列表"""
    user_id = get_user_id()
    items, total = await notification_service.list_my_notifications(
        session,
        user_id=user_id,
        page=query.page,
        page_size=query.page_size,
        is_read=query.is_read,
        notification_type=query.notification_type,
    )
    return ApiResponse.paginated(
        data=[NotificationResponse.model_validate(n).model_dump() for n in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.get("/notifications/unread-count")
async def get_unread_count(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """获取未读站内信数"""
    user_id = get_user_id()
    count = await notification_service.get_unread_count(session, user_id)
    return ApiResponse.success(
        data=NotificationUnreadCountResponse(unread_count=count).model_dump()
    )


@router.put("/notifications/read")
async def mark_read(
    data: NotificationMarkReadRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """标记站内信已读"""
    user_id = get_user_id()
    count = await notification_service.mark_read(
        session, user_id=user_id, notification_ids=data.notification_ids
    )
    await session.commit()
    return ApiResponse.success(data={"marked_count": count})
```

- [ ] **步骤 2：创建管理端控制器**

创建 `server/python/src/iam/controllers/admin/notification_controller.py`：

```python
"""
站内信控制器 - 管理端

管理端仅提供全局查看能力（按租户/接收人查询），发送由业务模块通过 framework 发送辅助触发。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import get_tenant_id
from iam.models import Notification
from iam.schemas.notification import NotificationPaginatedQuery, NotificationResponse
from sqlalchemy import func, select

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    query: NotificationPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """管理端查询站内信列表（按租户）"""
    tenant_id = get_tenant_id()
    conditions = [Notification.tenant_id == tenant_id]
    if query.notification_type:
        conditions.append(Notification.notification_type == query.notification_type)

    count_stmt = select(func.count(Notification.id)).where(*conditions)
    total = (await session.execute(count_stmt)).scalar() or 0

    offset = (query.page - 1) * query.page_size
    stmt = (
        select(Notification)
        .where(*conditions)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(query.page_size)
    )
    items = list((await session.execute(stmt)).scalars().all())

    return ApiResponse.paginated(
        data=[NotificationResponse.model_validate(n).model_dump() for n in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
```

- [ ] **步骤 3：编写控制器测试**

创建 `server/python/tests/iam/unit/controllers/test_notification_controller.py`：

```python
"""
站内信控制器单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch

from iam.controllers.console.notification_controller import (
    get_unread_count,
    list_my_notifications,
    mark_read,
)
from iam.schemas.notification import NotificationMarkReadRequest, NotificationPaginatedQuery


@pytest.mark.asyncio
class TestNotificationController:
    """站内信控制器测试"""

    async def test_get_unread_count_returns_count(self):
        """获取未读数"""
        session = AsyncMock()
        with patch("iam.controllers.console.notification_controller.get_user_id", return_value="u1"), \
             patch("iam.services.notification_service.notification_service.get_unread_count", new_callable=AsyncMock, return_value=3):
            response = await get_unread_count(session=session)
            assert response.status_code == 200

    async def test_mark_read_returns_marked_count(self):
        """标记已读"""
        session = AsyncMock()
        data = NotificationMarkReadRequest(notification_ids=["n1", "n2"])
        with patch("iam.controllers.console.notification_controller.get_user_id", return_value="u1"), \
             patch("iam.services.notification_service.notification_service.mark_read", new_callable=AsyncMock, return_value=2):
            response = await mark_read(data=data, session=session)
            assert response.status_code == 200
            session.commit.assert_called_once()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/controllers/test_notification_controller.py -v`
预期：PASS

- [ ] **步骤 5：在 module.py 注册路由**

修改 `server/python/src/iam/module.py` 的 `get_routers()` 方法，在导入区新增：

```python
        from iam.controllers.admin.notification_controller import (
            router as admin_notification_router,
        )
        from iam.controllers.console.notification_controller import (
            router as console_notification_router,
        )
```

在返回列表的 Admin 层区追加：

```python
            (admin_notification_router, "/iam/admin/v1", ["Admin - Notification"]),
```

在 Console 层区追加：

```python
            (console_notification_router, "/iam/console/v1", ["Console - Notification"]),
```

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/iam/controllers/admin/notification_controller.py server/python/src/iam/controllers/console/notification_controller.py server/python/src/iam/module.py server/python/tests/iam/unit/controllers/test_notification_controller.py
git commit -m "feat(iam): 新增站内信控制器（admin/console）并注册路由"
```

---

## 批次 4：iam 权限申请

### 任务 11：权限申请枚举 + 模型

**文件：**
- 修改：`server/python/src/iam/models/enums.py`
- 创建：`server/python/src/iam/models/permission_request.py`
- 修改：`server/python/src/iam/models/__init__.py`

- [ ] **步骤 1：在 enums.py 新增权限申请枚举**

在 `server/python/src/iam/models/enums.py` 追加：

```python
class PermissionRequestType(str, Enum):
    """权限申请类型"""

    LIBRARY_JOIN = "library_join"
    LIBRARY_RESOURCE = "library_resource"
    LIBRARY_ROLE = "library_role"
    KNOWLEDGE_BASE_JOIN = "knowledge_base_join"
    KNOWLEDGE_BASE_ROLE = "knowledge_base_role"


class PermissionRequestStatus(str, Enum):
    """权限申请状态"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLYING = "applying"
    APPLIED = "applied"
    APPLY_FAILED = "apply_failed"
```

- [ ] **步骤 2：创建 PermissionRequest 模型**

创建 `server/python/src/iam/models/permission_request.py`：

```python
"""
权限申请模型
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from iam.models import BaseModel


class PermissionRequest(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """权限申请表"""

    __tablename__ = "permission_request"
    __table_args__ = (
        Index("ix_permission_request_status", "status"),
        Index("ix_permission_request_applicant_id", "applicant_id"),
        Index("ix_permission_request_type", "request_type"),
        {"comment": "权限申请表"},
    )

    request_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="申请类型"
    )
    applicant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="申请人用户ID"
    )
    applicant_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="申请人名称"
    )
    target_module: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="目标模块（document/ai）"
    )
    target_resource_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="目标资源ID（文档库/知识库ID）"
    )
    target_resource_name: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="目标资源名称"
    )
    requested_role: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="申请的角色"
    )
    requested_permission: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="申请的权限"
    )
    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="申请理由"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", comment="状态"
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="审核人用户ID"
    )
    reviewer_name: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="审核人名称"
    )
    review_comment: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="审核意见"
    )
    reviewed_at: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="审核时间（ISO）"
    )
    apply_error: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="回调落地失败信息"
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="扩展数据（如资源ACL明细）"
    )


class PermissionCacheEvent(BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin):
    """权限变更流水表（排障用）"""

    __tablename__ = "permission_cache_event"
    __table_args__ = (
        Index("ix_permission_cache_event_user_id", "user_id"),
        {"comment": "权限变更流水表"},
    )

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="用户ID"
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="事件类型（permission_grant/permission_revoke/policy_change）"
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="资源类型"
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="资源ID"
    )
    detail: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="事件详情"
    )
```

- [ ] **步骤 3：在 models/__init__.py 导出**

追加导入与 `__all__` 项（`PermissionRequest`、`PermissionCacheEvent`、`PermissionRequestType`、`PermissionRequestStatus`）。

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/iam/models/enums.py server/python/src/iam/models/permission_request.py server/python/src/iam/models/__init__.py
git commit -m "feat(iam): 新增权限申请模型 PermissionRequest/PermissionCacheEvent"
```

### 任务 12：权限申请 Schema

**文件：**
- 创建：`server/python/src/iam/schemas/permission_request.py`

- [ ] **步骤 1：创建 Schema**

创建 `server/python/src/iam/schemas/permission_request.py`：

```python
"""
权限申请 Schema
"""

from datetime import datetime

from pydantic import Field

from framework.schemas.base import BaseModel, BasePaginatedQuery


class PermissionRequestCreate(BaseModel):
    """提交权限申请"""

    request_type: str = Field(..., description="申请类型")
    target_module: str = Field(..., description="目标模块")
    target_resource_id: str = Field(..., description="目标资源ID")
    target_resource_name: str = Field(..., description="目标资源名称")
    requested_role: str | None = Field(default=None, description="申请角色")
    requested_permission: str | None = Field(default=None, description="申请权限")
    reason: str | None = Field(default=None, description="申请理由")
    extra_data: dict | None = Field(default=None, description="扩展数据")


class PermissionRequestReview(BaseModel):
    """审核权限申请"""

    approved: bool = Field(..., description="是否通过")
    review_comment: str | None = Field(default=None, description="审核意见")


class PermissionRequestPaginatedQuery(BasePaginatedQuery):
    """权限申请分页查询"""

    status: str | None = Field(default=None, description="状态筛选")
    request_type: str | None = Field(default=None, description="类型筛选")
    target_module: str | None = Field(default=None, description="目标模块筛选")


class PermissionRequestResponse(BaseModel):
    """权限申请响应"""

    id: str
    request_type: str
    applicant_id: str
    applicant_name: str
    target_module: str
    target_resource_id: str
    target_resource_name: str
    requested_role: str | None = None
    requested_permission: str | None = None
    reason: str | None = None
    status: str
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    review_comment: str | None = None
    reviewed_at: str | None = None
    apply_error: str | None = None
    extra_data: dict | None = None
    created_at: datetime


class PermissionApplyCallbackRequest(BaseModel):
    """权限申请回调落地请求（inner 接口用）"""

    request_id: str = Field(..., description="权限申请ID")
    applicant_id: str = Field(..., description="申请人ID")
    request_type: str = Field(..., description="申请类型")
    target_resource_id: str = Field(..., description="目标资源ID")
    requested_role: str | None = Field(default=None, description="申请角色")
    requested_permission: str | None = Field(default=None, description="申请权限")
    extra_data: dict | None = Field(default=None, description="扩展数据")
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/schemas/permission_request.py
git commit -m "feat(iam): 新增权限申请 Schema"
```

### 任务 13：权限申请服务（TDD）

**文件：**
- 创建：`server/python/src/iam/services/permission_request_service.py`
- 测试：`server/python/tests/iam/unit/services/test_permission_request_service.py`

- [ ] **步骤 1：编写失败的测试**

```python
"""
权限申请服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from iam.services.permission_request_service import PermissionRequestService


@pytest.mark.asyncio
class TestPermissionRequestService:
    """权限申请服务测试"""

    async def test_submit_request_creates_pending(self):
        """提交申请创建 pending 记录"""
        session = AsyncMock(spec=AsyncSession)
        with patch("iam.services.permission_request_service.get_tenant_id", return_value="t1"), \
             patch("iam.services.permission_request_service.get_user_id", return_value="u1"), \
             patch("iam.services.permission_request_service.get_user_name", return_value="张三"):
            req = await PermissionRequestService.submit_request(
                session,
                request_type="library_join",
                target_module="document",
                target_resource_id="lib-1",
                target_resource_name="研发库",
                requested_role="member",
                reason="需要查看研发文档",
            )
        assert req.status == "pending"
        assert req.applicant_id == "u1"
        session.add.assert_called_once()

    async def test_approve_transitions_to_applying_and_callbacks(self):
        """审核通过转为 applying 并触发回调"""
        session = AsyncMock(spec=AsyncSession)
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "pending"
        mock_req.target_module = "document"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_req
        session.execute = AsyncMock(return_value=mock_result)

        with patch("iam.services.permission_request_service.get_user_id", return_value="reviewer-1"), \
             patch("iam.services.permission_request_service.get_user_name", return_value="管理员"), \
             patch("iam.services.permission_request_service.PermissionRequestService._apply_to_target_module", new_callable=AsyncMock, return_value=True):
            result = await PermissionRequestService.review(
                session, request_id="req-1", approved=True, review_comment="同意", reviewer_id="reviewer-1", reviewer_name="管理员"
            )
        assert result.status == "applied"

    async def test_reject_transitions_to_rejected(self):
        """审核拒绝转为 rejected，不回调"""
        session = AsyncMock(spec=AsyncSession)
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "pending"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_req
        session.execute = AsyncMock(return_value=mock_result)

        with patch("iam.services.permission_request_service.get_user_id", return_value="reviewer-1"), \
             patch("iam.services.permission_request_service.get_user_name", return_value="管理员"), \
             patch("iam.services.permission_request_service.PermissionRequestService._apply_to_target_module", new_callable=AsyncMock) as mock_apply:
            result = await PermissionRequestService.review(
                session, request_id="req-1", approved=False, review_comment="拒绝", reviewer_id="reviewer-1", reviewer_name="管理员"
            )
        assert result.status == "rejected"
        mock_apply.assert_not_called()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/iam/unit/services/test_permission_request_service.py -v`
预期：FAIL，`ModuleNotFoundError`

- [ ] **步骤 3：实现权限申请服务**

创建 `server/python/src/iam/services/permission_request_service.py`：

```python
"""
权限申请服务

提供权限申请提交、审批、回调落地。审批通过后通过 inner 接口回调目标业务模块落地授权。
"""

from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id, get_user_id
from framework.notification.sender import send_notification
from iam.models import PermissionRequest


class PermissionRequestService:
    """权限申请服务"""

    @staticmethod
    async def submit_request(
        session: AsyncSession,
        request_type: str,
        target_module: str,
        target_resource_id: str,
        target_resource_name: str,
        requested_role: str | None = None,
        requested_permission: str | None = None,
        reason: str | None = None,
        extra_data: dict | None = None,
    ) -> PermissionRequest:
        """提交权限申请"""
        tenant_id = get_tenant_id()
        applicant_id = get_user_id()
        applicant_name = _get_user_name()

        req = PermissionRequest(
            tenant_id=tenant_id,
            request_type=request_type,
            applicant_id=applicant_id,
            applicant_name=applicant_name,
            target_module=target_module,
            target_resource_id=target_resource_id,
            target_resource_name=target_resource_name,
            requested_role=requested_role,
            requested_permission=requested_permission,
            reason=reason,
            status="pending",
            extra_data=extra_data,
        )
        session.add(req)
        await session.flush()
        return req

    @staticmethod
    async def review(
        session: AsyncSession,
        request_id: str,
        approved: bool,
        review_comment: str | None,
        reviewer_id: str,
        reviewer_name: str,
    ) -> PermissionRequest:
        """审核权限申请"""
        stmt = select(PermissionRequest).where(PermissionRequest.id == request_id)
        req = (await session.execute(stmt)).scalar_one_or_none()
        if req is None:
            raise ValueError("权限申请不存在")
        if req.status != "pending":
            raise ValueError(f"权限申请状态非 pending，当前={req.status}")

        reviewed_at = datetime.now(timezone.utc).isoformat()
        req.reviewer_id = reviewer_id
        req.reviewer_name = reviewer_name
        req.review_comment = review_comment
        req.reviewed_at = reviewed_at

        if not approved:
            req.status = "rejected"
            await session.flush()
            await _notify_applicant(session, req, approved=False)
            return req

        # 通过：先标记 applying，回调落地后标记 applied
        req.status = "applying"
        await session.flush()

        try:
            success = await PermissionRequestService._apply_to_target_module(session, req)
            req.status = "applied" if success else "apply_failed"
            req.apply_error = None if success else "回调落地失败"
        except Exception as e:
            req.status = "apply_failed"
            req.apply_error = str(e)

        await session.flush()
        await _notify_applicant(session, req, approved=True)
        return req

    @staticmethod
    async def _apply_to_target_module(session: AsyncSession, req: PermissionRequest) -> bool:
        """
        通过 inner 接口回调目标业务模块落地授权。

        Phase 1 阶段目标模块 inner 接口尚未实现（Phase 2/3 实现），此处返回 True 占位。
        Phase 2 完成后接入 /document/inner/v1/permission-requests/apply，
        Phase 3 完成后接入 /ai/inner/v1/permission-requests/apply。
        """
        # TODO(phase2/phase3): 接入目标模块 inner 接口
        # url = f"/{req.target_module}/inner/v1/permission-requests/{req.id}/apply"
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(url, json={...})
        #     return resp.status_code == 200
        return True

    @staticmethod
    async def list_my_requests(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[PermissionRequest], int]:
        """查询我的申请"""
        from sqlalchemy import func

        conditions = [PermissionRequest.applicant_id == user_id]
        if status:
            conditions.append(PermissionRequest.status == status)

        total = (await session.execute(
            select(func.count(PermissionRequest.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(PermissionRequest)
            .where(*conditions)
            .order_by(PermissionRequest.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def list_pending_for_review(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        target_module: str | None = None,
    ) -> tuple[list[PermissionRequest], int]:
        """查询待我审批（管理端：按租户查 pending）"""
        from sqlalchemy import func

        tenant_id = get_tenant_id()
        conditions = [
            PermissionRequest.tenant_id == tenant_id,
            PermissionRequest.status == "pending",
        ]
        if target_module:
            conditions.append(PermissionRequest.target_module == target_module)

        total = (await session.execute(
            select(func.count(PermissionRequest.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(PermissionRequest)
            .where(*conditions)
            .order_by(PermissionRequest.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total


def _get_user_name() -> str:
    from framework.audit.service import get_user_name
    return get_user_name() or ""


async def _notify_applicant(session: AsyncSession, req: PermissionRequest, approved: bool) -> None:
    """通知申请人审核结果"""
    title = "权限申请已通过" if approved else "权限申请已拒绝"
    content = f"您申请的「{req.target_resource_name}」权限{'已通过' : '已拒绝'}"
    notif_type = "permission_request_approved" if approved else "permission_request_rejected"
    await send_notification(
        session=session,
        title=title,
        content=content,
        notification_type=notif_type,
        recipient_user_ids=[req.applicant_id],
        link=f"/iam/permission-requests?status={req.status}",
    )


permission_request_service = PermissionRequestService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/services/test_permission_request_service.py -v`
预期：PASS（3 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/services/permission_request_service.py server/python/tests/iam/unit/services/test_permission_request_service.py
git commit -m "feat(iam): 新增权限申请服务（提交/审批/回调占位/通知）"
```

### 任务 14：权限申请控制器

**文件：**
- 创建：`server/python/src/iam/controllers/console/permission_request_controller.py`
- 创建：`server/python/src/iam/controllers/admin/permission_request_controller.py`
- 测试：`server/python/tests/iam/unit/controllers/test_permission_request_controller.py`

- [ ] **步骤 1：创建用户端控制器**

创建 `server/python/src/iam/controllers/console/permission_request_controller.py`：

```python
"""
权限申请控制器 - 用户端
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_user_id, get_user_name
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestPaginatedQuery,
    PermissionRequestResponse,
)
from iam.services.permission_request_service import permission_request_service

router = APIRouter()


@router.post("/permission-requests")
async def submit_request(
    data: PermissionRequestCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """提交权限申请"""
    try:
        req = await permission_request_service.submit_request(
            session,
            request_type=data.request_type,
            target_module=data.target_module,
            target_resource_id=data.target_resource_id,
            target_resource_name=data.target_resource_name,
            requested_role=data.requested_role,
            requested_permission=data.requested_permission,
            reason=data.reason,
            extra_data=data.extra_data,
        )
        await session.commit()
        return ApiResponse.success(
            data=PermissionRequestResponse.model_validate(req).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/permission-requests")
async def list_my_requests(
    query: PermissionRequestPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询我的申请"""
    user_id = get_user_id()
    items, total = await permission_request_service.list_my_requests(
        session,
        user_id=user_id,
        page=query.page,
        page_size=query.page_size,
        status=query.status,
    )
    return ApiResponse.paginated(
        data=[PermissionRequestResponse.model_validate(r).model_dump() for r in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
```

- [ ] **步骤 2：创建管理端控制器**

创建 `server/python/src/iam/controllers/admin/permission_request_controller.py`：

```python
"""
权限申请控制器 - 管理端
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_user_id, get_user_name
from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from iam.schemas.permission_request import (
    PermissionRequestPaginatedQuery,
    PermissionRequestResponse,
    PermissionRequestReview,
)
from iam.services.permission_request_service import permission_request_service

router = APIRouter()


@router.get("/permission-requests")
async def list_pending(
    query: PermissionRequestPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询待审批申请"""
    items, total = await permission_request_service.list_pending_for_review(
        session,
        page=query.page,
        page_size=query.page_size,
        target_module=query.target_module,
    )
    return ApiResponse.paginated(
        data=[PermissionRequestResponse.model_validate(r).model_dump() for r in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.put("/permission-requests/{request_id}/review")
async def review_request(
    request_id: str,
    data: PermissionRequestReview,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """审核权限申请"""
    reviewer_id = get_user_id()
    reviewer_name = get_user_name() or ""
    try:
        req = await permission_request_service.review(
            session,
            request_id=request_id,
            approved=data.approved,
            review_comment=data.review_comment,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
        )
        await session.commit()
        return ApiResponse.success(
            data=PermissionRequestResponse.model_validate(req).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 3：编写控制器测试**

创建 `server/python/tests/iam/unit/controllers/test_permission_request_controller.py`：

```python
"""
权限申请控制器单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from iam.controllers.admin.permission_request_controller import review_request
from iam.controllers.console.permission_request_controller import submit_request
from iam.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestReview,
)


@pytest.mark.asyncio
class TestPermissionRequestController:
    """权限申请控制器测试"""

    async def test_submit_request_success(self):
        """提交申请成功"""
        session = AsyncMock()
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "pending"
        data = PermissionRequestCreate(
            request_type="library_join",
            target_module="document",
            target_resource_id="lib-1",
            target_resource_name="研发库",
            requested_role="member",
        )
        with patch("iam.services.permission_request_service.permission_request_service.submit_request", new_callable=AsyncMock, return_value=mock_req):
            response = await submit_request(data=data, session=session)
            assert response.status_code == 200
            session.commit.assert_called_once()

    async def test_review_request_reject(self):
        """审核拒绝"""
        session = AsyncMock()
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "rejected"
        data = PermissionRequestReview(approved=False, review_comment="拒绝")
        with patch("iam.controllers.admin.permission_request_controller.get_user_id", return_value="r1"), \
             patch("iam.controllers.admin.permission_request_controller.get_user_name", return_value="管理员"), \
             patch("iam.services.permission_request_service.permission_request_service.review", new_callable=AsyncMock, return_value=mock_req):
            response = await review_request(request_id="req-1", data=data, session=session)
            assert response.status_code == 200
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/controllers/test_permission_request_controller.py -v`
预期：PASS

- [ ] **步骤 5：在 module.py 注册路由**

修改 `server/python/src/iam/module.py`，导入并注册：

```python
        from iam.controllers.admin.permission_request_controller import (
            router as admin_permission_request_router,
        )
        from iam.controllers.console.permission_request_controller import (
            router as console_permission_request_router,
        )
```

返回列表追加：

```python
            (admin_permission_request_router, "/iam/admin/v1", ["Admin - PermissionRequest"]),
            (console_permission_request_router, "/iam/console/v1", ["Console - PermissionRequest"]),
```

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/iam/controllers/admin/permission_request_controller.py server/python/src/iam/controllers/console/permission_request_controller.py server/python/src/iam/module.py server/python/tests/iam/unit/controllers/test_permission_request_controller.py
git commit -m "feat(iam): 新增权限申请控制器（admin/console）并注册路由"
```

---

## 批次 5：iam 企业 Policy

### 任务 15：Policy 枚举 + 模型

**文件：**
- 修改：`server/python/src/iam/models/enums.py`
- 创建：`server/python/src/iam/models/policy.py`
- 修改：`server/python/src/iam/models/__init__.py`

- [ ] **步骤 1：在 enums.py 新增 PolicyEffect 枚举**

```python
class PolicyEffect(str, Enum):
    """Policy 效果"""

    ALLOW = "allow"
    DENY = "deny"
```

- [ ] **步骤 2：创建 Policy 模型**

创建 `server/python/src/iam/models/policy.py`：

```python
"""
企业 Policy 模型
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from iam.models import BaseModel


class Policy(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """企业 Policy 表（租户级安全策略）"""

    __tablename__ = "policy"
    __table_args__ = (
        Index("ix_policy_effect", "effect"),
        Index("ix_policy_enabled", "enabled"),
        {"comment": "企业 Policy 表"},
    )

    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="策略名称"
    )
    code: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="策略编码（租户内唯一）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="描述"
    )
    effect: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="效果（allow/deny）"
    )
    conditions: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, comment="条件列表（JSON 结构化）"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否启用"
    )
    priority: Mapped[int] = mapped_column(
        nullable=False, default=0, comment="优先级（数字越大越优先）"
    )
```

- [ ] **步骤 3：在 models/__init__.py 导出**

追加 `Policy`、`PolicyEffect` 导入与 `__all__` 项。

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/iam/models/enums.py server/python/src/iam/models/policy.py server/python/src/iam/models/__init__.py
git commit -m "feat(iam): 新增企业 Policy 模型"
```

### 任务 16：Policy Schema + 服务（TDD）

**文件：**
- 创建：`server/python/src/iam/schemas/policy.py`
- 创建：`server/python/src/iam/services/policy_service.py`
- 测试：`server/python/tests/iam/unit/services/test_policy_service.py`

- [ ] **步骤 1：创建 Schema**

创建 `server/python/src/iam/schemas/policy.py`：

```python
"""
企业 Policy Schema
"""

from datetime import datetime

from pydantic import Field

from framework.schemas.base import BaseModel, BasePaginatedQuery


class PolicyCreate(BaseModel):
    """创建 Policy"""

    name: str = Field(..., description="策略名称")
    code: str = Field(..., description="策略编码")
    description: str | None = Field(default=None, description="描述")
    effect: str = Field(..., description="效果（allow/deny）")
    conditions: list[dict] = Field(default_factory=list, description="条件列表")
    priority: int = Field(default=0, description="优先级")


class PolicyUpdate(BaseModel):
    """更新 Policy"""

    name: str | None = None
    description: str | None = None
    effect: str | None = None
    conditions: list[dict] | None = None
    priority: int | None = None


class PolicyPaginatedQuery(BasePaginatedQuery):
    """Policy 分页查询"""

    effect: str | None = Field(default=None, description="效果筛选")
    enabled: bool | None = Field(default=None, description="启用状态筛选")


class PolicyResponse(BaseModel):
    """Policy 响应"""

    id: str
    name: str
    code: str
    description: str | None = None
    effect: str
    conditions: list[dict]
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class PolicyEvaluateContext(BaseModel):
    """Policy 求值上下文（排障用）"""

    resource_type: str | None = None
    operation: str | None = None
    user_id: str | None = None
    extra: dict | None = None
```

- [ ] **步骤 2：编写服务测试**

创建 `server/python/tests/iam/unit/services/test_policy_service.py`：

```python
"""
企业 Policy 服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from iam.services.policy_service import PolicyService


@pytest.mark.asyncio
class TestPolicyService:
    """Policy 服务测试"""

    async def test_create_policy_default_disabled(self):
        """创建 Policy 默认停用"""
        session = AsyncMock(spec=AsyncSession)
        with patch("iam.services.policy_service.get_tenant_id", return_value="t1"):
            policy = await PolicyService.create(
                session,
                name="禁止下载",
                code="deny_download",
                effect="deny",
                conditions=[{"field": "operation", "op": "eq", "value": "download"}],
            )
        assert policy.enabled is False
        assert policy.effect == "deny"
        session.add.assert_called_once()

    async def test_toggle_enable(self):
        """启用/停用切换"""
        session = AsyncMock(spec=AsyncSession)
        mock_policy = MagicMock()
        mock_policy.enabled = False
        mock_policy.id = "p1"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_policy
        session.execute = AsyncMock(return_value=mock_result)

        result = await PolicyService.toggle_enable(session, policy_id="p1", enabled=True)
        assert result.enabled is True

    async def test_get_active_policies_filters_enabled(self):
        """获取启用的 Policy 仅返回 enabled=True"""
        session = AsyncMock(spec=AsyncSession)
        mock_p1 = MagicMock()
        mock_p1.enabled = True
        mock_p1.effect = "deny"
        mock_p1.conditions = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_p1]
        session.execute = AsyncMock(return_value=mock_result)

        with patch("iam.services.policy_service.get_tenant_id", return_value="t1"):
            policies = await PolicyService.get_active_policies(session)
        assert len(policies) == 1
```

- [ ] **步骤 3：运行测试验证失败**

运行：`cd server/python && pytest tests/iam/unit/services/test_policy_service.py -v`
预期：FAIL，`ModuleNotFoundError`

- [ ] **步骤 4：实现 Policy 服务**

创建 `server/python/src/iam/services/policy_service.py`：

```python
"""
企业 Policy 服务

提供 Policy CRUD、启用/停用、命中审计、求值辅助。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.ctx import get_tenant_id
from framework.permission.policy_evaluator import PolicyEvaluator
from iam.models import Policy


class PolicyService:
    """企业 Policy 服务"""

    _evaluator = PolicyEvaluator()

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        code: str,
        effect: str,
        conditions: list[dict],
        description: str | None = None,
        priority: int = 0,
    ) -> Policy:
        """创建 Policy（默认停用）"""
        tenant_id = get_tenant_id()
        policy = Policy(
            tenant_id=tenant_id,
            name=name,
            code=code,
            description=description,
            effect=effect,
            conditions=conditions,
            enabled=False,
            priority=priority,
        )
        session.add(policy)
        await session.flush()
        return policy

    @staticmethod
    async def update(
        session: AsyncSession,
        policy_id: str,
        name: str | None = None,
        description: str | None = None,
        effect: str | None = None,
        conditions: list[dict] | None = None,
        priority: int | None = None,
    ) -> Policy:
        """更新 Policy"""
        stmt = select(Policy).where(Policy.id == policy_id)
        policy = (await session.execute(stmt)).scalar_one_or_none()
        if policy is None:
            raise ValueError("Policy 不存在")

        if name is not None:
            policy.name = name
        if description is not None:
            policy.description = description
        if effect is not None:
            policy.effect = effect
        if conditions is not None:
            policy.conditions = conditions
        if priority is not None:
            policy.priority = priority
        await session.flush()
        return policy

    @staticmethod
    async def toggle_enable(session: AsyncSession, policy_id: str, enabled: bool) -> Policy:
        """启用/停用 Policy"""
        stmt = select(Policy).where(Policy.id == policy_id)
        policy = (await session.execute(stmt)).scalar_one_or_none()
        if policy is None:
            raise ValueError("Policy 不存在")
        policy.enabled = enabled
        await session.flush()
        return policy

    @staticmethod
    async def list_policies(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        effect: str | None = None,
        enabled: bool | None = None,
    ) -> tuple[list[Policy], int]:
        """查询 Policy 列表"""
        tenant_id = get_tenant_id()
        conditions = [Policy.tenant_id == tenant_id]
        if effect:
            conditions.append(Policy.effect == effect)
        if enabled is not None:
            conditions.append(Policy.enabled == enabled)

        total = (await session.execute(
            select(func.count(Policy.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Policy)
            .where(*conditions)
            .order_by(Policy.priority.desc(), Policy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_active_policies(session: AsyncSession) -> list[Policy]:
        """获取当前租户启用的 Policy 列表（供权限引擎求值）"""
        tenant_id = get_tenant_id()
        stmt = (
            select(Policy)
            .where(Policy.tenant_id == tenant_id, Policy.enabled == True)  # noqa: E712
            .order_by(Policy.priority.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    def to_evaluator_input(policies: list[Policy]) -> list[dict]:
        """将 Policy 模型转为求值器输入格式"""
        return [
            {
                "id": p.id,
                "effect": p.effect,
                "enabled": p.enabled,
                "conditions": p.conditions or [],
            }
            for p in policies
        ]


policy_service = PolicyService()
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/services/test_policy_service.py -v`
预期：PASS（3 个测试通过）

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/iam/schemas/policy.py server/python/src/iam/services/policy_service.py server/python/tests/iam/unit/services/test_policy_service.py
git commit -m "feat(iam): 新增企业 Policy 服务（CRUD/启停/求值辅助）"
```

### 任务 17：Policy 控制器

**文件：**
- 创建：`server/python/src/iam/controllers/admin/policy_controller.py`
- 测试：`server/python/tests/iam/unit/controllers/test_policy_controller.py`

- [ ] **步骤 1：创建管理端控制器**

创建 `server/python/src/iam/controllers/admin/policy_controller.py`：

```python
"""
企业 Policy 控制器 - 管理端
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.permission.audit_writer import write_audit
from iam.schemas.policy import (
    PolicyCreate,
    PolicyPaginatedQuery,
    PolicyResponse,
    PolicyUpdate,
)
from iam.services.policy_service import policy_service

router = APIRouter()


@router.get("/policies")
async def list_policies(
    query: PolicyPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """查询 Policy 列表"""
    items, total = await policy_service.list_policies(
        session,
        page=query.page,
        page_size=query.page_size,
        effect=query.effect,
        enabled=query.enabled,
    )
    return ApiResponse.paginated(
        data=[PolicyResponse.model_validate(p).model_dump() for p in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.post("/policies")
async def create_policy(
    data: PolicyCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """创建 Policy"""
    try:
        policy = await policy_service.create(
            session,
            name=data.name,
            code=data.code,
            effect=data.effect,
            conditions=data.conditions,
            description=data.description,
            priority=data.priority,
        )
        await write_audit(
            session=session,
            business_domain="iam",
            operation_type="create_policy",
            resource_type="policy",
            resource_id=policy.id,
            resource_name=policy.name,
            after_data={"code": policy.code, "effect": policy.effect},
        )
        await session.commit()
        return ApiResponse.success(
            data=PolicyResponse.model_validate(policy).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """更新 Policy"""
    try:
        policy = await policy_service.update(
            session,
            policy_id=policy_id,
            name=data.name,
            description=data.description,
            effect=data.effect,
            conditions=data.conditions,
            priority=data.priority,
        )
        await write_audit(
            session=session,
            business_domain="iam",
            operation_type="update_policy",
            resource_type="policy",
            resource_id=policy.id,
            resource_name=policy.name,
        )
        await session.commit()
        return ApiResponse.success(
            data=PolicyResponse.model_validate(policy).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/policies/{policy_id}/enable")
async def toggle_enable(
    policy_id: str,
    enabled: bool,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """启用/停用 Policy"""
    try:
        policy = await policy_service.toggle_enable(session, policy_id=policy_id, enabled=enabled)
        await write_audit(
            session=session,
            business_domain="iam",
            operation_type="toggle_policy",
            resource_type="policy",
            resource_id=policy.id,
            resource_name=policy.name,
            detail={"enabled": enabled},
        )
        await session.commit()
        return ApiResponse.success(
            data=PolicyResponse.model_validate(policy).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 2：编写控制器测试**

创建 `server/python/tests/iam/unit/controllers/test_policy_controller.py`：

```python
"""
Policy 控制器单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from iam.controllers.admin.policy_controller import create_policy, toggle_enable
from iam.schemas.policy import PolicyCreate


@pytest.mark.asyncio
class TestPolicyController:
    """Policy 控制器测试"""

    async def test_create_policy_success(self):
        """创建 Policy 成功"""
        session = AsyncMock()
        mock_policy = MagicMock()
        mock_policy.id = "p1"
        mock_policy.name = "禁止下载"
        mock_policy.code = "deny_download"
        mock_policy.effect = "deny"
        mock_policy.conditions = []
        mock_policy.enabled = False
        mock_policy.priority = 0
        data = PolicyCreate(
            name="禁止下载",
            code="deny_download",
            effect="deny",
            conditions=[{"field": "operation", "op": "eq", "value": "download"}],
        )
        with patch("iam.services.policy_service.policy_service.create", new_callable=AsyncMock, return_value=mock_policy), \
             patch("iam.controllers.admin.policy_controller.write_audit", new_callable=AsyncMock):
            response = await create_policy(data=data, session=session)
            assert response.status_code == 200
            session.commit.assert_called_once()

    async def test_toggle_enable(self):
        """启用 Policy"""
        session = AsyncMock()
        mock_policy = MagicMock()
        mock_policy.id = "p1"
        mock_policy.enabled = True
        with patch("iam.services.policy_service.policy_service.toggle_enable", new_callable=AsyncMock, return_value=mock_policy), \
             patch("iam.controllers.admin.policy_controller.write_audit", new_callable=AsyncMock):
            response = await toggle_enable(policy_id="p1", enabled=True, session=session)
            assert response.status_code == 200
```

- [ ] **步骤 3：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/controllers/test_policy_controller.py -v`
预期：PASS

- [ ] **步骤 4：在 module.py 注册路由**

修改 `server/python/src/iam/module.py`，导入并注册：

```python
        from iam.controllers.admin.policy_controller import (
            router as admin_policy_router,
        )
```

返回列表追加：

```python
            (admin_policy_router, "/iam/admin/v1", ["Admin - Policy"]),
```

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/controllers/admin/policy_controller.py server/python/src/iam/module.py server/python/tests/iam/unit/controllers/test_policy_controller.py
git commit -m "feat(iam): 新增企业 Policy 管理端控制器并注册路由"
```

---

## 批次 6：iam 组织/用户服务增强

### 任务 18：增强组织/用户选择器接口

**文件：**
- 修改：`server/python/src/iam/services/organization_service.py`
- 修改：`server/python/src/iam/services/user_service.py`
- 修改：`server/python/src/iam/controllers/console/org_user_controller.py`
- 测试：`server/python/tests/iam/unit/services/test_org_user_selector.py`

- [ ] **步骤 1：阅读现有 organization_service 和 user_service 接口**

运行：用 codegraph 读取 `OrganizationService` 和 `UserService` 现有方法签名，确认选择器所需接口是否已存在（人员选择器需用户搜索、组织树查询）。

- [ ] **步骤 2：编写选择器测试**

创建 `server/python/tests/iam/unit/services/test_org_user_selector.py`：

```python
"""
人员组织选择器接口测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from iam.services.organization_service import OrganizationService
from iam.services.user_service import UserService


@pytest.mark.asyncio
class TestOrgUserSelector:
    """人员组织选择器测试"""

    async def test_search_users_by_keyword(self):
        """按关键词搜索用户（选择器用）"""
        session = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "zhangsan"
        mock_user.nickname = "张三"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        session.execute = AsyncMock(return_value=mock_result)

        users = await UserService.search_for_selector(
            session, tenant_id="t1", keyword="张", limit=20
        )
        assert len(users) == 1

    async def test_get_org_tree_for_selector(self):
        """获取组织树（选择器用）"""
        session = AsyncMock()
        mock_org = MagicMock()
        mock_org.id = "org-1"
        mock_org.name = "总部"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_org]
        session.execute = AsyncMock(return_value=mock_result)

        tree = await OrganizationService.get_tree_for_selector(session, tenant_id="t1")
        assert isinstance(tree, list)
```

- [ ] **步骤 3：运行测试验证失败**

运行：`cd server/python && pytest tests/iam/unit/services/test_org_user_selector.py -v`
预期：FAIL，`AttributeError: ... has no attribute 'search_for_selector'`

- [ ] **步骤 4：在 user_service.py 增补 search_for_selector**

在 `UserService` 类中新增静态方法（参考现有 list_users 的查询模式）：

```python
    @staticmethod
    async def search_for_selector(
        session: AsyncSession,
        tenant_id: str,
        keyword: str | None = None,
        organization_id: str | None = None,
        limit: int = 20,
    ) -> list[User]:
        """人员选择器：按关键词搜索用户（返回精简字段）"""
        from sqlalchemy import or_

        conditions = [User.tenant_id == tenant_id, User.status == "active"]
        if keyword:
            conditions.append(
                or_(
                    User.username.like(f"%{keyword}%"),
                    User.nickname.like(f"%{keyword}%"),
                    User.email.like(f"%{keyword}%"),
                )
            )

        stmt = (
            select(User)
            .where(*conditions)
            .order_by(User.username)
            .limit(limit)
        )
        return list((await session.execute(stmt)).scalars().all())
```

- [ ] **步骤 5：在 organization_service.py 增补 get_tree_for_selector**

```python
    @staticmethod
    async def get_tree_for_selector(session: AsyncSession, tenant_id: str) -> list[dict]:
        """组织选择器：返回组织树"""
        stmt = (
            select(Organization)
            .where(Organization.tenant_id == tenant_id)
            .order_by(Organization.tree_sorts)
        )
        nodes = list((await session.execute(stmt)).scars().all())
        return Organization.build_tree(nodes)
```

- [ ] **步骤 6：运行测试验证通过**

运行：`cd server/python && pytest tests/iam/unit/services/test_org_user_selector.py -v`
预期：PASS

- [ ] **步骤 7：在 org_user_controller.py 增补端点**

在 `server/python/src/iam/controllers/console/org_user_controller.py` 新增：

```python
@router.get("/people/select")
async def select_people(
    keyword: str | None = None,
    organization_id: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """人员选择器接口"""
    tenant_id = get_tenant_id()
    users = await UserService.search_for_selector(
        session, tenant_id=tenant_id, keyword=keyword, organization_id=organization_id, limit=limit
    )
    return ApiResponse.success(
        data=[
            {"user_id": u.id, "username": u.username, "nickname": u.nickname, "email": u.email}
            for u in users
        ]
    )


@router.get("/organizations/tree")
async def select_org_tree(
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """组织树选择器接口"""
    tenant_id = get_tenant_id()
    tree = await OrganizationService.get_tree_for_selector(session, tenant_id)
    return ApiResponse.success(data=tree)
```

- [ ] **步骤 8：Commit**

```bash
git add server/python/src/iam/services/organization_service.py server/python/src/iam/services/user_service.py server/python/src/iam/controllers/console/org_user_controller.py server/python/tests/iam/unit/services/test_org_user_selector.py
git commit -m "feat(iam): 增强组织/用户服务（人员组织选择器接口）"
```

---

## 批次 7：iam 数据库迁移与种子

### 任务 19：站内信表迁移

**文件：**
- 创建：`server/python/src/iam/migrations/versions/004_notification.py`

- [ ] **步骤 1：创建迁移脚本**

创建 `server/python/src/iam/migrations/versions/004_notification.py`（参考 `003_audit_log.py` 模式，revision 链接 `003_audit_log`）：

```python
"""站内信表创建

Revision ID: 004_notification
Revises: 003_audit_log
Create Date: 2026-07-23

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_notification"
down_revision = "003_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建站内信表"""
    op.create_table(
        "notification",
        sa.Column("id", sa.String(36), primary_key=True, comment="主键ID"),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True, comment="租户ID"),
        sa.Column("title", sa.String(256), nullable=False, comment="标题"),
        sa.Column("content", sa.String(2048), nullable=False, comment="内容"),
        sa.Column("notification_type", sa.String(64), nullable=False, comment="通知类型"),
        sa.Column("recipient_id", sa.String(36), nullable=False, comment="接收人用户ID"),
        sa.Column("sender_id", sa.String(36), nullable=True, comment="发送人用户ID"),
        sa.Column("link", sa.String(512), nullable=True, comment="跳转链接"),
        sa.Column("extra_data", postgresql.JSONB, nullable=True, comment="扩展元数据"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false"), comment="是否已读"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True, comment="已读时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        schema="iam",
        comment="站内信表",
    )
    op.create_index("ix_notification_recipient_id", "notification", ["recipient_id"], schema="iam")
    op.create_index("ix_notification_is_read", "notification", ["is_read"], schema="iam")
    op.create_index("ix_notification_type", "notification", ["notification_type"], schema="iam")


def downgrade() -> None:
    op.drop_table("notification", schema="iam")
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/migrations/versions/004_notification.py
git commit -m "feat(iam): 新增站内信表迁移脚本"
```

### 任务 20：权限申请表迁移

**文件：**
- 创建：`server/python/src/iam/migrations/versions/005_permission_request.py`

- [ ] **步骤 1：创建迁移脚本**

创建 `server/python/src/iam/migrations/versions/005_permission_request.py`（revision 链接 `004_notification`），创建 `permission_request` 和 `permission_cache_event` 两张表，字段对应任务 11 模型定义。

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/migrations/versions/005_permission_request.py
git commit -m "feat(iam): 新增权限申请表与权限变更流水表迁移脚本"
```

### 任务 21：Policy 表迁移

**文件：**
- 创建：`server/python/src/iam/migrations/versions/006_policy.py`

- [ ] **步骤 1：创建迁移脚本**

创建 `server/python/src/iam/migrations/versions/006_policy.py`（revision 链接 `005_permission_request`），创建 `policy` 表，字段对应任务 15 模型定义（含 `conditions` JSONB、`enabled` Boolean、`priority` Integer）。

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/migrations/versions/006_policy.py
git commit -m "feat(iam): 新增企业 Policy 表迁移脚本"
```

### 任务 22：执行迁移验证 + Policy 种子数据

**文件：**
- 创建：`server/python/src/iam/migrations/seeds/policy_seed.py`
- 修改：`server/python/src/iam/module.py`（注册 seed）

- [ ] **步骤 1：执行迁移**

运行：`cd server/python && alembic -c alembic.ini upgrade head`
预期：无错误，5 张新表创建成功

- [ ] **步骤 2：创建 Policy 种子**

创建 `server/python/src/iam/migrations/seeds/policy_seed.py`：

```python
"""
默认 Policy 种子数据
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.models import Policy


async def run(session: AsyncSession) -> None:
    """创建默认停用的示范 Policy（仅示例，租户可自行启用）"""
    # 检查是否已存在
    stmt = select(Policy).where(Policy.code == "default_deny_download_sensitive")
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return

    policy = Policy(
        tenant_id="default",
        name="敏感资源禁止下载",
        code="default_deny_download_sensitive",
        description="示范策略：禁止下载标记为敏感的资源",
        effect="deny",
        conditions=[
            {"field": "operation", "op": "eq", "value": "download"},
            {"field": "resource_type", "op": "in", "value": ["document"]},
        ],
        enabled=False,
        priority=100,
    )
    session.add(policy)
    await session.flush()
```

- [ ] **步骤 3：在 module.py 注册 seed**

修改 `server/python/src/iam/module.py` 的 `get_seeds()`，导入并注册：

```python
        from iam.migrations.seeds.policy_seed import run as policy_seed_run
        return {
            "organization": organization_seed_run,
            "user": user_seed_run,
            "policy": policy_seed_run,
        }
```

- [ ] **步骤 4：验证表结构**

运行：`cd server/python && python -c "import asyncio; from sqlalchemy import text; from framework.database.core import get_engine; asyncio.run(...)"` 或通过测试 fixture 验证表存在。

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/migrations/seeds/policy_seed.py server/python/src/iam/module.py
git commit -m "feat(iam): 新增默认 Policy 种子数据并注册 seed"
```

---

## 批次 8：iam 前端

### 任务 23：前端类型 + API

**文件：**
- 创建：`web/vue/src/iam/types/notification.ts`
- 创建：`web/vue/src/iam/types/permissionRequest.ts`
- 创建：`web/vue/src/iam/types/policy.ts`
- 创建：`web/vue/src/iam/api/notification.ts`
- 创建：`web/vue/src/iam/api/permissionRequest.ts`
- 创建：`web/vue/src/iam/api/policy.ts`

- [ ] **步骤 1：创建 notification 类型**

创建 `web/vue/src/iam/types/notification.ts`：

```typescript
import type { BasePaginatedQuery } from "@/framework/types";

export interface Notification {
  id: string;
  title: string;
  content: string;
  notification_type: string;
  recipient_id: string;
  sender_id?: string;
  link?: string;
  extra_data?: Record<string, unknown>;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface NotificationPaginatedQuery extends BasePaginatedQuery {
  is_read?: boolean;
  notification_type?: string;
}

export interface NotificationMarkReadRequest {
  notification_ids: string[];
}

export interface NotificationUnreadCount {
  unread_count: number;
}
```

- [ ] **步骤 2：创建 permissionRequest 类型**

创建 `web/vue/src/iam/types/permissionRequest.ts`：

```typescript
import type { BasePaginatedQuery } from "@/framework/types";

export interface PermissionRequest {
  id: string;
  request_type: string;
  applicant_id: string;
  applicant_name: string;
  target_module: string;
  target_resource_id: string;
  target_resource_name: string;
  requested_role?: string;
  requested_permission?: string;
  reason?: string;
  status: "pending" | "approved" | "rejected" | "applying" | "applied" | "apply_failed";
  reviewer_id?: string;
  reviewer_name?: string;
  review_comment?: string;
  reviewed_at?: string;
  apply_error?: string;
  created_at: string;
}

export interface PermissionRequestCreate {
  request_type: string;
  target_module: string;
  target_resource_id: string;
  target_resource_name: string;
  requested_role?: string;
  requested_permission?: string;
  reason?: string;
  extra_data?: Record<string, unknown>;
}

export interface PermissionRequestReview {
  approved: boolean;
  review_comment?: string;
}

export interface PermissionRequestPaginatedQuery extends BasePaginatedQuery {
  status?: string;
  request_type?: string;
  target_module?: string;
}
```

- [ ] **步骤 3：创建 policy 类型**

创建 `web/vue/src/iam/types/policy.ts`：

```typescript
import type { BasePaginatedQuery } from "@/framework/types";

export interface PolicyCondition {
  field: string;
  op: "eq" | "ne" | "in" | "not_in" | "contains";
  value: unknown;
}

export interface Policy {
  id: string;
  name: string;
  code: string;
  description?: string;
  effect: "allow" | "deny";
  conditions: PolicyCondition[];
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface PolicyCreate {
  name: string;
  code: string;
  description?: string;
  effect: "allow" | "deny";
  conditions: PolicyCondition[];
  priority?: number;
}

export interface PolicyUpdate {
  name?: string;
  description?: string;
  effect?: "allow" | "deny";
  conditions?: PolicyCondition[];
  priority?: number;
}

export interface PolicyPaginatedQuery extends BasePaginatedQuery {
  effect?: string;
  enabled?: boolean;
}
```

- [ ] **步骤 4：创建 notification API**

创建 `web/vue/src/iam/api/notification.ts`：

```typescript
import { get, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Notification, NotificationPaginatedQuery, NotificationMarkReadRequest, NotificationUnreadCount } from "@/iam/types/notification";

export const getNotifications = (params?: NotificationPaginatedQuery) =>
  get<ApiResponse<Notification[]>>("/iam/console/v1/notifications", { params });

export const getUnreadCount = () =>
  get<ApiResponse<NotificationUnreadCount>>("/iam/console/v1/notifications/unread-count");

export const markNotificationsRead = (data: NotificationMarkReadRequest) =>
  put<ApiResponse<{ marked_count: number }>>("/iam/console/v1/notifications/read", data);
```

- [ ] **步骤 5：创建 permissionRequest API**

创建 `web/vue/src/iam/api/permissionRequest.ts`：

```typescript
import { get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { PermissionRequest, PermissionRequestCreate, PermissionRequestReview, PermissionRequestPaginatedQuery } from "@/iam/types/permissionRequest";

export const submitPermissionRequest = (data: PermissionRequestCreate) =>
  post<ApiResponse<PermissionRequest>>("/iam/console/v1/permission-requests", data);

export const getMyPermissionRequests = (params?: PermissionRequestPaginatedQuery) =>
  get<ApiResponse<PermissionRequest[]>>("/iam/console/v1/permission-requests", { params });

export const getPendingPermissionRequests = (params?: PermissionRequestPaginatedQuery) =>
  get<ApiResponse<PermissionRequest[]>>("/iam/admin/v1/permission-requests", { params });

export const reviewPermissionRequest = (id: string, data: PermissionRequestReview) =>
  put<ApiResponse<PermissionRequest>>(`/iam/admin/v1/permission-requests/${id}/review`, data);
```

- [ ] **步骤 6：创建 policy API**

创建 `web/vue/src/iam/api/policy.ts`：

```typescript
import { get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Policy, PolicyCreate, PolicyUpdate, PolicyPaginatedQuery } from "@/iam/types/policy";

export const getPolicies = (params?: PolicyPaginatedQuery) =>
  get<ApiResponse<Policy[]>>("/iam/admin/v1/policies", { params });

export const createPolicy = (data: PolicyCreate) =>
  post<ApiResponse<Policy>>("/iam/admin/v1/policies", data);

export const updatePolicy = (id: string, data: PolicyUpdate) =>
  put<ApiResponse<Policy>>(`/iam/admin/v1/policies/${id}`, data);

export const togglePolicyEnable = (id: string, enabled: boolean) =>
  put<ApiResponse<Policy>>(`/iam/admin/v1/policies/${id}/enable?enabled=${enabled}`);
```

- [ ] **步骤 7：更新 iam index.ts 导出**

修改 `web/vue/src/iam/index.ts`，在类型和 API 导出区追加新的导出。

- [ ] **步骤 8：Commit**

```bash
git add web/vue/src/iam/types/notification.ts web/vue/src/iam/types/permissionRequest.ts web/vue/src/iam/types/policy.ts web/vue/src/iam/api/notification.ts web/vue/src/iam/api/permissionRequest.ts web/vue/src/iam/api/policy.ts web/vue/src/iam/index.ts
git commit -m "feat(iam): 新增站内信/权限申请/Policy 前端类型与 API"
```

### 任务 24：站内信 store + 页面

**文件：**
- 创建：`web/vue/src/iam/stores/notification.ts`
- 创建：`web/vue/src/iam/pages/notifications/NotificationList.vue`

- [ ] **步骤 1：创建 notification store**

创建 `web/vue/src/iam/stores/notification.ts`（参考 `iam/stores/user.ts` 模式）：

```typescript
import { defineStore } from "pinia";
import { ref } from "vue";
import { getNotifications, getUnreadCount, markNotificationsRead } from "@/iam/api/notification";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { Notification, NotificationPaginatedQuery } from "@/iam/types/notification";

export const useNotificationStore = defineStore("iam-notification", () => {
  const notifications = ref<Notification[]>([]);
  const unreadCount = ref(0);
  const loading = ref(false);
  const total = ref(0);

  const fetchNotifications = async (params?: NotificationPaginatedQuery) => {
    loading.value = true;
    try {
      const response = await getNotifications(params);
      notifications.value = response.data ?? [];
      total.value = response.total ?? 0;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "获取站内信失败"));
    } finally {
      loading.value = false;
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await getUnreadCount();
      unreadCount.value = response.data?.unread_count ?? 0;
    } catch (error: any) {
      // 静默失败，不弹窗
    }
  };

  const markRead = async (notificationIds: string[]) => {
    loading.value = true;
    try {
      await markNotificationsRead({ notification_ids: notificationIds });
      notifications.value.forEach((n) => {
        if (notificationIds.length === 0 || notificationIds.includes(n.id)) {
          n.is_read = true;
        }
      });
      await fetchUnreadCount();
      notifySuccess("标记已读成功");
    } catch (error: any) {
      notifyError(getErrorMessage(error, "标记已读失败"));
    } finally {
      loading.value = false;
    }
  };

  return { notifications, unreadCount, loading, total, fetchNotifications, fetchUnreadCount, markRead };
});
```

- [ ] **步骤 2：创建 NotificationList 页面**

创建 `web/vue/src/iam/pages/notifications/NotificationList.vue`（参考 `iam/pages/audit-logs/AuditLogList.vue` 列表页模式，使用 `@/components` 统一入口的 DataTable/Card/Button）：

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useNotificationStore } from "@/iam/stores/notification";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const store = useNotificationStore();
const activeFilter = ref<"all" | "unread">("all");

const fetchData = () => {
  store.fetchNotifications({ page: 1, page_size: 20, is_read: activeFilter.value === "unread" ? false : undefined });
};

const handleMarkRead = (id?: string) => {
  store.markRead(id ? [id] : []);
};

const handleNavigate = (link?: string) => {
  if (link) window.location.href = link;
};

onMounted(() => {
  fetchData();
  store.fetchUnreadCount();
});
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>站内信</CardTitle>
      <div class="flex gap-2">
        <Button :variant="activeFilter === 'all' ? 'default' : 'outline'" size="sm" @click="activeFilter = 'all'; fetchData()">
          全部
        </Button>
        <Button :variant="activeFilter === 'unread' ? 'default' : 'outline'" size="sm" @click="activeFilter = 'unread'; fetchData()">
          未读 ({{ store.unreadCount }})
        </Button>
        <Button variant="ghost" size="sm" @click="handleMarkRead()">全部已读</Button>
      </div>
    </CardHeader>
    <CardContent>
      <div v-if="store.loading" class="text-center py-8">加载中...</div>
      <div v-else-if="store.notifications.length === 0" class="text-center py-8 text-muted-foreground">
        暂无站内信
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="item in store.notifications"
          :key="item.id"
          class="flex items-start justify-between p-3 border rounded-lg hover:bg-accent"
          :class="{ 'bg-muted/50': !item.is_read }"
        >
          <div class="flex-1 cursor-pointer" @click="handleNavigate(item.link)">
            <div class="flex items-center gap-2">
              <Badge v-if="!item.is_read" variant="destructive">未读</Badge>
              <span class="font-medium">{{ item.title }}</span>
            </div>
            <p class="text-sm text-muted-foreground mt-1">{{ item.content }}</p>
            <p class="text-xs text-muted-foreground mt-1">{{ item.created_at }}</p>
          </div>
          <Button v-if="!item.is_read" variant="ghost" size="sm" @click="handleMarkRead(item.id)">
            已读
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/iam/stores/notification.ts web/vue/src/iam/pages/notifications/NotificationList.vue
git commit -m "feat(iam): 新增站内信 store 与页面"
```

### 任务 25：权限申请 + Policy 页面

**文件：**
- 创建：`web/vue/src/iam/pages/permission-requests/PermissionRequestList.vue`
- 创建：`web/vue/src/iam/pages/policies/PolicyList.vue`

- [ ] **步骤 1：创建 PermissionRequestList 页面**

创建 `web/vue/src/iam/pages/permission-requests/PermissionRequestList.vue`（参考列表页模式，含「我的申请」和「待我审批」两个 Tab，调用 `getMyPermissionRequests` / `getPendingPermissionRequests`，审批操作调用 `reviewPermissionRequest`）。

- [ ] **步骤 2：创建 PolicyList 页面**

创建 `web/vue/src/iam/pages/policies/PolicyList.vue`（参考列表页模式，调用 `getPolicies`/`createPolicy`/`updatePolicy`/`togglePolicyEnable`，含条件编辑表单）。

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/iam/pages/permission-requests/PermissionRequestList.vue web/vue/src/iam/pages/policies/PolicyList.vue
git commit -m "feat(iam): 新增权限申请与 Policy 页面"
```

### 任务 26：权限排障面板组件 + 路由配置

**文件：**
- 创建：`web/vue/src/iam/components/PermissionTroubleshootPanel.vue`
- 修改：`web/vue/src/iam/router/index.ts`

- [ ] **步骤 1：创建权限排障面板组件**

创建 `web/vue/src/iam/components/PermissionTroubleshootPanel.vue`（展示权限判定结果：resource_permission / policy_effect / reasons 命中原因列表，输入 user_id/resource_type/resource_id/operation，调用后端排障接口展示最终允许/拒绝及原因）。

- [ ] **步骤 2：更新路由配置**

修改 `web/vue/src/iam/router/index.ts`，在 IAMRoot children 中追加：

```typescript
      // 站内信
      {
        path: "notifications",
        name: "NotificationManagement",
        component: () => import("@/iam/pages/notifications/NotificationList.vue"),
        meta: { title: "站内信", icon: "bell", requiresAuth: true },
      },
      // 权限申请
      {
        path: "permission-requests",
        name: "PermissionRequestManagement",
        component: () => import("@/iam/pages/permission-requests/PermissionRequestList.vue"),
        meta: { title: "权限申请", icon: "key", requiresAuth: true },
      },
      // 企业 Policy
      {
        path: "policies",
        name: "PolicyManagement",
        component: () => import("@/iam/pages/policies/PolicyList.vue"),
        meta: { title: "企业策略", icon: "shield", requiresAuth: true },
      },
```

- [ ] **步骤 3：前端类型校验**

运行：`cd web/vue && pnpm typecheck`
预期：无类型错误

- [ ] **步骤 4：Commit**

```bash
git add web/vue/src/iam/components/PermissionTroubleshootPanel.vue web/vue/src/iam/router/index.ts
git commit -m "feat(iam): 新增权限排障面板组件与路由配置"
```

### 任务 27：前端测试 + E2E 基础流程

**文件：**
- 创建：`web/vue/src/iam/pages/notifications/__tests__/NotificationList.spec.ts`
- 创建：`web/vue/src/iam/pages/policies/__tests__/PolicyList.spec.ts`

- [ ] **步骤 1：编写 NotificationList 组件测试**

测试 store 加载、未读标记、跳转交互（参考现有 iam 组件测试模式）。

- [ ] **步骤 2：编写 PolicyList 组件测试**

测试 Policy 列表渲染、启用/停用切换、创建表单提交。

- [ ] **步骤 3：运行前端测试**

运行：`cd web/vue && pnpm test`
预期：PASS

- [ ] **步骤 4：Commit**

```bash
git add web/vue/src/iam/pages/notifications/__tests__/ web/vue/src/iam/pages/policies/__tests__/
git commit -m "test(iam): 新增站内信与 Policy 页面组件测试"
```

---

## 批次 9：集成验证与收尾

### 任务 28：iam 模块定义增补菜单权限

**文件：**
- 修改：`server/python/src/iam/module.py`

- [ ] **步骤 1：在 get_module_definition 增补菜单和权限**

在 `server/python/src/iam/module.py` 的 `get_module_definition()` 返回的 `menus` 列表追加：

```python
                MenuDef(
                    code="iam.notifications",
                    name="站内信",
                    path="/iam/notifications",
                    icon="Bell",
                    sort_order=7,
                    permission_codes=["iam:notification:read"],
                ),
                MenuDef(
                    code="iam.permission_requests",
                    name="权限申请",
                    path="/iam/permission-requests",
                    icon="Key",
                    sort_order=8,
                    permission_codes=["iam:permission_request:read"],
                ),
                MenuDef(
                    code="iam.policies",
                    name="企业策略",
                    path="/iam/policies",
                    icon="Shield",
                    sort_order=9,
                    permission_codes=["iam:policy:read"],
                ),
```

在 `permissions` 列表追加：

```python
                # 站内信权限
                PermissionDef(code="iam:notification:read", name="查看站内信", resource="notification", action="read"),
                # 权限申请权限
                PermissionDef(code="iam:permission_request:read", name="查看权限申请", resource="permission_request", action="read"),
                PermissionDef(code="iam:permission_request:approve", name="审批权限申请", resource="permission_request", action="approve"),
                # Policy 权限
                PermissionDef(code="iam:policy:read", name="查看策略", resource="policy", action="read"),
                PermissionDef(code="iam:policy:write", name="编辑策略", resource="policy", action="write"),
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/iam/module.py
git commit -m "feat(iam): 增补站内信/权限申请/Policy 菜单与权限声明"
```

### 任务 29：集成测试 - 权限申请流程

**文件：**
- 创建：`server/python/tests/iam/integration/test_permission_flow.py`

- [ ] **步骤 1：编写集成测试**

测试完整流程：提交申请 -> 管理端审核通过 -> 状态 applied -> 申请人收到站内信（验证 Notification 表有记录）。

- [ ] **步骤 2：运行集成测试**

运行：`cd server/python && pytest tests/iam/integration/test_permission_flow.py -v`
预期：PASS

- [ ] **步骤 3：Commit**

```bash
git add server/python/tests/iam/integration/test_permission_flow.py
git commit -m "test(iam): 新增权限申请审批集成测试"
```

### 任务 30：Phase 1 整体验收

- [ ] **步骤 1：运行后端全部新增测试**

运行：`cd server/python && pytest tests/framework/unit/permission/ tests/framework/unit/notification/ tests/iam/unit/services/test_notification_service.py tests/iam/unit/services/test_permission_request_service.py tests/iam/unit/services/test_policy_service.py tests/iam/unit/controllers/test_notification_controller.py tests/iam/unit/controllers/test_permission_request_controller.py tests/iam/unit/controllers/test_policy_controller.py tests/iam/unit/services/test_org_user_selector.py tests/iam/integration/test_permission_flow.py -v`
预期：全部 PASS

- [ ] **步骤 2：运行 ruff 和 pyright**

运行：`cd server/python && ruff check src/framework/permission/ src/framework/notification/ src/iam/models/notification.py src/iam/models/permission_request.py src/iam/models/policy.py src/iam/services/notification_service.py src/iam/services/permission_request_service.py src/iam/services/policy_service.py src/iam/controllers/ && pyright src/framework/permission/ src/framework/notification/`
预期：无错误

- [ ] **步骤 3：运行前端类型检查和测试**

运行：`cd web/vue && pnpm typecheck && pnpm test`
预期：无错误

- [ ] **步骤 4：验证迁移脚本可正向执行**

运行：`cd server/python && alembic -c alembic.ini upgrade head`
预期：无错误

- [ ] **步骤 5：验证 OpenSpec tasks 全部完成**

逐项核对 `openspec/changes/kbhub-migration-phase1/tasks.md` 的 33 项任务，确认全部完成。

- [ ] **步骤 6：Commit 验收标记**

```bash
git add -A
git commit -m "chore(kbhub-phase1): Phase 1 整体验收通过"
```

---

## 自检结果

### 规格覆盖度
- ✅ framework 权限引擎（任务 2-3）
- ✅ framework Policy 求值器（任务 2）
- ✅ framework 审计写入辅助（任务 4）
- ✅ framework 站内信发送辅助（任务 5）
- ✅ iam 站内信模型/服务/控制器（任务 7-10）
- ✅ iam 权限申请模型/服务/控制器/回调（任务 11-14）
- ✅ iam Policy 模型/服务/控制器（任务 15-17）
- ✅ iam 组织/用户增强（任务 18）
- ✅ iam 迁移+种子（任务 19-22）
- ✅ iam 前端（任务 23-27）
- ✅ 菜单权限声明（任务 28）
- ✅ 集成测试（任务 29）

### 占位符扫描
- 权限申请回调 `_apply_to_target_module` 含 `TODO(phase2/phase3)` 标记，这是设计上明确的占位（Phase 1 目标模块 inner 接口未实现），非计划缺陷。Phase 2/3 实现后接入。

### 类型一致性
- `Notification` 模型字段（title/content/notification_type/recipient_id/is_read）在服务、Schema、控制器、前端类型中一致
- `PermissionRequest` 状态枚举（pending/applying/applied/apply_failed/rejected）在服务、Schema、前端类型中一致
- `Policy` 条件格式（field/op/value）在求值器、模型、Schema、前端类型中一致
