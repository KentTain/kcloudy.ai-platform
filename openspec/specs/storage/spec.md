## ADDED Requirements

### Requirement: MinIO 存储实现
系统 SHALL 实现 MinIO 存储提供者，支持文件上传、下载、删除、预签名 URL 功能。

#### Scenario: 上传文件
- **WHEN** 调用 `storage.upload("bucket", "path/file.txt", file_bytes)`
- **THEN** 文件上传到 MinIO，返回文件访问路径

#### Scenario: 下载文件
- **WHEN** 调用 `storage.download("bucket", "path/file.txt")`
- **THEN** 返回文件字节数据

#### Scenario: 删除文件
- **WHEN** 调用 `storage.delete("bucket", "path/file.txt")`
- **THEN** 文件被删除，返回 `True`

#### Scenario: 获取预签名 URL
- **WHEN** 调用 `storage.get_presigned_url("bucket", "path/file.txt", expires=3600)`
- **THEN** 返回 1 小时有效的预签名下载 URL

### Requirement: 存储工厂
系统 SHALL 提供存储工厂，根据配置 `oss.default-type` 返回对应的存储实现。

#### Scenario: 获取 MinIO 存储
- **WHEN** 配置 `oss.default-type=minio`
- **THEN** 工厂返回 MinioStorage 实例

#### Scenario: 获取阿里云存储
- **WHEN** 配置 `oss.default-type=aliyun`
- **THEN** 工厂返回 AliyunStorage 实例

### Requirement: 存储桶管理
系统 SHALL 支持存储桶的创建和检查。

#### Scenario: 检查存储桶存在
- **WHEN** 调用 `storage.bucket_exists("bucket")`
- **THEN** 返回存储桶是否存在

#### Scenario: 创建存储桶
- **WHEN** 调用 `storage.create_bucket("new-bucket")`
- **THEN** 创建新的存储桶

### Requirement: 文件存在检查
系统 SHALL 支持检查文件是否存在于存储中。

#### Scenario: 文件存在
- **WHEN** 调用 `storage.exists("bucket", "path/file.txt")` 且文件存在
- **THEN** 返回 `True`

#### Scenario: 文件不存在
- **WHEN** 调用 `storage.exists("bucket", "path/nonexistent.txt")` 且文件不存在
- **THEN** 返回 `False`
