## 新增需求

### 需求:角色分离 Entrypoint 脚本

系统必须提供 Entrypoint 脚本，根据 APP_ROLE 启动不同应用。

Entrypoint 脚本必须：
- 读取 APP_ROLE 环境变量
- 根据 role 执行对应的应用入口
- 输出启动日志
- 处理错误和退出码

#### 场景:Web 角色启动
- **当** APP_ROLE=web
- **那么** 执行 `uvicorn application_web:app --host 0.0.0.0 --port 8000`

#### 场景:Task 角色启动
- **当** APP_ROLE=task
- **那么** 执行 `uv run runtask`

#### 场景:Listener 角色启动
- **当** APP_ROLE=listener
- **那么** 执行 `uv run runlistener`

#### 场景:未知角色处理
- **当** APP_ROLE=unknown
- **那么** 输出错误信息并退出，退出码为 1

### 需求:应用入口读取模块配置

三个应用入口必须统一读取模块配置文件。

应用入口：
- application_web.py
- application_task.py
- application_listener.py

必须：
- 从 `config.modules` 导入 `ENABLED_MODULES`
- 如果配置文件不存在，加载所有模块
- 输出加载的模块列表日志

#### 场景:从配置文件加载模块
- **当** src/config/modules.py 存在
- **那么** 使用 ENABLED_MODULES 作为 module_names 参数

#### 场景:配置文件不存在
- **当** src/config/modules.py 不存在
- **那么** module_names 为 None，加载所有模块

#### 场景:日志输出模块列表
- **当** 应用启动
- **那么** 日志输出 "Loaded modules from config: ['demo', 'iam', 'tenant']"

### 需求:角色独立健康检查

每个角色必须配置适当的健康检查。

健康检查策略：
- Web 角色：HTTP `/health` 端点
- Task 角色：进程存活检查
- Listener 角色：进程存活检查

#### 场景:Web 健康检查
- **当** 访问 http://localhost:8000/health
- **那么** 返回 200 OK

#### 场景:Task 进程检查
- **当** Task 进程运行中
- **那么** Docker 健康检查通过

#### 场景:Listener 进程检查
- **当** Listener 进程运行中
- **那么** Docker 健康检查通过

### 需求:角色故障隔离

不同角色的故障必须相互隔离。

故障隔离要求：
- 一个角色崩溃不影响其他角色
- Docker 自动重启失败的容器
- 日志独立收集

#### 场景:Task 崩溃不影响 Web
- **当** backend-platform-task 崩溃
- **那么** backend-platform-api 继续提供服务

#### 场景:自动重启
- **当** 容器退出码非 0
- **那么** Docker 根据重启策略自动重启

## 修改需求

无。

## 移除需求

无。
