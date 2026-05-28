## 新增需求

### 需求:构建时模块选择

系统必须支持通过 BUILD_MODULES 环境变量控制构建时包含哪些模块。

当 BUILD_MODULES 未设置时，系统必须默认包含所有模块（demo、iam、tenant）。

BUILD_MODULES 必须接受逗号分隔的模块名称列表。

#### 场景:构建所有模块
- **当** BUILD_MODULES 未设置
- **那么** 构建产物包含 demo、iam、tenant 所有模块的代码

#### 场景:构建指定模块
- **当** 设置 BUILD_MODULES=demo,iam
- **那么** 构建产物仅包含 demo 和 iam 模块的代码

#### 场景:构建单个模块
- **当** 设置 BUILD_MODULES=demo
- **那么** 构建产物仅包含 demo 模块的代码

#### 场景:构建不存在的模块
- **当** 设置 BUILD_MODULES=nonexistent
- **那么** 构建必须失败并输出错误信息

### 需求:虚拟模块生成

系统必须通过 Vite 插件生成虚拟模块，导出 BUILD_MODULES 列表。

虚拟模块必须导出 BUILD_MODULES 常量，类型为 string[]。

main.ts 必须从虚拟模块导入 BUILD_MODULES 并只注册列表中的模块。

#### 场景:导入虚拟模块
- **当** 构建过程中
- **那么** Vite 插件生成虚拟模块，导出 BUILD_MODULES 列表

#### 场景:只注册选中模块
- **当** BUILD_MODULES=demo,iam
- **那么** main.ts 只注册 demo 和 iam 模块，tenant 模块不注册

### 需求:模块依赖检查

系统必须在构建时检查模块依赖完整性。

如果 BUILD_MODULES 包含的模块依赖未包含的模块，构建必须失败并输出依赖错误。

#### 场景:依赖完整性检查通过
- **当** BUILD_MODULES=demo,iam 且 demo 依赖 iam
- **那么** 构建成功

#### 场景:依赖缺失检查失败
- **当** BUILD_MODULES=demo 且 demo 依赖 iam
- **那么** 构建失败，输出错误：模块 demo 依赖 iam 但 iam 未包含在 BUILD_MODULES 中

### 需求:Tree-shaking 支持

系统必须通过 tree-shaking 移除未选中模块的代码。

未选中模块的代码禁止出现在最终构建产物中。

#### 场景:未选中模块代码被移除
- **当** BUILD_MODULES=demo
- **那么** 构建产物中不包含 iam 和 tenant 模块的代码
