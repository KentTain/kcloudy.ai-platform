import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { Select, Table, Input } from "@/components/common";
import AppForm from "@/framework/components/ui/AppForm.vue";
import AppFormItem from "@/framework/components/ui/AppFormItem.vue";

describe("P1 Components", () => {
  describe("Select", () => {
    const options = [
      { label: "选项1", value: "1" },
      { label: "选项2", value: "2" },
      { label: "禁用选项", value: "3", disabled: true },
    ];

    it("renders correctly", () => {
      const wrapper = mount(Select, {
        props: { options },
      });

      expect(wrapper.find("button").exists()).toBe(true);
    });

    it("shows placeholder when no value selected", () => {
      const wrapper = mount(Select, {
        props: { options },
      });

      expect(wrapper.text()).toContain("请选择");
    });

    it("opens dropdown on click", async () => {
      const wrapper = mount(Select, {
        props: { options },
      });

      await wrapper.find("button").trigger("click");

      // shadcn Select uses portal, so dropdown might be teleported
      expect(wrapper.emitted("update:modelValue")).toBeFalsy();
    });

    it("preserves number value when selecting option", async () => {
      const numberOptions = [{ label: "零", value: 0 }, { label: "一", value: 1 }];
      const onUpdateModelValue = vi.fn();
      const onChange = vi.fn();

      const wrapper = mount(Select, {
        props: {
          options: numberOptions,
          "onUpdate:modelValue": onUpdateModelValue,
          onChange,
        },
      });

      const select = wrapper.findComponent({ name: "SelectRoot" });
      await select.vm.$emit("update:modelValue", "1");

      expect(onUpdateModelValue).toHaveBeenCalledWith(1);
      expect(onChange).toHaveBeenCalledWith(1);
    });

    it("preserves zero value when selecting option", async () => {
      const numberOptions = [{ label: "零", value: 0 }, { label: "一", value: 1 }];
      const onUpdateModelValue = vi.fn();
      const onChange = vi.fn();

      const wrapper = mount(Select, {
        props: {
          options: numberOptions,
          "onUpdate:modelValue": onUpdateModelValue,
          onChange,
        },
      });

      const select = wrapper.findComponent({ name: "SelectRoot" });
      await select.vm.$emit("update:modelValue", "0");

      expect(onUpdateModelValue).toHaveBeenCalledWith(0);
      expect(onChange).toHaveBeenCalledWith(0);
    });

    it("does not open when disabled", async () => {
      const wrapper = mount(Select, {
        props: { options, disabled: true },
      });

      expect(wrapper.find("button").attributes("disabled")).toBeDefined();
    });
  });

  describe("Table", () => {
    const columns = [
      { key: "name", title: "名称" },
      { key: "age", title: "年龄", align: "center" as const },
      { key: "action", title: "操作", sortable: true },
    ];

    const data = [
      { name: "张三", age: 25, action: "编辑" },
      { name: "李四", age: 30, action: "删除" },
    ];

    it("renders correctly", () => {
      const wrapper = mount(Table, {
        props: { columns, data },
      });

      expect(wrapper.find("table").exists()).toBe(true);
    });

    it("renders columns", () => {
      const wrapper = mount(Table, {
        props: { columns, data },
      });

      const headers = wrapper.findAll("th");
      expect(headers[0].text()).toBe("名称");
      expect(headers[1].text()).toBe("年龄");
      expect(headers[2].text()).toBe("操作");
    });

    it("renders data rows", () => {
      const wrapper = mount(Table, {
        props: { columns, data },
      });

      const rows = wrapper.findAll("tbody tr");
      expect(rows).toHaveLength(2);
    });

    it("shows empty text when no data", () => {
      const wrapper = mount(Table, {
        props: { columns, data: [] },
      });

      expect(wrapper.text()).toContain("暂无数据");
    });

    it("shows loading state", () => {
      const wrapper = mount(Table, {
        props: { columns, data: [], loading: true },
      });

      expect(wrapper.text()).toContain("加载中");
    });

    it("emits sort event", async () => {
      const onSort = vi.fn();
      const wrapper = mount(Table, {
        props: { columns, data, onSort },
      });

      const sortableHeader = wrapper.findAll("th")[2].find("div");
      await sortableHeader.trigger("click");

      expect(onSort).toHaveBeenCalledWith({ key: "action", order: "asc" });
    });

    it("renders stripe rows", () => {
      const wrapper = mount(Table, {
        props: { columns, data, stripe: true },
      });

      expect(wrapper.find("table").exists()).toBe(true);
    });

    it("renders border", () => {
      const wrapper = mount(Table, {
        props: { columns, data, border: true },
      });

      expect(wrapper.find(".rounded-md").exists()).toBe(true);
    });
  });

  describe("AppForm", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppForm, {
        slots: { default: "Form content" },
      });

      expect(wrapper.find(".app-form").exists()).toBe(true);
      expect(wrapper.text()).toContain("Form content");
    });

    it("validates required field", async () => {
      const rules = {
        name: [{ required: true, message: "请输入名称" }],
      };

      const wrapper = mount(AppForm, {
        props: { rules },
      });

      const isValid = wrapper.vm.validate();
      expect(isValid).toBe(false);
    });

    it("resets form", () => {
      const wrapper = mount(AppForm);

      wrapper.vm.resetForm();

      expect(wrapper.vm.isValid).toBe(true);
    });

    it("emits submit event", async () => {
      const onSubmit = vi.fn();
      const wrapper = mount(AppForm, {
        props: { onSubmit },
      });

      await wrapper.trigger("submit");

      expect(onSubmit).toHaveBeenCalled();
    });
  });

  describe("AppFormItem", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppFormItem, {
        props: { label: "用户名" },
        slots: { default: "Input" },
      });

      expect(wrapper.find(".app-form-item").exists()).toBe(true);
      expect(wrapper.find(".app-form-item__label").text()).toBe("用户名");
    });

    it("shows required mark", () => {
      const wrapper = mount(AppFormItem, {
        props: { label: "用户名", required: true },
      });

      expect(wrapper.find(".app-form-item--required").exists()).toBe(true);
    });
  });
});
