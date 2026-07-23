# 权限判定引擎接口规范

## 新增需求

### Requirement: 权限判定引擎

权限判定引擎 SHALL 编排第2层资源权限判定与第3层企业 Policy 求值，遵循 deny 优先与多租户隔离。

#### 场景：编排第2层资源权限判定和第3层Policy求值

- **Given** 用户对资源 R 持有角色 Role-A，且租户 T 下存在一条启用的 Policy P（条件匹配资源 R）
- **When** 调用权限判定引擎 `evaluate(user, action, resource)`
- **Then** 引擎先执行第2层资源权限判定（基于角色-权限矩阵），判定结果为 allow；再执行第3层 Policy 求值，Policy P 命中且效果为 deny；最终返回 deny，并记录 Policy 命中审计日志

#### 场景：Policy deny 优先于 allow

- **Given** 用户对资源 R 同时命中两条 Policy：P-allow（效果为 allow）和 P-deny（效果为 deny）
- **When** 调用权限判定引擎 `evaluate(user, action, resource)`
- **Then** 引擎返回 deny，deny 优先级高于所有 allow，审计日志中记录两条 Policy 均命中但最终效果为 deny

#### 场景：无 Policy 时仅资源权限判定

- **Given** 用户对资源 R 持有角色 Role-A，且租户 T 下无任何启用的 Policy
- **When** 调用权限判定引擎 `evaluate(user, action, resource)`
- **Then** 引擎仅执行第2层资源权限判定，返回基于角色-权限矩阵的判定结果，不执行第3层 Policy 求值

#### 场景：多租户隔离

- **Given** 租户 T1 下存在 Policy P1（deny），租户 T2 下存在 Policy P2（allow），两 Policy 条件均匹配资源 R
- **When** 租户 T1 的用户 U1 和租户 T2 的用户 U2 分别调用 `evaluate(user, action, resource)`
- **Then** U1 的判定仅考虑 T1 下的 Policy P1，返回 deny；U2 的判定仅考虑 T2 下的 Policy P2，返回 allow；两租户的 Policy 互不影响
