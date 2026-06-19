## ADDED Requirements

### Requirement: 登录页两列布局

LoginPage SHALL 采用两列布局：左侧为品牌展示区（渐变背景 + logo + 平台名称 + 描述文字），右侧为登录表单区。

#### Scenario: 大屏两列显示

- **WHEN** 用户在 lg 及以上断点访问登录页
- **THEN** 页面 SHALL 显示两列布局，左侧品牌区占约一半宽度，右侧表单区占约一半宽度

#### Scenario: 小屏单列回退

- **WHEN** 用户在 lg 以下断点访问登录页
- **THEN** 页面 SHALL 仅显示登录表单区，隐藏品牌展示区

#### Scenario: 品牌区内容

- **WHEN** 品牌展示区渲染
- **THEN** SHALL 展示平台名称 "AI 助手平台" 和简短描述文字

### Requirement: 登录表单 shadcn 组件化

LoginPage 登录表单 SHALL 使用 shadcn Card、Input、FormField、FormItem、FormLabel、FormMessage 组件替代 CommonCard/CommonInput。

#### Scenario: 表单组件替换

- **WHEN** LoginPage 登录表单渲染
- **THEN** SHALL 使用 shadcn Card 作为容器，shadcn Input 作为输入框，shadcn FormField/FormItem/FormLabel/FormMessage 构建表单项

#### Scenario: 移除 Common 组件依赖

- **WHEN** LoginPage 组件导入声明
- **THEN** SHALL 不包含对 CommonCard、CommonInput、CommonButton 的引用

### Requirement: 登录表单 vee-validate 校验

LoginPage 登录表单 SHALL 使用 vee-validate + zod schema 校验替代手写 ref 验证。

#### Scenario: zod schema 定义

- **WHEN** 登录表单校验逻辑初始化
- **THEN** SHALL 定义 zod schema 包含 username（必填、非空字符串）和 password（必填、最少 1 个字符）字段

#### Scenario: 表单提交校验

- **WHEN** 用户点击登录按钮提交表单
- **THEN** vee-validate SHALL 根据 zod schema 校验所有字段，校验失败时在对应 FormMessage 中显示错误提示

#### Scenario: 校验成功提交

- **WHEN** 表单校验通过后提交
- **THEN** SHALL 调用 authStore.login 执行登录逻辑

### Requirement: 登录按钮 shadcn 化

LoginPage 登录按钮 SHALL 使用 shadcn Button 替代 CommonButton。

#### Scenario: 按钮渲染

- **WHEN** 登录按钮渲染
- **THEN** SHALL 使用 shadcn Button，支持 loading 状态显示 spinner

#### Scenario: 加载状态

- **WHEN** 登录请求进行中
- **THEN** 按钮 SHALL 显示 loading spinner 并禁用点击

### Requirement: 统一错误页布局

ForbiddenPage 和 NotFoundPage SHALL 采用统一的错误页布局风格。

#### Scenario: 居中布局

- **WHEN** 403 或 404 页面渲染
- **THEN** SHALL 采用居中布局，大号错误码数字 + 标题 + 描述文字 + 操作按钮行

#### Scenario: ForbiddenPage 内容

- **WHEN** ForbiddenPage 渲染
- **THEN** SHALL 显示 "403" 错误码、"无访问权限" 标题、描述文案、"返回上一页" 和 "返回首页" 按钮

#### Scenario: NotFoundPage 内容

- **WHEN** NotFoundPage 渲染
- **THEN** SHALL 显示 "404" 错误码、"页面不存在" 标题、描述文案、"返回上一页" 和 "返回首页" 按钮

### Requirement: 错误页 shadcn 组件化

ForbiddenPage 和 NotFoundPage SHALL 使用 shadcn Button 替代 CommonButton。

#### Scenario: 移除 Common 组件依赖

- **WHEN** ForbiddenPage 或 NotFoundPage 组件导入声明
- **THEN** SHALL 不包含对 CommonButton 的引用

#### Scenario: 操作按钮

- **WHEN** 错误页操作按钮渲染
- **THEN** SHALL 使用 shadcn Button，"返回上一页" 使用 variant="outline"，"返回首页" 使用 variant="default"