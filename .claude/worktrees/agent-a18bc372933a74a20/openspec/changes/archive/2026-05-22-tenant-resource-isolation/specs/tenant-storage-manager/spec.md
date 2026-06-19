## ADDED Requirements

### Requirement: 存储桶路由管理

系统 SHALL 根据租户配置路由到独立存储桶。

#### Scenario: 租户配置独立存储桶
- **WHEN** 租户配置了 storage_bucket
- **THEN** 该租户的所有存储操作使用独立存储桶

#### Scenario: 租户无独立存储桶配置
- **WHEN** 租户未配置 storage_bucket
- **THEN** 使用默认存储桶
- **AND** 使用 tenant_id/ 路径前缀进行逻辑隔离

### Requirement: 文件上传隔离

系统 SHALL 自动将文件上传到租户对应的存储桶。

#### Scenario: 上传文件到独立存储桶
- **WHEN** 租户配置了独立存储桶且调用上传接口
- **THEN** 文件上传到租户的独立存储桶
- **AND** 无需手动指定存储桶名称

#### Scenario: 上传文件到默认存储桶（逻辑隔离）
- **WHEN** 租户未配置独立存储桶且调用上传接口
- **THEN** 文件上传到默认存储桶
- **AND** 文件路径自动添加 tenant_id/ 前缀

### Requirement: 文件下载隔离

系统 SHALL 自动从租户对应的存储桶下载文件。

#### Scenario: 从独立存储桶下载文件
- **WHEN** 租户配置了独立存储桶且调用下载接口
- **THEN** 从租户的独立存储桶下载文件

#### Scenario: 从默认存储桶下载文件（逻辑隔离）
- **WHEN** 租户未配置独立存储桶且调用下载接口
- **THEN** 从默认存储桶下载文件
- **AND** 自动添加 tenant_id/ 路径前缀

### Requirement: 存储桶自动创建

系统 SHALL 支持自动创建租户存储桶。

#### Scenario: 首次使用时创建存储桶
- **WHEN** 租户配置了独立存储桶但存储桶不存在
- **THEN** 系统自动创建该存储桶
- **AND** 设置适当的访问权限

### Requirement: 预签名 URL 生成

系统 SHALL 生成指向正确存储桶的预签名 URL。

#### Scenario: 生成独立存储桶的预签名 URL
- **WHEN** 租户配置了独立存储桶且请求预签名 URL
- **THEN** URL 指向租户的独立存储桶

#### Scenario: 生成默认存储桶的预签名 URL
- **WHEN** 租户未配置独立存储桶且请求预签名 URL
- **THEN** URL 指向默认存储桶的租户路径
