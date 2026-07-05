# Phase 1：AI SDK 扩展功能需求规格说明书

**版本**: 1.0
**日期**: 2026-07-05
**阶段**: Phase 1（核心功能）
**实施周期**: 2 周

---

## 一、概述

### 1.1 背景

当前 AI 对话系统基于 Vercel AI SDK 协议实现，但仅支持 55% 的数据结构类型和 50% 的事件流类型。为提供完整的 AI 对话体验，需要扩展支持更多消息部分类型和事件类型。

### 1.2 目标

Phase 1 聚焦于实现 3 个核心功能：
1. **来源引用**：支持搜索/RAG 场景的来源信息展示
2. **文件附件**：支持文件上传、存储和展示
3. **自定义数据**：支持表格和 JSON 数据的可视化

### 1.3 范围

**包含功能**：
- 来源引用（SourceUrlUIPart + SourceDocumentUIPart）
- 文件附件（FileUIPart 扩展）
- 自定义数据（DataUIPart）

**不包含功能**：
- 步骤边界（Phase 3）
- 动态工具（Phase 3）
- 消息元数据（Phase 3）
- 多模态输入（Phase 3）

---

## 二、架构设计

### 2.1 整体架构

采用**插件化处理器架构**，支持灵活扩展：

```
后端架构：
┌─────────────────────────────────────────┐
│  UIMessageChunkCallbackHandler          │
│  (统一事件处理器)                         │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  UIPartProcessorRegistry                │
│  (处理器注册中心)                         │
└─────────────┬───────────────────────────┘
              │
       ┌──────┴──────┬──────────┬──────────┐
       ▼             ▼          ▼          ▼
   ┌───────┐    ┌────────┐ ┌────────┐ ┌────────┐
   │ Source│    │  File  │ │  Data  │ │  Text  │
   │Processor│   │Processor│ │Processor│ │Processor│
   └───────┘    └────────┘ └────────┘ └────────┘

前端架构：
┌─────────────────────────────────────────┐
│  MessageContent                         │
│  (统一渲染入口)                           │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  PartRendererRegistry                   │
│  (渲染器注册中心)                         │
└─────────────┬───────────────────────────┘
              │
       ┌──────┴──────┬──────────┬──────────┐
       ▼             ▼          ▼          ▼
   ┌───────┐    ┌────────┐ ┌────────┐ ┌────────┐
   │ Source│    │  File  │ │  Data  │ │  Text  │
   │Renderer│    │Renderer│ │Renderer│ │Renderer│
   └───────┘    └────────┘ └────────┘ └────────┘
```

### 2.2 核心接口

**后端处理器接口**：
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Any

@dataclass
class ProcessContext:
    """处理器上下文"""
    tool_name: str | None = None
    tool_result: Any = None
    data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

