# OpenSpec 与 Superpowers 协同工作指南

本文档说明如何将 OpenSpec（规范驱动开发）与 Superpowers（工作流纪律）两个框架配合使用，实现"做对的事情，用对的方式"。

## 核心理念

| 框架 | 解决的问题 | 类比 |
|------|-----------|------|
| OpenSpec | 做什么、为什么做 | 建筑蓝图 |
| Superpowers | 怎么做、按什么标准做 | 施工规范 |

**缺少任何一个的后果**：

- 只有 OpenSpec：规范对了但代码质量烂
- 只有 Superpowers：代码质量好了但方向错了
- 两个都没有：方向错 + 代码烂

## 分工说明

### OpenSpec 负责"做什么"

**核心产物**：

| 产物 | 说明 |
|------|------|
| `proposal.md` | 为什么要做、范围是什么、排除什么 |
| `specs/` | 增量规范，描述场景（假设/当/则） |
| `design.md` | 技术方案、架构决策 |
| `tasks.md` | 实现步骤清单 |

**使用的 Skills**：

- `/opsx:explore` — 探索想法、讨论方案
- `/opsx:new` — 创建新变更
- `/opsx:continue` — 继续创建产物
- `/opsx:verify` — 验证实现与规范一致
- `/opsx:archive` — 归档并更新主规范

### Superpowers 负责"怎么做"

**核心纪律**：

| Skill | 作用 |
|-------|------|
| `brainstorming` | 在实现前探索需求和设计 |
| `test-driven-development` | 红灯-绿灯-重构循环 |
| `requesting-code-review` | 代码质量审查 |
| `verification-before-completion` | 完成前运行测试验证 |

## 完整工作流

```text
┌─────────────────────────────────────────────────────────────────┐
│                      完整协同工作流                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段一：需求对齐（OpenSpec 主导）                                  │
│  ─────────────────────────────                                  │
│                                                                 │
│  1. /opsx:explore        ← 探索技术方案                           │
│  2. /opsx:new <name>     ← 创建变更                              │
│  3. 人工审核产物          ← 检查 proposal/specs/design/tasks       │
│                                                                 │
│  阶段二：衔接转换                                                  │
│  ─────────────────────────────                                  │
│                                                                 │
│  4. openspec-superpowers-bridge  ← 加载规范上下文                 │
│     - 读取 OpenSpec 产物                                         │
│     - 跳过 brainstorming（explore 已完成）                        │
│     - 场景转换为测试用例                                          │
│     - Tasks 拆分为 TDD 步骤 Superpowers planning                 │
│                                                                 │
│  阶段三：实现执行（Superpowers 主导）                               │
│  ─────────────────────────────                                  │
│                                                                 │
│  5. test-driven-development  ← TDD 循环实现                     │
│     - 写失败测试                                                │
│     - 最小实现                                                  │
│     - 重构                                                      │
│                                                                 │
│  阶段四：双重审查                                                │
│  ─────────────────────────────                                  │
│                                                                 │
│  6. requesting-code-review   ← 代码质量审查                     │
│  7. spec-compliance-check    ← 规范合规审查                     │
│                                                                 │
│  阶段五：双重验证                                                │
│  ─────────────────────────────                                  │
│                                                                 │
│  8. /opsx:verify                    ← OpenSpec 规范验证         │
│  9. verification-before-completion  ← 运行测试                  │
│                                                                 │
│  阶段六：归档收尾                                                │
│  ─────────────────────────────                                  │
│                                                                 │
│  10. /opsx:archive  ← 归档并更新主规范                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 关键衔接点

### 1. 跳过重复阶段

OpenSpec 的 `explore` 已经讨论过需求和技术方案，Superpowers 的 `brainstorming` 会重复劳动。

**规则**：如果 explore 和 propose 已完成，跳过 brainstorming，直接进入 planning。

### 2. 粒度转换

| OpenSpec Task | Superpowers Plan |
|---------------|------------------|
| "实现 JWT 签发函数" | 1. 写失败测试 → 2. 运行测试 → 3. 写最小实现 → 4. 运行测试 → 5. 重构 → 6. 提交 |

**转换规则**：

- 每个 task 拆成 TDD 循环
- 场景直接转换为测试用例
- 保持每个 commit 粒度小

### 3. 场景到测试的转换

OpenSpec 场景格式：

```markdown
### 场景：有效凭证登录
- 假设 用户持有有效的用户名和密码
- 当 用户提交登录请求
- 则 返回 access token 和 refresh token
```

转换为测试：

```python
def test_有效凭证登录_返回token():
    # 假设 -> setup
    user = create_test_user(username="test", password="valid")
    
    # 当 -> action
    result = login(username="test", password="valid")
    
    # 则 -> assertion
    assert result.access_token is not None
    assert result.refresh_token is not None
