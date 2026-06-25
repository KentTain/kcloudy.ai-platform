# 插件管理功能实施任务

## 1. 基础设施（P0）

- [ ] 1.1 定义 PluginInstallationDTO、PluginRuntimeStateDTO、PluginConfigDTO 数据传输对象
- [ ] 1.2 定义 PluginInstallationProvider 协议
- [ ] 1.3 实现 Tenant 模块的 PluginInstallationProviderImpl
- [ ] 1.4 在应用入口注册 Provider
- [ ] 1.5 定义 PluginInstallationFailed、PluginUninstallFailed 领域事件
- [ ] 1.6 实现 Tenant 侧插件安装失败事件处理器

## 2. 数据库模型

- [ ] 2.1 创建 TenantPluginDefinition 模型（tenant.plugin_definitions 表）
- [ ] 2.2 创建 TenantPluginInstallation 模型（tenant.plugin_installations 表）
- [ ] 2.3 创建 PluginConfig 模型（ai.plugin_configs 表）
- [ ] 2.4 创建 PluginRuntimeState 模型（ai.plugin_runtime_states 表）
- [ ] 2.5 编写数据库迁移脚本（新增四张表）
- [ ] 2.6 新增 plugin_definitions 表字段（is_recommended、is_enabled）
- [ ] 2.7 新增 plugin_installations 表字段（install_type）

## 3. Tenant 模块 - 插件定义注册

- [ ] 3.1 实现插件包解析工具类（解析 manifest.yaml）
- [ ] 3.2 实现服务器目录扫描注册功能
- [ ] 3.3 实现本地上传 zip 包注册功能
- [ ] 3.4 实现远程 URL 拉取注册功能
- [ ] 3.5 创建插件定义注册 Service
- [ ] 3.6 创建插件定义注册 Controller（admin API）

## 4. Tenant 模块 - 插件定义管理

- [ ] 4.1 创建插件定义列表查询 Service
- [ ] 4.2 创建插件定义列表查询 Controller（分页、搜索、过滤）
- [ ] 4.3 创建插件定义详情查询 Service
- [ ] 4.4 创建插件定义详情查询 Controller
- [ ] 4.5 创建插件定义更新 Service（标记推荐/禁用）
- [ ] 4.6 创建插件定义更新 Controller
- [ ] 4.7 创建插件定义删除 Service（前置检查 refers）
- [ ] 4.8 创建插件定义删除 Controller

## 5. Tenant 模块 - 统计

- [ ] 5.1 创建定义侧统计 Service（总数、类型分布、推荐数）
- [ ] 5.2 创建安装侧统计 Service（总安装数、活跃数、周新增）
- [ ] 5.3 创建统计 Controller

## 6. AI 模块 - 重构 PluginManager

- [ ] 6.1 重构 _load_plugins_metadata_from_database 方法（使用 Provider）
- [ ] 6.2 重构 _load_plugin_info_from_installation 方法（分离数据源）
- [ ] 6.3 重构 _save_plugin_installation_to_database 方法（使用 Provider）
- [ ] 6.4 重构 _check_duplicate_installation 方法（使用 Provider）
- [ ] 6.5 重构 _ensure_plugin_ready 方法（查询 plugin_configs 表）
- [ ] 6.6 重构 start_plugin 方法（写入 plugin_runtime_states）
- [ ] 6.7 重构 stop_plugin 方法（更新状态到 Provider 和 runtime_states）
- [ ] 6.8 实现事件驱动的安装流程（发布失败事件）
- [ ] 6.9 实现事件驱动的卸载流程

## 7. AI 模块 - 可用插件浏览

- [ ] 7.1 创建可用插件列表 Service（从 Tenant Provider 获取定义）
- [ ] 7.2 创建可用插件列表 Controller（标记是否已安装）
- [ ] 7.3 创建已安装插件列表 Service（使用 Provider + AI 表）
- [ ] 7.4 创建已安装插件列表 Controller

## 8. AI 模块 - 插件安装/卸载

