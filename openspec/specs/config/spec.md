## ADDED Requirements

### Requirement: YAML 配置文件加载
系统 SHALL 支持从 YAML 文件加载配置，支持 `application.yml` 和 `application-{env}.yml` 分层加载。

#### Scenario: 加载默认配置文件
- **WHEN** 应用启动时
- **THEN** 系统加载 `config/application.yml` 配置文件

#### Scenario: 环境配置覆盖
- **WHEN** 指定环境为 `local`
- **THEN** 系统先加载 `application.yml`，再加载 `application-local.yml` 覆盖相同配置项

### Requirement: Pydantic 配置验证
系统 SHALL 使用 Pydantic 对配置进行类型验证，配置不符合要求时抛出验证错误。

#### Scenario: 配置类型验证
- **WHEN** 配置项 `server.port` 应为整数但值为字符串
- **THEN** 系统抛出 ValidationError 异常

#### Scenario: 必填配置缺失
- **WHEN** 必填配置项缺失
- **THEN** 系统抛出 ValidationError 并提示缺失字段

### Requirement: 配置访问接口
系统 SHALL 提供全局配置访问接口 `settings`，支持点号访问嵌套配置。

#### Scenario: 访问顶层配置
- **WHEN** 调用 `settings.server.port`
- **THEN** 返回配置文件中定义的端口号

#### Scenario: 访问嵌套配置
- **WHEN** 调用 `settings.oss.minio.endpoint`
- **THEN** 返回 MinIO 端点配置

### Requirement: 环境变量覆盖
系统 SHALL 支持通过环境变量覆盖 YAML 配置，环境变量格式为 `SECTION__KEY`（双下划线分隔）。

#### Scenario: 环境变量覆盖端口
- **WHEN** 设置环境变量 `SERVER__PORT=9000`
- **THEN** `settings.server.port` 返回 `9000` 而非 YAML 中的值