```

### 4. 双重审查

| 维度 | 使用 Skill | 检查内容 |
|------|-----------|----------|
| 代码质量 | `requesting-code-review` | 命名、结构、错误处理 |
| 规范合规 | `spec-compliance-check` | 需求覆盖、场景实现、决策遵循 |

**顺序**：先代码质量审查，后规范合规审查。

### 5. 双重验证

| 维度 | 使用方法 | 检查内容 |
|------|----------|----------|
| 规范合规 | `/opsx:verify` | 规范一致性、任务完成度 |
| 功能正确 | `verification-before-completion` | 测试通过、功能可用 |

**顺序**：先 verify 后运行测试。

## 常见问题与解决方案

### 问题 1：explore 和 brainstorming 重复

**现象**：OpenSpec 的 explore 已经讨论过方案，Superpowers 的 brainstorming 又问一遍。

**解决**：如果 explore/propose 已完成，跳过 brainstorming。

### 问题 2：tasks 粒度不匹配

**现象**：OpenSpec 的 tasks 是需求视角，Superpowers 的 plan 是实现视角。

**解决**：使用 `openspec-superpowers-bridge` 自动转换粒度。

### 问题 3：实现与 design.md 不一致

**现象**：代码质量没问题，但实现方式和技术方案不一致。

**解决**：

1. 实现前必须加载 design.md
2. 使用 `spec-compliance-check` 检查

### 问题 4：审查不检查规范合规

**现象**：代码审查通过，但实现不符合规范。

**解决**：代码审查后必须运行 `spec-compliance-check`。

### 问题 5：verify 通过但测试没跑

**现象**：verify 只检查规范合规，不运行测试。

**解决**：archive 前必须运行 `verification-before-completion`。

### 问题 6：排除范围被违反

**现象**：AI "好心" 多做了你没要求的功能。

**解决**：

1. 在 `proposal.md` 明确写出排除范围
2. `spec-compliance-check` 会检查排除范围

### 问题 7：多变更并行

**现象**：多个变更同时进行，规范混淆。

**解决**：每个变更使用独立的 git worktree。

## 快速上手

### 3 分钟开始第一个联合任务

```bash
# 1. 探索方案
/opsx:explore

# 2. 创建变更
/opsx:new <功能名>

# 3. 人工审核产物
# 检查 openspec/changes/<功能名>/ 下的文档

# 4. 衔接并开始实现
"读取 openspec/changes/ 目录下的规范，用 Superpowers 的 writing-plans 拆计划"

# 5. TDD 实现
# 每个 task 走红灯-绿灯-重构循环

# 6. 双重审查
/requesting-code-review
/spec-compliance-check

# 7. 双重验证
/opsx:verify
# 然后运行测试命令

# 8. 归档
/opsx:archive
```

### 3 条起步规则

1. **先 explore 再 propose** — 别让 AI 猜需求
2. **把 design.md 喂给 Superpowers** — 别让 AI 猜方案
3. **双审查** — 别让 AI 自己给自己打分

## 自定义 Skills

本项目已安装以下衔接 Skills：

### spec-compliance-check

**用途**：检查实现是否符合 OpenSpec 规范

**触发时机**：代码实现完成后，代码审查之前

**检查内容**：

- 规范覆盖
- 场景覆盖
- 设计决策遵循
- 排除范围检查

### openspec-superpowers-bridge

**用途**：自动衔接 OpenSpec 和 Superpowers

**触发时机**：开始实现 OpenSpec tasks 时

**功能**：

- 自动加载规范上下文
- 跳过重复的 brainstorming
- 场景转测试用例
- Tasks 拆 TDD 步骤

## 适用场景

### 只用 OpenSpec 就够

- 改按钮颜色、修 typo 等小改动
- 需求很明确，AI 不会做多余的事
- 你只需要对齐"做什么"

### 只用 Superpowers 就够

- 一次性脚本（写完就扔）
- 需求明确但不需要长期规范的小功能
- 你自己很清楚需求

### 两个都用

- 团队协作的项目
- 长期维护的项目
- 复杂功能开发
- 已有代码库的项目

**判断标准**：代码要活多久 + 有多少人碰代码

- 活 1 天 1 个人碰 → 两个都不用
- 活 1 个月 3 个人碰 → 两个都用

## 参考资料

- OpenSpec 官方：<https://github.com/fission-AI/open-spec>
- Superpowers 官方：<https://github.com/jessevogt/superpowers>
- 本项目 Skills 目录：`.claude/skills/`
