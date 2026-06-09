# AI Elements 组件库

AI Elements 是一组专为 AI 对话场景设计的 Vue 组件，用于构建 AI 助手、聊天界面、代码展示等交互体验。

## 组件分类

### 对话核心组件

| 组件 | 用途 |
|------|------|
| Conversation | 对话容器，管理消息列表和滚动 |
| Message | 单条消息容器 |
| MessageContent | 消息内容展示 |
| MessageAvatar | 消息头像 |
| MessageActions | 消息操作按钮组 |
| MessageToolbar | 消息工具栏 |

### Agent 组件

| 组件 | 用途 |
|------|------|
| Agent | Agent 容器 |
| AgentHeader | Agent 头部信息 |
| AgentContent | Agent 内容区域 |
| AgentInstructions | Agent 指令展示 |
| AgentOutput | Agent 输出展示 |
| AgentTools | Agent 工具列表 |
| AgentTool | 单个工具卡片 |

### 内容展示组件

| 组件 | 用途 |
|------|------|
| Artifact | 内容块容器（代码、文档等） |
| ArtifactHeader | 内容块头部 |
| ArtifactContent | 内容块内容 |
| ArtifactActions | 内容块操作 |
| CodeBlock | 代码块展示 |
| CodeBlockHeader | 代码块头部 |
| CodeBlockContent | 代码块内容 |
| CodeBlockCopyButton | 复制按钮 |
| Image | 图片展示 |
| FileTree | 文件树 |

### 交互反馈组件

| 组件 | 用途 |
|------|------|
| ChainOfThought | 思考链展示 |
| ChainOfThoughtStep | 思考步骤 |
| ChainOfThoughtContent | 思考内容 |
| Loader | 加载动画 |
| Shimmer | 骨架屏闪烁效果 |
| Progress | 进度条 |
| Spinner | 旋转加载器 |

### 输入组件

| 组件 | 用途 |
|------|------|
| PromptInput | 提示词输入框 |
| SpeechInput | 语音输入 |
| Attachments | 附件列表 |
| Attachment | 单个附件 |
| AttachmentPreview | 附件预览 |

### 选择器组件

| 组件 | 用途 |
|------|------|
| ModelSelector | 模型选择器 |
| MicSelector | 麦克风选择器 |
| VoiceSelector | 语音选择器 |

### 工具调用组件

| 组件 | 用途 |
|------|------|
| Tool | 工具卡片 |
| ToolHeader | 工具头部 |
| ToolInput | 工具输入参数 |
| ToolOutput | 工具输出结果 |
| ToolStatusBadge | 工具状态徽章 |

### 引用与来源组件

| 组件 | 用途 |
|------|------|
| InlineCitation | 内联引用 |
| InlineCitationCard | 引用卡片 |
| InlineCitationSource | 引用来源 |
| Sources | 来源列表 |

### 测试与调试组件

| 组件 | 用途 |
|------|------|
| TestResults | 测试结果容器 |
| TestSuite | 测试套件 |
| TestCase | 测试用例 |
| StackTrace | 堆栈跟踪 |

### 其他组件

| 组件 | 用途 |
|------|------|
| Confirmation | 确认对话框 |
| Checkpoint | 检查点 |
| Commit | Git 提交展示 |
| PackageInfo | 包信息展示 |
| Sandbox | 沙盒环境 |
| Terminal | 终端模拟 |
| WebPreview | 网页预览 |
| AudioPlayer | 音频播放器 |
| Transcription | 语音转写 |

## 导入方式

```typescript
// 直接从组件目录导入
import Message from '@/components/ai-elements/message/Message.vue';
import CodeBlock from '@/components/ai-elements/code-block/CodeBlock.vue';
```

## 使用示例

### 基础对话

```vue
<script setup lang="ts">
import Conversation from '@/components/ai-elements/conversation/Conversation.vue';
import Message from '@/components/ai-elements/message/Message.vue';
import MessageContent from '@/components/ai-elements/message/MessageContent.vue';
import MessageAvatar from '@/components/ai-elements/message/MessageAvatar.vue';
</script>

<template>
  <Conversation>
    <Message>
      <MessageAvatar src="/avatar.png" />
      <MessageContent>你好，有什么可以帮助你的？</MessageContent>
    </Message>
  </Conversation>
</template>
```

### 代码块展示

```vue
<script setup lang="ts">
import CodeBlock from '@/components/ai-elements/code-block/CodeBlock.vue';
</script>

<template>
  <CodeBlock language="typescript">
    const greeting = "Hello, World!";
  </CodeBlock>
</template>
```

## 设计原则

1. **组合式设计**：组件采用 Compound Component 模式，通过组合实现灵活布局
2. **无样式限制**：基于 shadcn/ui，可自定义样式
3. **类型安全**：完整的 TypeScript 类型定义
4. **AI 场景优化**：专为 AI 对话场景设计，内置思考链、工具调用等特性