class UIPartProcessor(ABC):
    """UI Part 处理器基类"""
    
    @abstractmethod
    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理并生成 SSE 事件
        
        Args:
            context: 处理器上下文
            
        Yields:
            SSE 事件字典
        """
        pass
    
    @classmethod
    @abstractmethod
    def supported_types(cls) -> list[str]:
        """返回此处理器支持的 Part 类型"""
        pass
```

**前端渲染器接口**：
```typescript
interface PartRendererProps {
  part: UIMessagePart
  message: UIMessage
}

interface PartRenderer {
  // 渲染器名称
  name: string
  // 支持的 Part 类型
  supportedTypes: string[]
  // 渲染函数
  render(props: PartRendererProps): VNode
}
```

---

## 三、数据结构设计

### 3.1 后端数据模型

**SourceUrlPart（来源引用 - URL）**：
```python
from dataclasses import dataclass, field
from typing import Literal, Optional, Any
import uuid

@dataclass
class SourceUrlPart:
    type: Literal["source-url"] = "source-url"
    source_id: str = field(default_factory=lambda: f"source-{uuid.uuid4().hex[:8]}")
    url: str = ""
    title: Optional[str] = None
    provider_metadata: Optional[dict[str, Any]] = None
```

**SourceDocumentPart（来源引用 - 文档）**：
```python
@dataclass
class SourceDocumentPart:
    type: Literal["source-document"] = "source-document"
    source_id: str = field(default_factory=lambda: f"source-{uuid.uuid4().hex[:8]}")
    media_type: str = ""  # MIME type
    url: str = ""
    title: Optional[str] = None
    provider_metadata: Optional[dict[str, Any]] = None
```

**FilePart（文件附件）**：
```python
@dataclass
class FilePart:
    type: Literal["file"] = "file"
    media_type: str = ""
    url: str = ""
    filename: Optional[str] = None
    size: Optional[int] = None  # 文件大小（字节）
    provider_metadata: Optional[dict[str, Any]] = None
```

**DataPart（自定义数据）**：
```python
@dataclass
class DataPart:
    type: str  # 自定义数据类型标识（"table" | "json"）
    id: str = field(default_factory=lambda: f"data-{uuid.uuid4().hex[:8]}")
    content: Any = None  # 自定义数据内容
```

### 3.2 前端类型定义

**TypeScript 类型定义**：
```typescript
// 来源引用 - URL
export interface SourceUrlPart extends UIMessagePartBase {
  type: "source-url";
  sourceId: string;
  url: string;
  title?: string;
}

// 来源引用 - 文档
export interface SourceDocumentPart extends UIMessagePartBase {
  type: "source-document";
  sourceId: string;
  mediaType: string;
  url: string;
  title?: string;
}

// 文件附件
export interface FilePart extends UIMessagePartBase {
  type: "file";
  mediaType: string;
  url: string;
  filename?: string;
  size?: number;
}

// 自定义数据
export interface DataPart extends UIMessagePartBase {
  type: string; // "table" | "json"
  id: string;
  content: unknown;
}

// 更新联合类型
export type UIMessagePart = 
  | ThinkingPart 
  | TextPart 
  | ImagePart 
  | ToolCallPart 
  | ToolResultPart
  | SourceUrlPart      // 新增
  | SourceDocumentPart // 新增
  | FilePart           // 新增
  | DataPart;          // 新增
```

---

## 四、后端处理器设计

### 4.1 SourceProcessor（来源引用处理器）

**职责**：
- 从工具调用结果中提取来源信息
- 自动识别搜索工具返回的 URL 和文档
- 生成 `source-url` 和 `source-document` SSE 事件

**实现**：
```python
from typing import AsyncGenerator
from extended.langchain.callbacks.processors.base import UIPartProcessor, ProcessContext
from ai.controllers.v1.chat.event_types import EventType

class SourceProcessor(UIPartProcessor):
    # 搜索工具名称关键字
    SEARCH_TOOL_KEYWORDS = frozenset([
        "search", "baidu", "google", "bing", 
        "duckduckgo", "websearch", "web_search"
    ])
    
    @classmethod
    def supported_types(cls) -> list[str]:
        return ["source-url", "source-document"]
    
    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理工具调用结果，提取来源信息"""
        if not context.tool_name or not context.tool_result:
            return
        
        # 1. 检查是否是搜索类工具
        if not self._is_search_tool(context.tool_name):
            return
        
        # 2. 从工具结果中提取来源
        sources = self._extract_sources(context.tool_result)
        
        # 3. 为每个来源生成事件
        for source in sources:
            if source.get("type") == "url":
                yield {
                    "type": EventType.SOURCE_URL,
                    "sourceId": source["source_id"],
                    "url": source["url"],
                    "title": source.get("title"),
                }
            elif source.get("type") == "document":
                yield {
                    "type": EventType.SOURCE_DOCUMENT,
                    "sourceId": source["source_id"],
                    "mediaType": source["media_type"],
                    "url": source["url"],
                    "title": source.get("title"),
                }
    
    def _is_search_tool(self, tool_name: str) -> bool:
        """判断是否是搜索类工具"""
        if not tool_name:
            return False
        tool_name_lower = tool_name.lower()
        return any(keyword in tool_name_lower for keyword in self.SEARCH_TOOL_KEYWORDS)
    
    def _extract_sources(self, tool_result: Any) -> list[dict]:
        """从工具结果中提取来源信息
        
        Args:
            tool_result: 工具返回结果
            
        Returns:
            来源列表，格式：
            [
                {
                    "type": "url",
                    "source_id": "source-abc123",
                    "url": "https://...",
                    "title": "标题"
                },
                {
                    "type": "document",
                    "source_id": "source-def456",
                    "media_type": "application/pdf",
                    "url": "https://...",
                    "title": "标题"
                }
            ]
        """
        sources = []
        
        # 支持多种工具结果格式
        if isinstance(tool_result, dict):
            results = tool_result.get("results", [])
            if isinstance(results, list):
                for item in results:
                    if item.get("type") in ["url", "document"]:
                        sources.append({
                            "type": item["type"],
                            "source_id": f"source-{uuid.uuid4().hex[:8]}",
                            "url": item.get("url", ""),
                            "title": item.get("title"),
                            "media_type": item.get("mediaType", ""),
                        })
        
        return sources
