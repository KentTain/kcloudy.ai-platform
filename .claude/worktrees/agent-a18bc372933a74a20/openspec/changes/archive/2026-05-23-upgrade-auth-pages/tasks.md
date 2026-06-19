## 1. 依赖安装

- [x] 1.1 安装 shadcn form 组件：`npx shadcn-vue@latest add form`（包含 vee-validate + zod 依赖）
- [x] 1.2 安装 shadcn badge 组件：`npx shadcn-vue@latest add badge`

## 2. LoginPage 重写

- [x] 2.1 重写 LoginPage.vue（lg:grid-cols-2），左侧品牌区（渐变背景 + logo + 平台描述），右侧表单区使用 shadcn Card 包裹
- [x] 2.2 实现登录表单 vee-validate + zod schema 校验：定义 loginSchema（username: z.string().min(1, "请输入用户名"), password: z.string().min(1, "请输入密码")），使用 useForm + toTypedSchema
- [x] 2.3 替换表单输入组件：CommonInput → shadcn Input + FormField/FormItem/FormLabel/FormMessage
- [x] 2.4 替换登录按钮：CommonButton → shadcn Button（type="submit"，loading 状态使用 :disabled + spinner）
- [x] 2.5 处理登录错误响应：authStore.login catch 错误在表单上方展示 error banner
- [x] 2.6 移除 LoginPage 中对 CommonCard/CommonInput/CommonButton 的所有导入和引用

## 3. 错误页重写

- [x] 3.1 重写 ForbiddenPage.vue — 居中布局 + 大号 "403" 错误码 + "无访问权限" 标题 + 描述文案 + shadcn Button 操作行（outline + default）
- [x] 3.2 重写 NotFoundPage.vue — 居中布局 + 大号 "404" 错误码 + "页面不存在" 标题 + 描述文案 + shadcn Button 操作行（outline + default）
- [x] 3.3 移除 ForbiddenPage 和 NotFoundPage 中对 CommonButton 的所有导入和引用

## 4. 测试

- [x] 4.1 更新 LoginPage 相关测试：验证 vee-validate 表单校验行为（空用户名/空密码显示错误提示）
- [x] 4.2 更新 ForbiddenPage/NotFoundPage 测试：验证 shadcn Button 替代 CommonButton 后的交互行为
- [x] 4.3 验证小屏断点（< lg）LoginPage 仅显示表单区、隐藏品牌区