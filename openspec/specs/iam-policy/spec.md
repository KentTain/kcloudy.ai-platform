# 企业 Policy 规范

## Purpose

定义 IAM 模块的企业 Policy 能力，支持 Policy 的创建、编辑、启用、停用与条件匹配求值，遵循 deny 优先于所有 allow 的合并规则，停用后不参与判定，命中写入审计日志，并实现多租户隔离。

## Requirements

### Requirement: 企业 Policy

企业 Policy SHALL 支持 Policy 的创建/编辑/启用/停用、条件匹配求值、deny 优先于所有 allow、停用后不参与判定、命中审计与多租户隔离。

#### 场景：创建/编辑/启用/停用 Policy

- **Given** 租户 T1 的管理员登录系统
- **When** 管理员依次执行：创建 Policy P1（条件为密级=机密，效果为 deny）→ 编辑 P1 增加下载限制条件 → 启用 P1 → 停用 P1
- **Then** 创建后 P1 状态为 disabled（默认停用），编辑后条件更新为密级=机密 AND 下载限制=true，启用后状态为 enabled，停用后状态为 disabled；每次操作均记录审计日志

#### 场景：Policy 条件匹配

- **Given** 租户 T1 下存在一条启用的 Policy P1，条件包含：密级=机密、下载限制=true、DLP=启用、水印=强制、入库=需审批、问答=禁止
- **When** 权限判定引擎对资源 R1 求值，R1 的属性为密级=机密、下载限制=true、DLP=启用、水印=强制、入库=需审批、问答=禁止
- **Then** Policy P1 的所有条件均匹配，P1 命中，效果生效；若 R1 任一属性不满足条件，则 P1 不命中

#### 场景：Policy deny 优先于所有 allow

- **Given** 租户 T1 下存在两条启用的 Policy：P-allow（条件匹配，效果为 allow）和 P-deny（条件匹配，效果为 deny）
- **When** 权限判定引擎对资源 R1 求值，R1 同时满足两条 Policy 的条件
- **Then** 两条 Policy 均命中，但 deny 效果优先于 allow，最终判定结果为 deny；即使存在多条 allow Policy，只要有一条 deny 命中，结果均为 deny

#### 场景：停用 Policy 后不再参与权限判定

- **Given** 租户 T1 下存在 Policy P1，状态为 enabled，条件匹配资源 R1，效果为 deny
- **When** 管理员停用 P1，随后权限判定引擎对资源 R1 求值
- **Then** P1 状态为 disabled，不参与权限判定求值，R1 不再受 P1 的 deny 约束；若无其他 deny Policy 命中，判定结果由资源权限和剩余 allow Policy 决定

#### 场景：Policy 命中审计

- **Given** 租户 T1 下存在启用的 Policy P1，条件匹配资源 R1
- **When** 权限判定引擎对资源 R1 求值，P1 命中
- **Then** 系统写入审计日志，记录包含：命中的 Policy ID、Policy 名称、Policy 效果（allow/deny）、匹配的条件、判定时间、操作用户、资源信息

#### 场景：多租户隔离

- **Given** 租户 T1 下存在 Policy P1（deny），租户 T2 下存在 Policy P2（allow）
- **When** 租户 T1 的管理员查询 Policy 列表，租户 T2 的管理员查询 Policy 列表
- **Then** T1 管理员仅可见 P1，T2 管理员仅可见 P2；T1 的权限判定仅考虑 P1，T2 的权限判定仅考虑 P2；T1 管理员不可编辑/启停/删除 T2 的 Policy，反之亦然