```

**工具结果格式约定**：
搜索工具需返回标准格式：
```python
{
    "results": [
        {
            "type": "url",  # 或 "document"
            "url": "https://...",
            "title": "标题",
            "mediaType": "text/html",  # document 类型必填
        }
    ]
}
```

---

### 4.2 FileProcessor（文件附件处理器）

**职责**：
- 接收文件上传请求
- 存储到 MinIO
- 返回文件 URL
- 记录文件访问时间（用于清理）

**实现**：
```python
from minio import Minio
from datetime import datetime
import uuid

class FileProcessor(UIPartProcessor):
    def __init__(self, minio_client: Minio):
        self.minio_client = minio_client
        self.bucket_name = "ai-chat-temp"
    
    @classmethod
    def supported_types(cls) -> list[str]:
        return ["file"]
    
    async def upload_file(
        self, 
        tenant_id: str, 
        user_id: str, 
        file: UploadFile
    ) -> FilePart:
        """上传文件到 MinIO
        
        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            file: 上传的文件
            
        Returns:
            FilePart 对象
        """
        # 1. 生成存储路径
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        file_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = f"{tenant_id}/{user_id}/{file_name}"
        
        # 2. 上传到 MinIO
        await self.minio_client.put_object(
            bucket_name=self.bucket_name,
            object_name=file_path,
            data=file.file,
            length=file.size,
            content_type=file.content_type,
        )
        
        # 3. 生成访问 URL
        url = self.minio_client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=file_path,
            expires=timedelta(days=7),  # 7 天有效期
        )
        
        # 4. 记录文件访问时间
        await self._record_file_access(tenant_id, user_id, file_path)
        
        # 5. 返回 FilePart
        return FilePart(
            media_type=file.content_type,
            url=url,
            filename=file.filename,
            size=file.size,
        )
    
    async def _record_file_access(
        self, 
        tenant_id: str, 
        user_id: str, 
        file_path: str
    ):
        """记录文件访问时间"""
        # 存储到 Redis 或数据库
        # 用于后续文件清理
        pass
```

**文件清理任务**：
```python
from datetime import datetime, timedelta

async def cleanup_old_files(db_session, minio_client: Minio):
    """清理 30 天未访问的文件"""
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # 1. 查询未访问文件
    old_files = await db_session.execute(
        "SELECT file_path FROM file_access_records "
        "WHERE last_access_time < :cutoff_date",
        {"cutoff_date": cutoff_date}
    )
    
    # 2. 删除文件
    for file in old_files:
        try:
            await minio_client.remove_object(
                bucket_name="ai-chat-temp",
                object_name=file.file_path
            )
        except Exception as e:
            logger.warning(f"Failed to delete file {file.file_path}: {e}")
    
    logger.info(f"Cleaned up {len(old_files)} old files")
```

---

### 4.3 DataProcessor（自定义数据处理器）

**职责**：
- 处理结构化数据（表格、JSON）
- 验证数据格式
- 生成 `data` SSE 事件

**实现**：
```python
class DataProcessor(UIPartProcessor):
    SUPPORTED_DATA_TYPES = frozenset(["table", "json"])
    
    @classmethod
    def supported_types(cls) -> list[str]:
        return list(cls.SUPPORTED_DATA_TYPES)
    
    async def process(self, context: ProcessContext) -> AsyncGenerator[dict, None]:
        """处理自定义数据"""
        if not context.data:
            return
        
        data_type = context.data.get("type")
        
        # 1. 验证数据类型
        if data_type not in self.SUPPORTED_DATA_TYPES:
            raise DataValidationError(data_type, f"Unsupported type: {data_type}")
        
        # 2. 验证数据格式
        if data_type == "table":
            self._validate_table_data(context.data["content"])
        elif data_type == "json":
            self._validate_json_data(context.data["content"])
        
        # 3. 生成事件
        yield {
            "type": EventType.DATA,
            "id": context.data["id"],
            "dataType": data_type,
            "content": context.data["content"],
        }
    
    def _validate_table_data(self, content: Any):
        """验证表格数据格式"""
        if not isinstance(content, dict):
            raise DataValidationError("table", "Content must be a dictionary")
        
        if "headers" not in content or "rows" not in content:
            raise DataValidationError("table", "Missing 'headers' or 'rows' field")
        
        if not isinstance(content["headers"], list):
            raise DataValidationError("table", "'headers' must be a list")
        
        if not isinstance(content["rows"], list):
            raise DataValidationError("table", "'rows' must be a list")
    
    def _validate_json_data(self, content: Any):
        """验证 JSON 数据格式"""
        try:
            json.dumps(content)
        except (TypeError, ValueError) as e:
            raise DataValidationError("json", f"Invalid JSON: {e}")
