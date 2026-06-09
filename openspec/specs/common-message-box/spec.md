# common-message-box 规格

## 概述

服务式 API 消息框组件，支持 Promise 链式调用，类似 Element Plus 的 ElMessageBox。

## 功能需求

### 核心功能

- 服务式 API 调用（MessageBox.confirm/alert/success/error/info）
- Promise 返回值支持 async/await
- 自定义标题、内容、类型
- 关闭前回调（beforeClose）

### 服务 API

```typescript
// 确认对话框
MessageBox.confirm(options: MessageBoxOptions): Promise<boolean>

// 快捷方法
MessageBox.alert(content: string, title?: string): Promise<boolean>
MessageBox.success(content: string, title?: string): Promise<boolean>
MessageBox.error(content: string, title?: string): Promise<boolean>
MessageBox.info(content: string, title?: string): Promise<boolean>
MessageBox.confirmWithOptions(content: string, title?: string, type?: MessageBoxType): Promise<boolean>
```

### 类型定义

```typescript
type MessageBoxType = 'info' | 'success' | 'warning' | 'error'

interface MessageBoxOptions {
  title?: string
  content?: string
  type?: MessageBoxType
  showCancel?: boolean
  beforeClose?: (action: 'confirm' | 'cancel', done: () => void) => void
}
```

## 迁移来源

- 源文件：`D:\Project\ai\Alon\apps\kbhub\web\src\components\alon\alon-message-box\`
- 目标位置：`web/vue/src/components/common/feedback/message-box/`

## 文件清单

| 源文件 | 目标文件 |
|--------|----------|
| AlonMessageBox.vue | MessageBox.vue |
| messageBox.ts | messageBox.ts |
| index.ts | index.ts |

## 依赖

- ui/dialog
- vue（createApp, h, ref）

## 验收标准

- [ ] 组件迁移完成，文件位置正确
- [ ] 重命名完成（移除 Alon 前缀）
- [ ] 服务 API 正常工作
- [ ] 构建通过
