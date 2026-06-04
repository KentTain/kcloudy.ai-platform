<script setup lang="ts">
/**
 * ToolCallItem 组件
 *
 * 渲染单个工具调用，展示工具名称、参数和结果
 */
import { computed } from "vue";
import { Tool, ToolHeader, ToolContent, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import type { ToolCallPart, ToolResultPart } from "@/ai/types";

// 扩展类型，支持合并后的数据
interface MergedToolPart extends ToolCallPart {
  _result?: unknown;
}

interface Props {
  /** 工具调用部分 */
  part: ToolCallPart | ToolResultPart | MergedToolPart;
  /** 对应的工具结果（如果有） */
  result?: unknown;
}

const props = defineProps<Props>();

// 判断是否是合并后的数据
const isMergedPart = (part: Props["part"]): part is MergedToolPart => {
  return part.type === "tool-call" && "_result" in part;
};

// 计算工具状态
const toolState = computed(() => {
  // 如果是合并后的数据，有 result
  if (isMergedPart(props.part)) {
    const result = props.part._result;
    if (typeof result === "string" && result.startsWith("Error:")) {
      return "output-error";
    }
    return "output-available";
  }

  if (props.part.type === "tool-result") {
    // 如果有结果，检查是否是错误
    const result = props.part.result;
    if (typeof result === "string" && result.startsWith("Error:")) {
      return "output-error";
    }
    return "output-available";
  }
  // tool-call 表示正在执行
  return "input-available";
});

// 获取工具名称
const toolName = computed(() => props.part.toolName);

// 获取工具调用 ID
const toolCallId = computed(() => props.part.toolCallId);

// 获取输入参数
const input = computed(() => {
  if (props.part.type === "tool-call") {
    return props.part.args;
  }
  return {};
});

// 获取输出结果
const output = computed(() => {
  // 合并后的数据
  if (isMergedPart(props.part)) {
    return props.part._result;
  }
  if (props.part.type === "tool-result") {
    return props.part.result;
  }
  return undefined;
});

// 获取错误信息
const errorText = computed(() => {
  // 合并后的数据
  if (isMergedPart(props.part)) {
    const result = props.part._result;
    if (typeof result === "string" && result.startsWith("Error:")) {
      return result;
    }
  }
  if (props.part.type === "tool-result") {
    const result = props.part.result;
    if (typeof result === "string" && result.startsWith("Error:")) {
      return result;
    }
  }
  return undefined;
});

// 工具名称映射（用于友好显示）
const toolNameMap: Record<string, string> = {
  search: "搜索",
  web_search: "网络搜索",
  baidu_search: "百度搜索",
  google_search: "Google 搜索",
};

// 显示名称
const displayName = computed(() => {
  return toolNameMap[toolName.value] || toolName.value;
});
</script>

<template>
  <Tool :key="toolCallId" default-open>
    <ToolHeader
      type="dynamic-tool"
      :state="toolState"
      :tool-name="toolName"
      :title="displayName"
    />
    <ToolContent>
      <!-- 显示工具参数 -->
      <ToolInput v-if="input && Object.keys(input).length > 0" :input="input" />
      <!-- 显示工具结果 -->
      <ToolOutput
        v-if="output !== undefined || errorText"
        :output="output"
        :error-text="errorText"
      />
    </ToolContent>
  </Tool>
</template>