```

---

## 五、前端渲染器设计

### 5.1 SourceRenderer（来源引用渲染器）

**组件结构**：
```
SourceRenderer/
├── SourceRenderer.vue          # 主渲染器
├── SourceUrlCard.vue           # URL 来源卡片
├── SourceDocumentCard.vue      # 文档来源卡片
└── index.ts                    # 导出
```

**SourceUrlCard 组件**：
```vue
<script setup lang="ts">
import { GlobeIcon, ExternalLinkIcon } from 'lucide-vue-next'
import type { SourceUrlPart } from '@/ai/types'

interface Props {
  sourceId: string
  url: string
  title?: string
}

defineProps<Props>()
</script>

<template>
  <a
    :href="url"
    target="_blank"
    rel="noopener noreferrer"
    class="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors"
  >
    <GlobeIcon class="size-5 text-muted-foreground" />
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ title || url }}</div>
      <div class="text-xs text-muted-foreground truncate">{{ url }}</div>
    </div>
    <ExternalLinkIcon class="size-4 text-muted-foreground" />
  </a>
</template>
```

**SourceDocumentCard 组件**：
```vue
<script setup lang="ts">
import { FileIcon, EyeIcon } from 'lucide-vue-next'
import { Button } from '@/components'
import type { SourceDocumentPart } from '@/ai/types'

interface Props {
  sourceId: string
  mediaType: string
  url: string
  title?: string
}

const props = defineProps<Props>()

const handlePreview = () => {
  window.open(props.url, '_blank')
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg border p-3">
    <FileIcon class="size-5 text-muted-foreground" />
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ title || 'Document' }}</div>
      <div class="text-xs text-muted-foreground">{{ mediaType }}</div>
    </div>
    <Button variant="ghost" size="sm" @click="handlePreview">
      <EyeIcon class="size-4" />
    </Button>
  </div>
</template>
```

---

### 5.2 FileRenderer（文件附件渲染器）

**组件结构**：
```
FileRenderer/
├── FileRenderer.vue            # 主渲染器
├── FileUploadButton.vue        # 上传按钮
├── FileAttachment.vue          # 附件展示
└── index.ts
```

**FileUploadButton 组件**：
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { UploadIcon } from 'lucide-vue-next'
import { Button } from '@/components'

interface Props {
  accept?: string  // 文件类型限制
  maxSize?: number // 最大文件大小（字节）
}

const props = withDefaults(defineProps<Props>(), {
  accept: '*',
  maxSize: 10 * 1024 * 1024, // 10MB
})

const emit = defineEmits<{
  (e: 'upload', files: File[]): void
}>()

const fileInput = ref<HTMLInputElement>()

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return
  
  const validFiles = Array.from(files).filter(file => {
    if (file.size > props.maxSize) {
      console.warn(`File ${file.name} exceeds size limit`)
      return false
    }
    return true
  })
  
  emit('upload', validFiles)
}
</script>

<template>
  <Button variant="ghost" size="sm" @click="triggerUpload">
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      :accept="accept"
      multiple
      @change="handleFileSelect"
    />
    <UploadIcon class="size-4 mr-2" />
    上传文件
  </Button>
</template>
```

**FileAttachment 组件**：
```vue
<script setup lang="ts">
import { FileIcon, DownloadIcon } from 'lucide-vue-next'
import { Button } from '@/components'
import type { FilePart } from '@/ai/types'

interface Props {
  mediaType: string
  url: string
  filename?: string
  size?: number
}

const props = defineProps<Props>()

const formatSize = (bytes?: number) => {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const handleDownload = () => {
  window.open(props.url, '_blank')
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg border p-3">
    <FileIcon class="size-5 text-muted-foreground" />
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ filename }}</div>
      <div class="text-xs text-muted-foreground">{{ formatSize(size) }}</div>
    </div>
    <Button variant="ghost" size="sm" @click="handleDownload">
      <DownloadIcon class="size-4" />
    </Button>
  </div>
</template>
```

---

