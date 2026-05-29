## 新增需求

### 需求:Dockerfile 支持 BUILD_MODULES 参数

系统必须提供 Dockerfile，支持 BUILD_MODULES 构建参数指定要打包的模块。

Dockerfile 必须：
- 接收 BUILD_MODULES 参数，默认值为 `demo,iam,tenant`
- 在构建阶段生成 `src/config/modules.py` 配置文件
- 使用多阶段构建，分离构建和运行环境
- 支持自动依赖解析

#### 场景:构建平台版镜像
- **当** BUILD_MODULES=demo,iam,tenant
- **那么** 生成的镜像包含所有模块代码，自动解析依赖

#### 场景:构建独立模块镜像
- **当** BUILD_MODULES=demo
- **那么** 自动包含 demo, iam, tenant 模块（依赖解析）

#### 场景:默认构建参数
- **当** 未指定 BUILD_MODULES
- **那么** 使用默认值 demo,iam,tenant

### 需求:Dockerfile 支持 APP_ROLE 参数

系统必须支持 APP_ROLE 构建参数，指定容器运行角色。

角色类型：
- `web`: Web API 服务
- `task`: 定时任务调度器
- `listener`: 消息监听器

Dockerfile 必须：
- 接收 APP_ROLE 参数，默认值为 `web`
- 将 APP_ROLE 设置为环境变量
- 在镜像标签中记录角色信息

#### 场景:构建 Web API 镜像
- **当** APP_ROLE=web
- **那么** 镜像标签包含 role=web

#### 场景:构建 Task 镜像
- **当** APP_ROLE=task
- **那么** 镜像标签包含 role=task

#### 场景:构建 Listener 镜像
- **当** APP_ROLE=listener
- **那么** 镜像标签包含 role=listener

### 需求:模块配置文件生成

系统必须在构建时生成 `src/config/modules.py` 文件。

配置文件必须：
- 导出 `ENABLED_MODULES` 常量
- 包含指定的模块名称列表
- Python 类型安全

#### 场景:生成配置文件格式正确
- **当** BUILD_MODULES=demo,iam
- **那么** 生成 `ENABLED_MODULES = ["demo", "iam"]`

#### 场景:配置文件包含构建信息
- **当** 生成配置文件
- **那么** 文件头部包含 BUILD_MODULES 注释

## 修改需求

无。

## 移除需求

无。
