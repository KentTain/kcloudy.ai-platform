import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import AppSelect from "@/framework/components/ui/AppSelect.vue";
import AppTable from "@/framework/components/ui/AppTable.vue";
import AppForm from "@/framework/components/ui/AppForm.vue";
import AppFormItem from "@/framework/components/ui/AppFormItem.vue";
import AppInput from "@/framework/components/ui/AppInput.vue";

describe("P1 Components", () => {
  describe("AppSelect", () => {
    const options = [
      { label: "选项1", value: "1" },
      { label: "选项2", value: "2" },
      { label: "禁用选项", value: "3", disabled: true },
    ];

    it("renders correctly", () => {
      const wrapper = mount(AppSelect, {
        props: { options },
      });

      expect(wrapper.find(".app-select").exists()).toBe(true);
      expect(wrapper.find(".app-select__placeholder").text()).toBe("请选择");
    });

    it("shows selected value", () => {
      const wrapper = mount(AppSelect, {
        props: { options, modelValue: "1" },
      });

      expect(wrapper.find(".app-select__value").text()).toBe("选项1");
    });

    it("opens dropdown on click", async () => {
      const wrapper = mount(AppSelect, {
        props: { options },
      });

      await wrapper.find(".app-select__trigger").trigger("click");

      expect(wrapper.find(".app-select__dropdown").exists()).toBe(true);
    });

    it("selects option", async () => {
      const wrapper = mount(AppSelect, {
        props: { options },
      });

      await wrapper.find(".app-select__trigger").trigger("click");
      await wrapper.findAll(".app-select__option")[0].trigger("click");

      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
      expect(wrapper.emitted("update:modelValue")![0]).toEqual(["1"]);
    });

    it("clears value", async () => {
      const wrapper = mount(AppSelect, {
        props: { options, modelValue: "1", clearable: true },
      });

      await wrapper.find(".app-select__clear").trigger("click");

      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
      expect(wrapper.emitted("update:modelValue")![0]).toEqual([null]);
    });

    it("does not open when disabled", async () => {
      const wrapper = mount(AppSelect, {
        props: { options, disabled: true },
      });

      await wrapper.find(".app-select__trigger").trigger("click");

      expect(wrapper.find(".app-select__dropdown").exists()).toBe(false);
    });
  });

  describe("AppTable", () => {
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
      const wrapper = mount(AppTable, {
        props: { columns, data },
      });

      expect(wrapper.find(".app-table").exists()).toBe(true);
    });

    it("renders columns", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data },
      });

      const headers = wrapper.findAll(".app-table__header span");
      expect(headers[0].text()).toBe("名称");
      expect(headers[1].text()).toBe("年龄");
      expect(headers[2].text()).toBe("操作");
    });

    it("renders data rows", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data },
      });

      const rows = wrapper.findAll(".app-table__row");
      expect(rows).toHaveLength(2);
    });

    it("shows empty text when no data", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data: [] },
      });

      expect(wrapper.find(".app-table__empty").text()).toBe("暂无数据");
    });

    it("shows loading state", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data: [], loading: true },
      });

      expect(wrapper.find(".app-table__loading").exists()).toBe(true);
    });

    it("emits sort event", async () => {
      const wrapper = mount(AppTable, {
        props: { columns, data },
      });

      const sortableHeader = wrapper.findAll(".app-table__header--sortable")[0];
      await sortableHeader.trigger("click");

      expect(wrapper.emitted("sort")).toBeTruthy();
    });

    it("renders stripe rows", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data, stripe: true },
      });

      expect(wrapper.find(".app-table--stripe").exists()).toBe(true);
    });

    it("renders border", () => {
      const wrapper = mount(AppTable, {
        props: { columns, data, border: true },
      });

      expect(wrapper.find(".app-table--border").exists()).toBe(true);
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
      const wrapper = mount(AppForm);

      await wrapper.trigger("submit");

      expect(wrapper.emitted("submit")).toBeTruthy();
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