### 5.3 DataRenderer（自定义数据渲染器）

**组件结构**：
```
DataRenderer/
├── DataRenderer.vue            # 主渲染器（分发器）
├── TableRenderer.vue           # 表格渲染
├── JsonRenderer.vue            # JSON 渲染
└── index.ts
```

**DataRenderer 组件**：
```vue
<script setup lang="ts">
import { computed } from 'vue'
import TableRenderer from './TableRenderer.vue'
import JsonRenderer from './JsonRenderer.vue'
import type { DataPart } from '@/ai/types'

interface Props {
  type: string      // 数据类型
  id: string
  content: unknown  // 数据内容
}

const props = defineProps<Props>()

const dataType = computed(() => props.type)
</script>

<template>
  <TableRenderer v-if="dataType === 'table'" :data="content" />
  <JsonRenderer v-else-if="dataType === 'json'" :data="content" />
  <div v-else class="text-sm text-muted-foreground">
    不支持的数据类型: {{ dataType }}
  </div>
</template>
```

**TableRenderer 组件**：
```vue
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: {
    headers: string[]
    rows: any[][]
  }
}

const props = defineProps<Props>()

const headers = computed(() => props.data?.headers || [])
const rows = computed(() => props.data?.rows || [])
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm border">
      <thead>
        <tr class="border-b bg-muted/50">
          <th
            v-for="(header, index) in headers"
            :key="index"
            class="px-4 py-2 text-left font-medium"
          >
            {{ header }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in rows"
          :key="rowIndex"
          class="border-b last:border-b-0"
        >
          <td
            v-for="(cell, cellIndex) in row"
            :key="cellIndex"
            class="px-4 py-2"
          >
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

**JsonRenderer 组件**：
```vue
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: any
}

const props = defineProps<Props>()

const formattedJson = computed(() => {
  return JSON.stringify(props.data, null, 2)
})
</script>

<template>
  <pre class="rounded-lg bg-muted p-4 text-xs overflow-x-auto"><code>{{ formattedJson }}</code></pre>
</template>
```

---

## 六、SSE 事件类型扩展

### 6.1 新增事件类型

在 `ai/controllers/v1/chat/event_types.py` 中添加：

```python
from enum import Enum

class EventType(str, Enum):
    # 现有事件
    START = "start"
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"
    
    # 思考过程事件（已实现）
    THINKING_START = "thinking-start"
    THINKING_DELTA = "thinking-delta"
    THINKING_END = "thinking-end"
    
    # 工具调用事件（已实现）
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"
    
    # 新增：来源引用事件
    SOURCE_URL = "source-url"
    SOURCE_DOCUMENT = "source-document"
    
    # 新增：文件事件
    FILE_UPLOAD_START = "file-upload-start"
    FILE_UPLOAD_END = "file-upload-end"
    
    # 新增：数据事件
    DATA = "data"
    
    # 结束事件
    FINISH = "finish"
    ERROR = "error"
    WARNING = "warning"  # 新增
```

### 6.2 事件格式定义

**来源引用事件**：
```python
# SOURCE_URL
{
    "type": "source-url",
    "sourceId": "source-abc123",
    "url": "https://example.com",
    "title": "Example Page",
}

# SOURCE_DOCUMENT
{
    "type": "source-document",
    "sourceId": "source-def456",
    "mediaType": "application/pdf",
    "url": "https://minio.example.com/ai-chat-temp/...",
    "title": "Document Title",
}
```

**文件上传事件**：
```python
# FILE_UPLOAD_START
{
    "type": "file-upload-start",
    "uploadId": "upload-xyz789",
    "filename": "document.pdf",
    "size": 1048576,
}

# FILE_UPLOAD_END
{
    "type": "file-upload-end",
    "uploadId": "upload-xyz789",
    "file": {
        "mediaType": "application/pdf",
        "url": "https://minio.example.com/ai-chat-temp/...",
        "filename": "document.pdf",
        "size": 1048576,
    },
}
```

**数据事件**：
```python
# DATA
{
    "type": "data",
    "id": "data-ghi012",
    "dataType": "table",  # 或 "json"
    "content": {
        "headers": ["Name", "Age"],
        "rows": [["Alice", 25], ["Bob", 30]]
    },
}
```

### 6.3 SSE Generator 更新

在 `llm.py` 的 `_sse_generator()` 中处理新事件：

```python
async def _sse_generator(event_queue, message_id, max_timeout=300):
    # ... 现有代码 ...
    
    while True:
        event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
        event_type = event.get("type")
        
        # 处理新事件
        if event_type in [
            EventType.SOURCE_URL,
            EventType.SOURCE_DOCUMENT,
            EventType.FILE_UPLOAD_START,
            EventType.FILE_UPLOAD_END,
            EventType.DATA,
            EventType.WARNING,
        ]:
            yield _format_sse_line(event)
        # ... 其他事件处理 ...
