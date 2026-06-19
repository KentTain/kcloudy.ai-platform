## ADDED Requirements

### Requirement: 存储路径隔离

系统 SHALL 自动为 MinIO 对象路径添加租户目录前缀。

#### Scenario: 上传文件自动添加前缀
- **WHEN** 调用 `StorageService.upload("avatars/user_123.jpg", file)` 且当前租户为 `tenant_001`
- **THEN** 实际存储路径为 `tenant_001/avatars/user_123.jpg`

#### Scenario: 下载文件自动添加前缀
- **WHEN** 调用 `StorageService.download("avatars/user_123.jpg")` 且当前租户为 `tenant_001`
- **THEN** 实际下载路径为 `tenant_001/avatars/user_123.jpg`

#### Scenario: 删除文件自动添加前缀
- **WHEN** 调用 `StorageService.delete("avatars/user_123.jpg")` 且当前租户为 `tenant_001`
- **THEN** 实际删除路径为 `tenant_001/avatars/user_123.jpg`

#### Scenario: 管理员场景跳过前缀
- **WHEN** 调用 `StorageService.upload("system/logo.png", file, skip_tenant=True)`
- **THEN** 实际存储路径为 `system/logo.png`（无租户前缀）

### Requirement: 预签名 URL 包含租户路径

系统 SHALL 在生成预签名 URL 时包含租户路径。

#### Scenario: 生成预签名 URL
- **WHEN** 调用 `StorageService.get_presigned_url("documents/report.pdf")` 且当前租户为 `tenant_001`
- **THEN** 返回的 URL 指向 `tenant_001/documents/report.pdf`

### Requirement: 列举对象隔离

系统 SHALL 在列举对象时自动过滤租户目录。

#### Scenario: 列举对象自动过滤
- **WHEN** 调用 `StorageService.list_objects("documents/")` 且当前租户为 `tenant_001`
- **THEN** 只返回 `tenant_001/documents/` 下的对象

### Requirement: 跨租户隔离验证

系统 SHALL 确保不同租户的存储数据相互隔离。

#### Scenario: 租户 A 无法访问租户 B 的文件
- **WHEN** 租户 A 尝试下载 `documents/report.pdf`
- **THEN** 无法下载到租户 B 的 `tenant_002/documents/report.pdf` 文件

#### Scenario: 租户 A 无法列举租户 B 的文件
- **WHEN** 租户 A 列举 `documents/` 目录
- **THEN** 只能看到 `tenant_001/documents/` 下的文件

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
