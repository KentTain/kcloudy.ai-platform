## ADDED Requirements

### Requirement: 独立存储桶物理隔离

系统 SHALL 支持租户使用独立的存储桶，实现存储数据物理隔离。

#### Scenario: 租户使用独立存储桶
- **WHEN** 租户配置了独立存储桶（storage_bucket 不为空）
- **THEN** 租户文件存储在独立存储桶中
- **AND** 文件完全物理隔离，无法被其他租户访问

#### Scenario: 独立存储桶无需路径前缀
- **WHEN** 租户使用独立存储桶
- **THEN** 文件路径无需添加 tenant_id/ 前缀
- **AND** 路径直接使用原始路径

### Requirement: 存储模式选择

系统 SHALL 支持逻辑隔离和物理隔离两种存储模式。

#### Scenario: 逻辑隔离模式
- **WHEN** 租户未配置独立存储桶
- **THEN** 使用共享存储桶 + tenant_id/ 路径前缀
- **AND** 文件自动添加租户前缀

#### Scenario: 物理隔离模式
- **WHEN** 租户配置了独立存储桶
- **THEN** 使用独立存储桶
- **AND** 文件路径不添加租户前缀

### Requirement: 跨模式访问控制

系统 SHALL 确保不同隔离模式的租户数据相互隔离。

#### Scenario: 逻辑隔离租户无法访问物理隔离租户数据
- **WHEN** 租户 A 使用逻辑隔离，租户 B 使用物理隔离
- **THEN** 租户 A 无法访问租户 B 的文件

#### Scenario: 物理隔离租户无法访问逻辑隔离租户数据
- **WHEN** 租户 A 使用物理隔离，租户 B 使用逻辑隔离
- **THEN** 租户 A 无法访问租户 B 的文件