```

---

## 七、API 接口设计

### 7.1 文件上传接口

**端点**：`POST /ai/console/v1/files/upload`

**请求**：
- Content-Type: `multipart/form-data`
- 参数：
  - `file`: UploadFile（必需）
  - `conversation_id`: str（可选，用于关联会话）

**响应**：
```python
{
    "code": 200,
    "data": {
        "fileId": "file-abc123",
        "mediaType": "application/pdf",
        "url": "https://minio.example.com/ai-chat-temp/tenant1/user1/abc123_document.pdf",
        "filename": "document.pdf",
        "size": 1048576,
    }
}
```

**实现**：
```python
from fastapi import File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """文件上传接口"""
    tenant_id = get_tenant_id()
    user_id = get_user_id()
    
    # 1. 验证文件大小（最大 10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 2. 获取 FileProcessor
    file_processor = get_file_processor()
    
    # 3. 上传文件
    file_part = await file_processor.upload_file(tenant_id, user_id, file)
    
    # 4. 返回结果
    return ORJSONResponse(content={
        "code": 200,
        "data": {
            "fileId": file_part.file_id,
            "mediaType": file_part.media_type,
            "url": file_part.url,
            "filename": file_part.filename,
            "size": file_part.size,
        }
    })
```

---

### 7.2 文件清理接口（管理端）

**端点**：`POST /ai/admin/v1/files/cleanup`

**请求**：
```python
{
    "days": 30,  # 清理多少天前的文件
    "dryRun": true  # 是否只预览不执行
}
```

**响应**：
```python
{
    "code": 200,
    "data": {
        "totalFiles": 150,
        "totalSize": 524288000,  # 字节
        "files": [
            "tenant1/user1/abc123_old.pdf",
            "tenant2/user2/def456_old.docx",
        ]
    }
}
```

---

### 7.3 扩展现有对话接口

**端点**：`POST /ai/console/v1/chat-messages`

**请求扩展**：
```python
class AIChatRequest(BaseModel):
    id: Optional[str] = None
    messages: list[UIMessage]
    trigger: Optional[str] = "submit-message"
    messageId: Optional[str] = None
    body: Optional[ModelBody] = None
    
    # 新增：文件上传支持
    files: Optional[list[FilePart]] = None  # 已上传的文件列表
```

---

### 7.4 来源引用查询接口

**端点**：`GET /ai/console/v1/sources/{source_id}`

**响应**：
```python
{
    "code": 200,
    "data": {
        "sourceId": "source-abc123",
        "type": "url",  # 或 "document"
        "url": "https://example.com",
        "title": "Example Page",
        "accessCount": 42,  # 访问次数
        "lastAccessTime": "2026-07-05T10:00:00Z",
    }
}
```

---

## 八、错误处理设计

### 8.1 错误类型定义

```python
# ai/schemas/errors.py

