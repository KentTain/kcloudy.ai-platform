# AI SDK 数据结构与对话功能分析报告

## 一、AI SDK 完整数据结构

### 1. UIMessage 核心结构

```typescript
interface UIMessage<METADATA = unknown, DATA_PARTS extends UIDataTypes = UIDataTypes, TOOLS extends UITools = UITools> {
  id: string;
  role: 'system' | 'user' | 'assistant';
  metadata?: METADATA;
  parts: Array<UIMessagePart<DATA_PARTS, TOOLS>>;
}
```

### 2. UIMessagePart 完整类型

AI SDK 支持以下 **9 种**消息部分类型：

| 类型 | 说明 | 当前支持 |
|------|------|----------|
| **TextUIPart** | 文本内容 | ✅ 已支持 |
| **ReasoningUIPart** | 推理/思考过程 | ✅ 已支持（ThinkingPart） |
| **ToolUIPart** | 静态工具调用 | ✅ 已支持（ToolCallPart） |
| **DynamicToolUIPart** | 动态工具调用 | ❌ 未支持 |
| **SourceUrlUIPart** | URL 来源引用 | ❌ 未支持 |
| **SourceDocumentUIPart** | 文档来源引用 | ❌ 未支持 |
| **FileUIPart** | 文件附件 | ✅ 部分支持（ImagePart） |
| **DataUIPart** | 自定义数据 | ❌ 未支持 |
| **StepStartUIPart** | 步骤边界标记 | ❌ 未支持 |

### 3. UI Chunk 事件类型

AI SDK 定义了 **12 种**流式事件：

| 事件类型 | 说明 | 当前支持 |
|---------|------|----------|
| `text-start` | 文本开始 | ✅ 已支持 |
| `text-delta` | 文本增量 | ✅ 已支持 |
| `text-end` | 文本结束 | ✅ 已支持 |
| `reasoning-start` | 推理开始 | ✅ 已支持（thinking-start） |
| `reasoning-delta` | 推理增量 | ✅ 已支持（thinking-delta） |
| `reasoning-end` | 推理结束 | ✅ 已支持（thinking-end） |
| `tool-call` | 工具调用 | ✅ 已支持 |
| `tool-result` | 工具结果 | ✅ 已支持 |
| `source-url` | URL 来源 | ❌ 未支持 |
| `source-document` | 文档来源 | ❌ 未支持 |
| `data` | 自定义数据 | ❌ 未支持 |
| `step-start` | 步骤开始 | ❌ 未支持 |

---

## 二、现有对话接口功能清单

### 已实现功能 ✅

#### 后端（Python）

1. **核心对话功能**
   - ✅ 流式对话（SSE）
   - ✅ 会话管理（创建/恢复/删除）
   - ✅ 消息历史存储
   - ✅ 多模型支持

2. **消息部分支持**
   - ✅ 文本消息（TextPart）
   - ✅ 思考过程（ThinkingPart）
   - ✅ 图片消息（ImagePart）
   - ✅ 工具调用（ToolCallPart）
   - ✅ 工具结果（ToolResultPart）

3. **事件处理**
   - ✅ 文本流式事件
   - ✅ 思考过程事件
   - ✅ 工具调用事件
   - ✅ 错误处理事件

4. **安全特性**
   - ✅ 三层敏感信息过滤
   - ✅ 租户隔离
   - ✅ 用户认证

#### 前端（Vue）

1. **UI 组件**
   - ✅ Conversation（对话容器）
   - ✅ Message（消息展示）
   - ✅ ThinkingBlock（思考过程）
   - ✅ ToolCallItem（工具调用）
   - ✅ PromptInput（输入框）
   - ✅ ModelSelector（模型选择）

2. **状态管理**
   - ✅ 会话列表
   - ✅ 消息管理
   - ✅ 流式状态

---

## 三、缺失功能分析

### 🔴 高优先级缺失功能

#### 1. 来源引用（Source Citation）

**影响**：搜索类工具无法展示引用来源，用户无法验证信息可靠性

**需要添加**：
- `SourceUrlUIPart`：URL 来源
  ```typescript
  type SourceUrlUIPart = {
    type: 'source-url';
    sourceId: string;
    url: string;
    title?: string;
    providerMetadata?: ProviderMetadata;
  };
  ```
- `SourceDocumentUIPart`：文档来源
  ```typescript
  type SourceDocumentUIPart = {
    type: 'source-document';
    sourceId: string;
    mediaType: string;
    url: string;
    title?: string;
    providerMetadata?: ProviderMetadata;
  };
  ```

**应用场景**：
- 搜索工具展示搜索结果来源
- RAG 检索展示文档引用
- 多模态引用（图片、视频等）

