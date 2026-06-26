/**
 * ToolCallItem 组件单元测试
 */
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import ToolCallItem from "@/ai/components/ToolCallItem.vue";
import type { ToolCallPart, ToolResultPart } from "@/ai/types";

// 使用 vi.mock 替换子组件模块（兼容 <script setup> 的本地导入）
vi.mock("@/components/ai-elements/tool", () => ({
  Tool: {
    template: '<div class="tool-stub"><slot /></div>',
  },
  ToolHeader: {
    template: '<div class="tool-header-stub" />',
    props: ["type", "state", "toolName", "title"],
  },
  ToolContent: {
    template: '<div class="tool-content-stub"><slot /></div>',
  },
  ToolInput: {
    template: '<div class="tool-input-stub" />',
    props: ["input"],
  },
  ToolOutput: {
    template: '<div class="tool-output-stub" />',
    props: ["output", "errorText"],
  },
}));

describe("ToolCallItem", () => {
  it("渲染工具调用（进行中状态）", () => {
    const toolCall: ToolCallPart = {
      type: "tool-call",
      toolCallId: "call-123",
      toolName: "search",
      args: { query: "test query" },
    };

    const wrapper = mount(ToolCallItem, {
      props: { part: toolCall },
    });

    expect(wrapper.find(".tool-stub").exists()).toBe(true);
    expect(wrapper.find(".tool-header-stub").exists()).toBe(true);
  });

  it("渲染工具结果（已完成状态）", () => {
    const toolResult: ToolResultPart = {
      type: "tool-result",
      toolCallId: "call-123",
      toolName: "search",
      result: "Search result content",
    };

    const wrapper = mount(ToolCallItem, {
      props: { part: toolResult },
    });

    expect(wrapper.find(".tool-stub").exists()).toBe(true);
    expect(wrapper.find(".tool-header-stub").exists()).toBe(true);
  });

  it("渲染工具错误状态", () => {
    const toolResult: ToolResultPart = {
      type: "tool-result",
      toolCallId: "call-123",
      toolName: "search",
      result: "Error: Something went wrong",
    };

    const wrapper = mount(ToolCallItem, {
      props: { part: toolResult },
    });

    expect(wrapper.find(".tool-stub").exists()).toBe(true);
  });

  it("渲染合并后的工具调用（包含参数和结果）", () => {
    // 模拟合并后的数据：tool-call 类型带有 _result 字段
    const mergedPart = {
      type: "tool-call" as const,
      toolCallId: "call-123",
      toolName: "search",
      args: { query: "test query" },
      _result: "Search result content",
    };

    const wrapper = mount(ToolCallItem, {
      props: { part: mergedPart },
    });

    expect(wrapper.find(".tool-stub").exists()).toBe(true);
    expect(wrapper.find(".tool-header-stub").exists()).toBe(true);
    // 合并后的数据应该同时显示输入和输出
    // 输入仅在 args 有内容时渲染
    expect(wrapper.find(".tool-input-stub").exists()).toBe(true);
    expect(wrapper.find(".tool-output-stub").exists()).toBe(true);
  });

  it("正确计算工具状态", () => {
    // 测试进行中状态
    const toolCall: ToolCallPart = {
      type: "tool-call",
      toolCallId: "call-123",
      toolName: "search",
      args: { query: "test" },
    };

    const wrapper = mount(ToolCallItem, {
      props: { part: toolCall },
    });

    // 验证组件渲染成功
    expect(wrapper.exists()).toBe(true);
  });
});
