## 新增需求

### 需求:Dockerfile 支持 BUILD_MODULES 参数

系统必须提供 Dockerfile，支持 BUILD_MODULES 构建参数指定要打包的模块。

Dockerfile 必须：
- 接收 BUILD_MODULES 参数，默认值为 `demo,iam,tenant`
- 在构建阶段生成 `src/config/modules.ts` 配置文件
- 使用多阶段构建，分离构建和运行环境

#### 场景:构建平台版镜像
- **当** BUILD_MODULES=demo,iam,tenant
- **那么** 生成的镜像包含所有模块代码

#### 场景:构建独立模块镜像
- **当** BUILD_MODULES=demo
- **那么** 生成的镜像仅包含 demo 模块代码

#### 场景:默认构建参数
- **当** 未指定 BUILD_MODULES
- **那么** 使用默认值 demo,iam,tenant

### 需求:模块配置文件生成

系统必须在构建时生成 `src/config/modules.ts` 文件。

配置文件必须：
- 导出 `ENABLED_MODULES` 常量
- 包含指定的模块名称数组
- TypeScript 类型安全

#### 场景:生成配置文件格式正确
- **当** BUILD_MODULES=demo,iam
- **那么** 生成 `export const ENABLED_MODULES = ['demo', 'iam'];`

### 需求:构建产物优化

系统必须优化构建产物体积。

优化措施必须包括：
- 未使用模块代码不打包
- 利用 Vite 的 tree-shaking
- 静态资源压缩

#### 场景:独立模块构建体积更小
- **当** 构建单个模块
- **那么** 构建产物体积明显小于平台版

## 修改需求

无。

## 移除需求

无。