#### 2. 文件附件（File Attachment）

**影响**：无法上传和展示文件附件

**需要扩展**：
```typescript
type FileUIPart = {
  type: 'file';
  mediaType: string;
  url: string;
  filename?: string;
  providerMetadata?: ProviderMetadata;
};
```

**应用场景**：
- 上传 PDF/Word/Excel 分析
- 代码文件上传
- 音视频文件处理

#### 3. 自定义数据（Custom Data）

**影响**：无法传输结构化数据（如表格、图表、JSON）

**需要添加**：
```typescript
type DataUIPart<DATA_TYPES extends UIDataTypes> = {
  type: T; // 自定义类型标识
  id: string;
  content: unknown; // 自定义数据内容
};
```

**应用场景**：
- 图表数据展示
- 表格数据渲染
- 结构化 JSON 展示

#### 4. 步骤边界（Step Boundary）

**影响**：多步骤任务无法清晰划分

**需要添加**：
```typescript
type StepStartUIPart = {
  type: 'step-start';
};
```

**应用场景**：
- Agent 多步骤任务
- 复杂工作流展示
- 调试步骤追踪

### 🟡 中优先级缺失功能

#### 5. 动态工具调用（Dynamic Tool）

**影响**：无法支持运行时动态注册的工具

**需要添加**：
```typescript
type DynamicToolUIPart = {
  type: 'tool-invocation';
  toolCall: DynamicToolCall;
};
```

**应用场景**：
- 用户自定义工具
- 插件系统
- 运行时工具发现

#### 6. 消息元数据（Message Metadata）

**影响**：无法附加额外消息信息

**需要扩展**：
```typescript
interface UIMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  parts: UIMessagePart[];
  metadata?: METADATA; // 添加元数据字段
}
```

**应用场景**：
- 消息评分/反馈
- 消息标签
- 消息来源追踪

#### 7. Provider Metadata

**影响**：无法携带提供商特定信息

**需要扩展**：
```typescript
interface UIMessagePart {
  type: string;
  providerMetadata?: ProviderMetadata;
}
```

**应用场景**：
- Token 使用统计
- 模型信息
- 提供商特定功能

### 🟢 低优先级缺失功能

#### 8. 消息状态管理

**当前缺失**：
- 消息编辑状态
- 消息删除状态
- 消息重新生成状态

#### 9. 多模态输入支持

**当前缺失**：
- 语音输入集成
- 图像理解
- 视频处理

---

## 四、AI Elements 组件扩展建议

### 🔴 高优先级组件

#### 1. Sources 组件

**用途**：展示来源引用列表

**组件设计**：
```vue
<Sources>
  <SourceUrlCard
    v-for="source in sources"
    :key="source.sourceId"
    :url="source.url"
    :title="source.title"
  />
</Sources>
```

**现有组件**：
- ✅ `InlineCitation`：内联引用
- ✅ `Sources`：来源列表
- ❌ `SourceUrlCard`：URL 来源卡片（需新增）
- ❌ `SourceDocumentCard`：文档来源卡片（需新增）

#### 2. FileAttachment 组件

**用途**：文件上传和展示

**组件设计**：
```vue
<Attachments>
  <FileAttachment
    v-for="file in files"
    :key="file.id"
    :file="file"
    :on-preview="handlePreview"
  />
</Attachments>
```

**现有组件**：
- ✅ `Attachments`：附件容器
- ✅ `Attachment`：单个附件
- ✅ `AttachmentPreview`：附件预览
- ❌ 需扩展支持更多文件类型

#### 3. DataVisualization 组件

**用途**：自定义数据可视化

**组件设计**：
```vue
<DataVisualization :data="chartData" type="chart" />
<DataTable :data="tableData" />
```

**现有组件**：
- ✅ `common/DataTable`：数据表格
- ❌ `ChartVisualization`：图表可视化（需新增）
- ❌ `JsonDisplay`：JSON 展示（需新增）

### 🟡 中优先级组件

#### 4. StepIndicator 组件

**用途**：展示多步骤任务进度

**组件设计**：
```vue
<StepIndicator :current-step="2" :total-steps="5">
  <Step title="分析问题" :status="'done'" />
  <Step title="搜索资料" :status="'active'" />
  <Step title="生成答案" :status="'pending'" />
</StepIndicator>
```

**现有组件**：
- ✅ `Progress`：进度条
- ✅ `Spinner`：加载器
- ❌ `StepIndicator`：步骤指示器（需新增）

#### 5. MessageFeedback 组件

**用途**：消息评分和反馈

