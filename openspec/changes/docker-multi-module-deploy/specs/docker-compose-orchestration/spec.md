## 新增需求

### 需求:多服务 Docker Compose 配置

系统必须提供 Docker Compose 配置，支持多服务编排。

配置必须支持以下服务：
- demo-service：demo 模块前端服务
- iam-service：iam 模块前端服务
- tenant-service：tenant 模块前端服务
- nginx：反向代理服务

每个服务必须使用相同的 Dockerfile，通过 BUILD_MODULES 参数区分。

#### 场景:启动所有服务
- **当** 运行 docker-compose up
- **那么** 启动 demo、iam、tenant 和 nginx 四个服务

#### 场景:启动单个服务
- **当** 运行 docker-compose up demo-service
- **那么** 仅启动 demo-service 及其依赖服务

#### 场景:服务独立构建
- **当** 构建 demo-service
- **那么** 使用 BUILD_MODULES=demo 构建镜像

### 需求:Docker 多阶段构建

Dockerfile 必须使用多阶段构建优化镜像大小。

构建阶段划分：
- base：安装依赖
- builder：编译代码
- runtime：Nginx 运行时

最终镜像必须只包含构建产物和运行时依赖。

#### 场景:多阶段构建
- **当** 构建 Docker 镜像
- **那么** 最终镜像大小显著小于单阶段构建

#### 场景:构建缓存
- **当** 依赖未变更
- **那么** 利用 Docker 缓存层加速构建

### 需求:环境变量配置

Docker Compose 必须支持通过环境变量配置服务参数。

必须支持以下环境变量：
- BUILD_MODULES：构建时包含的模块
- API_GATEWAY_URL：API 网关地址
- MODULE_DOMAIN：模块外部域名

#### 场景:使用环境变量配置
- **当** 设置 BUILD_MODULES=demo
- **那么** 构建的镜像只包含 demo 模块

#### 场景:默认环境变量
- **当** 未设置环境变量
- **那么** 使用配置文件中的默认值

### 需求:服务健康检查

每个服务必须配置健康检查。

健康检查必须验证服务是否正常响应 HTTP 请求。

Docker Compose 必须在健康检查失败时重启服务。

#### 场景:健康检查通过
- **当** 服务正常响应 HTTP 请求
- **那么** 健康检查状态为 healthy

#### 场景:健康检查失败
- **当** 服务无响应
- **那么** Docker 重启服务

### 需求:部署文档

系统必须提供多模块部署文档。

文档必须包含：
- 单体部署步骤
- 分离部署步骤
- 混合部署步骤
- 环境变量说明
- 常见问题解答

#### 场景:阅读部署文档
- **当** 查看 docs/deploy/multi-module.md
- **那么** 文档包含完整的部署步骤和示例