- [ ] 8.1 重构插件安装 Service（使用 Provider + 事件驱动）
- [ ] 8.2 重构插件安装 Controller
- [ ] 8.3 重构插件卸载 Service
- [ ] 8.4 重构插件卸载 Controller

## 9. AI 模块 - 启动/停止

- [ ] 9.1 重构启动插件 Service
- [ ] 9.2 重构启动插件 Controller
- [ ] 9.3 重构停止插件 Service
- [ ] 9.4 重构停止插件 Controller

## 10. AI 模块 - 配置管理

- [ ] 10.1 创建插件配置查询 Service
- [ ] 10.2 创建插件配置查询 Controller
- [ ] 10.3 创建插件配置更新 Service
- [ ] 10.4 创建插件配置更新 Controller

## 11. AI 模块 - 运行时监控

- [ ] 11.1 创建单个插件运行时状态查询 Service
- [ ] 11.2 创建单个插件运行时状态查询 Controller
- [ ] 11.3 创建批量运行时状态查询 Service
- [ ] 11.4 创建批量运行时状态查询 Controller

## 12. AI 模块 - 安装任务追踪

- [ ] 12.1 创建安装任务列表查询 Service
- [ ] 12.2 创建安装任务列表查询 Controller
- [ ] 12.3 创建安装任务详情查询 Service
- [ ] 12.4 创建安装任务详情查询 Controller

## 13. AI 模块 - 统计

- [ ] 13.1 创建状态统计 Service（ACTIVE、INACTIVE、PENDING、FAILED）
- [ ] 13.2 创建使用统计 Service（调用次数、错误次数、响应时间）
- [ ] 13.3 创建运行时统计 Service（进程数、内存、CPU）
- [ ] 13.4 创建统计 Controller

## 14. 前端 - Tenant 管理侧

- [ ] 14.1 创建插件定义列表页面（统计卡片 + 操作按钮 + 表格）
- [ ] 14.2 实现服务器目录扫描功能
- [ ] 14.3 实现本地上传插件功能
- [ ] 14.4 实现远程 URL 拉取功能
- [ ] 14.5 创建插件定义详情页面
- [ ] 14.6 实现标记推荐/禁用功能
- [ ] 14.7 实现删除插件定义功能

## 15. 前端 - AI 使用侧

- [ ] 15.1 创建插件管理页面（统计卡片 + 标签页）
- [ ] 15.2 实现已安装插件列表标签页
- [ ] 15.3 实现可用插件列表标签页
- [ ] 15.4 实现安装插件功能
- [ ] 15.5 实现卸载插件功能
- [ ] 15.6 实现启动/停止插件功能
- [ ] 15.7 创建插件详情页面（基本信息 + 配置 + 监控）
- [ ] 15.8 实现配置管理功能
- [ ] 15.9 实现运行时状态监控面板
- [ ] 15.10 实现安装任务追踪功能

## 16. 数据迁移（P1）

- [ ] 16.1 编写数据迁移脚本（ai.plugins → tenant.plugin_definitions）
- [ ] 16.2 编写数据迁移脚本（ai.plugin_declarations 合并到 plugin_definitions）
- [ ] 16.3 编写数据迁移脚本（ai.plugin_installations 字段分离）
- [ ] 16.4 执行数据迁移并验证
- [ ] 16.5 确认功能正常运行后删除旧表
- [ ] 16.6 删除旧模型定义代码

## 17. 测试

- [ ] 17.1 编写 PluginInstallationProvider 单元测试
- [ ] 17.2 编写 Tenant 模块插件定义管理单元测试
- [ ] 17.3 编写 AI 模块重构后单元测试
- [ ] 17.4 编写事件处理器单元测试
- [ ] 17.5 编写 Tenant 管理侧 API 集成测试
- [ ] 17.6 编写 AI 使用侧 API 集成测试
- [ ] 17.7 编写前端组件单元测试
- [ ] 17.8 编写前端 E2E 测试