**组件设计**：
```vue
<MessageActions>
  <MessageFeedback
    :message-id="message.id"
    @rate="handleRate"
    @feedback="handleFeedback"
  />
</MessageActions>
```

**现有组件**：
- ✅ `MessageActions`：消息操作容器
- ✅ `MessageAction`：单个操作按钮
- ❌ `MessageFeedback`：反馈组件（需新增）

---

## 五、实施建议

### Phase 1：核心功能补全（2 周）

**目标**：支持完整的 AI SDK 数据结构

#### 任务清单

1. **后端扩展**
   - [ ] 添加 `SourceUrlUIPart` 支持
   - [ ] 添加 `SourceDocumentUIPart` 支持
   - [ ] 扩展 `FileUIPart` 支持多文件类型
   - [ ] 添加 `DataUIPart` 自定义数据支持
   - [ ] 实现 SSE 事件：`source-url`, `source-document`, `data`

2. **前端扩展**
   - [ ] 更新 `UIMessagePart` 类型定义
   - [ ] 实现 `SourceUrlCard` 组件
   - [ ] 实现 `SourceDocumentCard` 组件
   - [ ] 扩展 `FileAttachment` 组件
   - [ ] 实现 `DataVisualization` 组件

3. **测试覆盖**
   - [ ] 单元测试：新数据类型处理
   - [ ] 集成测试：SSE 事件流
   - [ ] E2E 测试：UI 交互

### Phase 2：体验优化（1 周）

**目标**：提升用户体验

#### 任务清单

1. **交互优化**
   - [ ] 来源引用点击跳转
   - [ ] 文件预览增强
   - [ ] 数据可视化交互
   - [ ] 步骤进度展示

2. **性能优化**
   - [ ] 大文件上传优化
   - [ ] 数据缓存策略
   - [ ] 懒加载优化

### Phase 3：高级功能（1 周）

**目标**：支持高级特性

#### 任务清单

1. **动态工具支持**
   - [ ] 实现 `DynamicToolUIPart`
   - [ ] 工具动态注册机制
   - [ ] 工具发现 UI

2. **元数据扩展**
   - [ ] 消息元数据存储
   - [ ] Provider Metadata 支持
   - [ ] 统计信息展示

---

## 六、优先级矩阵

| 功能 | 影响范围 | 实现难度 | 优先级 | 预计工作量 |
|------|---------|---------|--------|-----------|
| 来源引用 | 高 | 低 | 🔴 P0 | 3 天 |
| 文件附件 | 中 | 中 | 🔴 P0 | 4 天 |
| 自定义数据 | 高 | 中 | 🔴 P0 | 5 天 |
| 步骤边界 | 中 | 低 | 🟡 P1 | 2 天 |
| 动态工具 | 低 | 高 | 🟡 P1 | 5 天 |
| 元数据 | 中 | 低 | 🟢 P2 | 2 天 |
| 多模态 | 低 | 高 | 🟢 P2 | 5 天 |

---

## 七、技术债务

### 当前问题

1. **类型定义不完整**
   - 未完整对齐 AI SDK 类型
   - 缺少泛型支持
   - 缺少类型守卫

2. **组件复用不足**
   - 部分组件重复实现
   - 缺少统一入口
   - 样式不一致

3. **测试覆盖不足**
   - 前端组件测试缺失
   - E2E 测试不全
   - 性能测试缺失

### 解决方案

1. **重构类型定义**
   - 完整对齐 AI SDK 类型
   - 使用泛型增强灵活性
   - 添加类型守卫函数

2. **组件库整理**
   - 统一导入入口
   - 样式规范化
   - 文档补充

3. **测试补全**
   - 补充单元测试
   - 补充 E2E 测试
   - 添加性能基准测试

---

## 八、总结

### 当前完成度

- **数据结构支持**: 55% (5/9 类型)
- **事件流支持**: 50% (6/12 事件)
- **组件库完善度**: 70% (核心组件齐全)

### 关键差距

1. **来源引用**：搜索/RAG 场景必需
2. **文件附件**：多模态交互必需
3. **自定义数据**：高级可视化必需

### 下一步行动

1. **立即启动**：来源引用功能（P0）
2. **本周启动**：文件附件功能（P0）
3. **下周启动**：自定义数据功能（P0）

---

## 附录：AI SDK 官方文档参考

- [AI SDK UI Messages](https://sdk.vercel.ai/docs/reference/ai-sdk-ui/ui-messages)
- [AI SDK UI Parts](https://sdk.vercel.ai/docs/reference/ai-sdk-ui/ui-parts)
- [AI SDK Streaming](https://sdk.vercel.ai/docs/reference/ai-sdk-ui/streaming)
