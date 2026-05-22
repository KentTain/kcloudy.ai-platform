## ADDED Requirements

### Requirement: 租户资源配置存储

系统 SHALL 允许为租户配置独立的数据库、存储、缓存资源。

#### Scenario: 创建租户时配置独立数据库
- **WHEN** 管理员创建租户并指定数据库配置（db_type、db_host、db_port、db_name、db_username、db_password）
- **THEN** 租户的数据库配置被加密存储
- **AND** 数据库密码使用 AES-256-GCM 加密

#### Scenario: 创建租户时配置独立存储桶
- **WHEN** 管理员创建租户并指定存储配置（storage_type、storage_bucket）
- **THEN** 租户的存储配置被存储

#### Scenario: 创建租户时配置独立缓存 DB
- **WHEN** 管理员创建租户并指定缓存配置（cache_db）
- **THEN** 租户的缓存配置被存储
- **AND** cache_db 值在 0-15 范围内

#### Scenario: 创建租户时不配置独立资源
- **WHEN** 管理员创建租户时不指定资源配置
- **THEN** 租户使用系统默认资源（逻辑隔离模式）

### Requirement: 敏感信息加密

系统 SHALL 使用 AES-256-GCM 加密存储数据库密码等敏感信息。

#### Scenario: 存储数据库密码时自动加密
- **WHEN** 管理员设置租户的数据库密码
- **THEN** 密码使用租户的 encryption_key 加密后存储

#### Scenario: 读取数据库密码时自动解密
- **WHEN** 系统需要访问租户的数据库密码
- **THEN** 使用租户的 encryption_key 解密

#### Scenario: 租户加密密钥自动生成
- **WHEN** 创建新租户时
- **THEN** 系统自动生成唯一的 encryption_key
- **AND** encryption_key 使用主密钥加密后存储

### Requirement: 资源配置更新

系统 SHALL 支持更新租户的资源配置。

#### Scenario: 更新数据库配置
- **WHEN** 管理员更新租户的数据库配置
- **THEN** 新配置立即生效
- **AND** 现有数据库连接池被标记为需要刷新

#### Scenario: 更新存储配置
- **WHEN** 管理员更新租户的存储桶配置
- **THEN** 后续操作使用新的存储桶

#### Scenario: 更新缓存配置
- **WHEN** 管理员更新租户的 Redis DB 配置
- **THEN** 后续操作使用新的 Redis DB

### Requirement: 资源配置验证

系统 SHALL 验证资源配置的有效性。

#### Scenario: 验证数据库连接
- **WHEN** 管理员保存数据库配置时
- **THEN** 系统尝试验证数据库连接
- **AND** 连接失败时返回错误信息

#### Scenario: 验证存储桶存在
- **WHEN** 管理员保存存储配置时
- **THEN** 系统验证存储桶是否存在
- **AND** 不存在时提示创建或选择其他桶

#### Scenario: 验证 Redis DB 编号范围
- **WHEN** 管理员保存缓存配置时
- **THEN** 系统验证 cache_db 在 0-15 范围内
- **AND** 超出范围时返回错误