class FileUploadError(Exception):
    """文件上传错误"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class UnsupportedMediaTypeError(FileUploadError):
    """不支持的媒体类型"""
    def __init__(self, media_type: str):
        super().__init__(
            f"Unsupported media type: {media_type}",
            "UNSUPPORTED_MEDIA_TYPE"
        )

class FileSizeExceededError(FileUploadError):
    """文件大小超限"""
    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"File size {size} exceeds limit {max_size}",
            "FILE_SIZE_EXCEEDED"
        )

class SourceExtractionError(Exception):
    """来源提取错误"""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Failed to extract sources from {tool_name}: {reason}")

class DataValidationError(Exception):
    """数据验证错误"""
    def __init__(self, data_type: str, reason: str):
        self.data_type = data_type
        self.reason = reason
        super().__init__(f"Invalid {data_type} data: {reason}")
```

### 8.2 错误处理策略

**文件上传错误处理**：
```python
@router.post("/files/upload")
async def upload_file(file: UploadFile, ...):
    try:
        # 验证文件大小
        MAX_FILE_SIZE = 10 * 1024 * 1024
        if file.size > MAX_FILE_SIZE:
            raise FileSizeExceededError(file.size, MAX_FILE_SIZE)
        
        # 处理上传
        file_part = await file_processor.upload_file(...)
        
    except FileUploadError as e:
        logger.warning(f"File upload failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except Exception as e:
        logger.exception("Unexpected error during file upload")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**来源提取错误处理**：
```python
class SourceProcessor(UIPartProcessor):
    async def process(self, context: ProcessContext):
        try:
            sources = self._extract_sources(context.tool_result)
            for source in sources:
                yield self._create_source_event(source)
        
        except SourceExtractionError as e:
            logger.warning(f"Source extraction failed: {e}")
            # 不中断流程，静默失败
            yield {
                "type": EventType.WARNING,
                "message": f"Failed to extract sources: {e.reason}",
            }
```

### 8.3 前端错误展示

**错误边界组件**：
```vue
<script setup lang="ts">
import { AlertCircleIcon } from 'lucide-vue-next'

interface Props {
  error?: {
    code: string
    message: string
  }
}

defineProps<Props>()
</script>

<template>
  <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3">
    <div class="flex items-center gap-2 text-red-600">
      <AlertCircleIcon class="size-4" />
      <span class="text-sm font-medium">{{ error.message }}</span>
    </div>
  </div>
  
  <slot v-else />
</template>
```

---

## 九、测试策略设计

### 9.1 单元测试

**后端单元测试**：

文件结构：
```
tests/ai/unit/
├── processors/
│   ├── test_source_processor.py
│   ├── test_file_processor.py
│   └── test_data_processor.py
└── test_file_upload.py
```

**SourceProcessor 测试**：
```python
@pytest.mark.asyncio
class TestSourceProcessor:
    async def test_extract_url_sources_from_search_tool(self):
        """测试从搜索工具提取 URL 来源"""
        processor = SourceProcessor()
        context = ProcessContext(
            tool_name="google_search",
            tool_result={
                "results": [
                    {
                        "type": "url",
                        "url": "https://example.com",
                        "title": "Example",
                    }
                ]
            }
        )
        
        events = []
        async for event in processor.process(context):
            events.append(event)
        
        assert len(events) == 1
        assert events[0]["type"] == "source-url"
        assert events[0]["url"] == "https://example.com"
    
    async def test_extract_document_sources(self):
        """测试提取文档来源"""
        # ... 测试代码 ...
    
    async def test_non_search_tool_ignored(self):
        """测试非搜索工具被忽略"""
        processor = SourceProcessor()
        context = ProcessContext(
            tool_name="calculator",
            tool_result={"result": 42}
        )
        
        events = []
        async for event in processor.process(context):
            events.append(event)
        
        assert len(events) == 0
```

**前端单元测试**：

文件结构：
```
web/vue/tests/ai/unit/components/
├── SourceRenderer.test.ts
├── FileRenderer.test.ts
└── DataRenderer.test.ts
```

**SourceRenderer 测试**：
```typescript
describe('SourceRenderer', () => {
  it('renders source URL card with correct link', () => {
    const source: SourceUrlPart = {
      type: 'source-url',
      sourceId: 'source-123',
      url: 'https://example.com',
      title: 'Example Site',
    }
    
    const wrapper = mount(SourceRenderer, {
      props: { part: source }
    })
    
    expect(wrapper.find('a').attributes('href')).toBe('https://example.com')
    expect(wrapper.text()).toContain('Example Site')
  })
})
```

---

### 9.2 集成测试

文件结构：
```
tests/ai/integration/
├── test_file_upload_flow.py
├── test_source_extraction_flow.py
└── test_data_processing_flow.py
```

**完整流程测试**：
```python
@pytest.mark.asyncio
class TestFileUploadFlow:
    async def test_complete_file_upload_flow(self, test_client, mock_minio):
        """测试完整的文件上传流程"""
        # 1. 上传文件
        with open("test.pdf", "rb") as f:
            response = await test_client.post(
                "/ai/console/v1/files/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        
        assert response.status_code == 200
        file_data = response.json()["data"]
        
        # 2. 发送带文件的消息
        chat_response = await test_client.post(
            "/ai/console/v1/chat-messages",
            json={
                "messages": [
                    {
                        "id": "msg-123",
                        "role": "user",
                        "parts": [
                            {"type": "text", "text": "分析这个文件"},
                            file_data,
                        ]
                    }
                ]
            }
        )
        
        assert chat_response.status_code == 200
```

---

### 9.3 E2E 测试

文件结构：
```
web/vue/tests/ai/e2e/
├── file-upload.spec.ts
├── source-citation.spec.ts
└── data-visualization.spec.ts
```

**文件上传 E2E 测试**：
```typescript
test('user can upload and send file in chat', async ({ page }) => {
  // 1. 打开对话页面
  await page.goto('/ai')
  
  // 2. 上传文件
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('test-assets/document.pdf')
  
  // 3. 验证文件显示
  await expect(page.locator('[data-testid="file-attachment"]')).toBeVisible()
  
  // 4. 发送消息
  await page.fill('textarea', '分析这个文件')
  await page.click('button[type="submit"]')
  
  // 5. 等待响应
  await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible()
})
```

---

## 十、实施计划

### 10.1 时间线

**第 1 周（后端核心）**：
- Day 1-2: 实现处理器架构和注册中心
- Day 3-4: 实现 SourceProcessor + FileProcessor
- Day 5: 实现 DataProcessor + SSE 事件扩展

**第 2 周（前端 + 集成）**：
- Day 1-2: 实现渲染器架构和注册中心
- Day 3-4: 实现 SourceRenderer + FileRenderer + DataRenderer
- Day 5: 集成测试 + E2E 测试

### 10.2 依赖关系

```
后端处理器 → SSE 事件扩展 → 前端渲染器 → UI 集成
     ↓
  单元测试
     ↓
  集成测试
     ↓
   E2E 测试
```

### 10.3 验收标准

**功能验收**：
- ✅ 文件上传功能正常，支持 10MB 以内文件
- ✅ 文件自动存储到 MinIO 指定目录
- ✅ 搜索工具自动提取来源引用
- ✅ 表格和 JSON 数据正确渲染
- ✅ SSE 事件正确发送和接收

**质量验收**：
- ✅ 后端单元测试覆盖率 ≥ 85%
- ✅ 前端单元测试覆盖率 ≥ 75%
- ✅ 集成测试全部通过
- ✅ E2E 测试全部通过

**性能验收**：
- ✅ 文件上传响应时间 < 2s（10MB 文件）
- ✅ 来源提取处理时间 < 100ms
- ✅ 数据渲染响应时间 < 500ms

---

## 十一、风险评估

### 11.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| MinIO 存储失败 | 高 | 低 | 实现重试机制和错误处理 |
| 文件清理任务失败 | 中 | 低 | 监控告警 + 手动触发接口 |
| 大文件上传超时 | 中 | 中 | 限制文件大小 + 分片上传（Phase 2） |
| 来源提取格式不兼容 | 低 | 中 | 支持多种格式 + 文档说明 |

### 11.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 存储成本过高 | 高 | 中 | 实施文件清理策略 + 配额限制 |
| 用户上传恶意文件 | 高 | 中 | 文件类型验证 + 安全扫描（Phase 2） |
| 敏感信息泄露 | 高 | 低 | 文件访问权限控制 |

---

## 十二、后续规划

### Phase 2（1 周）：体验优化

- 文件预览增强（PDF、图片、视频）
- 来源引用点击跳转优化
- 数据可视化交互增强
- 大文件分片上传

### Phase 3（1 周）：高级功能

- 步骤边界（StepStartUIPart）
- 动态工具（DynamicToolUIPart）
- 消息元数据扩展
- 多模态输入支持

---

## 附录

### A. 文件类型支持清单

| 文件类型 | MIME Type | 支持状态 |
|---------|-----------|---------|
| PDF | application/pdf | ✅ 支持 |
| Word | application/msword | ✅ 支持 |
| Excel | application/vnd.ms-excel | ✅ 支持 |
| 图片 | image/* | ✅ 支持 |
| 视频 | video/* | ⚠️ 部分支持（Phase 2） |
| 音频 | audio/* | ⚠️ 部分支持（Phase 2） |

### B. 数据类型支持清单

| 数据类型 | 格式说明 | 支持状态 |
|---------|---------|---------|
| table | `{headers: string[], rows: any[][]}` | ✅ 支持 |
| json | 任意 JSON 对象 | ✅ 支持 |
| chart | 图表数据结构 | ⚠️ Phase 2 |
| geo | 地理位置数据 | ⚠️ Phase 3 |

### C. 参考文档

- [AI SDK UI Messages](https://sdk.vercel.ai/docs/reference/ai-sdk-ui/ui-messages)
- [AI SDK UI Parts](https://sdk.vercel.ai/docs/reference/ai-sdk-ui/ui-parts)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)
