## 1. 搜索残留

- [x] 1.1 全局搜索 `el-` 组件引用（`grep -rn "el-" web/vue/src/`）
- [x] 1.2 全局搜索 `element-plus` 依赖引入（`grep -rn "element-plus" web/vue/src/`）
- [x] 1.3 全局搜索 `ElementPlus` 类型导入（`grep -rn "ElementPlus" web/vue/src/`）
- [x] 1.4 整理搜索结果，确认所有需要清理的文件和位置

## 2. 清理残留代码

- [x] 2.1 清理模板中的 `<el-*>` 组件使用
- [x] 2.2 清理 import 语句中的 Element Plus 相关引入
- [x] 2.3 清理类型引用中的 ElementPlus 类型
- [x] 2.4 清理样式引入（如 `element-plus/theme-chalk`）

## 3. 移除全局注册

- [x] 3.1 移除 main.ts 中的 `import ElementPlus from 'element-plus'`
- [x] 3.2 移除 main.ts 中的 `app.use(ElementPlus)`
- [x] 3.3 移除 main.ts 中的 Element Plus 样式引入
- [x] 3.4 清理其他入口文件中的 Element Plus 注册（如有）

## 4. 移除依赖

- [x] 4.1 从 package.json 移除 `element-plus` 依赖
- [x] 4.2 从 package.json 移除 `@element-plus/icons-vue` 依赖（若存在）
- [x] 4.3 执行 `pnpm install` 更新依赖锁文件

## 5. 验证清理

- [x] 5.1 再次全局搜索确认零残留
- [x] 5.2 执行 `pnpm build` 编译检查
- [x] 5.3 执行 `pnpm test:unit` 单元测试验证
- [x] 5.4 浏览器验证主要功能页面正常渲染
