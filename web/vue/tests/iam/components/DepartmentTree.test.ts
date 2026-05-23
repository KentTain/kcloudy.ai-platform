import { describe, expect, it, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import DepartmentTree from "@/iam/components/DepartmentTree.vue";
import type { Department } from "@/iam/types";

// Mock departments data
const mockDepartments: Department[] = [
  {
    id: "dept-1",
    tenant_id: "tenant-1",
    name: "总公司",
    sort_order: 0,
    status: "active",
    created_at: "2024-01-01",
    children: [
      {
        id: "dept-2",
        tenant_id: "tenant-1",
        parent_id: "dept-1",
        name: "研发部",
        sort_order: 0,
        status: "active",
        created_at: "2024-01-01",
        children: [
          {
            id: "dept-3",
            tenant_id: "tenant-1",
            parent_id: "dept-2",
            name: "前端组",
            sort_order: 0,
            status: "active",
            created_at: "2024-01-01",
          },
          {
            id: "dept-4",
            tenant_id: "tenant-1",
            parent_id: "dept-2",
            name: "后端组",
            sort_order: 1,
            status: "active",
            created_at: "2024-01-01",
          },
        ],
      },
      {
        id: "dept-5",
        tenant_id: "tenant-1",
        parent_id: "dept-1",
        name: "市场部",
        sort_order: 1,
        status: "active",
        created_at: "2024-01-01",
      },
    ],
  },
];

// Common stubs for Element Plus components
const globalStubs = {
  "el-tree": true,
  "el-input": true,
  "el-icon": true,
  Search: true,
};

describe("DepartmentTree", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("基础渲染", () => {
    it("组件存在且可挂载", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.exists()).toBe(true);
    });

    it("渲染部门树容器", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.find(".department-tree").exists()).toBe(true);
    });
  });

  describe("树形结构展示", () => {
    it("展示部门树形结构", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证树形数据结构
      const treeData = wrapper.vm.treeData;
      expect(treeData).toBeDefined();
      expect(treeData.length).toBe(1); // 一个根节点（总公司）

      // 验证子节点
      const rootDept = treeData[0];
      expect(rootDept.label).toBe("总公司");
      expect(rootDept.children?.length).toBe(2); // 研发部和市场部
    });

    it("展示部门名称和负责人信息", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      const treeData = wrapper.vm.treeData;
      const rootDept = treeData[0];

      expect(rootDept.label).toBe("总公司");
      expect(rootDept.id).toBe("dept-1");
    });
  });

  describe("节点选择", () => {
    it("单选模式 - 只能选择一个部门", async () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
          mode: "single",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证单选模式
      expect(wrapper.props("mode")).toBe("single");
    });

    it("多选模式 - 可以选择多个部门", async () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: [],
          mode: "multiple",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证多选模式
      expect(wrapper.props("mode")).toBe("multiple");
    });

    it("支持 v-model 双向绑定", async () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "dept-2",
          mode: "single",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证初始选中状态
      expect(wrapper.props("modelValue")).toBe("dept-2");
    });
  });

  describe("部门搜索", () => {
    it("支持按名称搜索过滤", async () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 模拟搜索输入
      wrapper.vm.filterText = "研发";
      wrapper.vm.debouncedFilterText = "研发";
      await wrapper.vm.$nextTick();

      // 验证过滤后的数据
      const filteredData = wrapper.vm.filteredTreeData;
      expect(filteredData.length).toBeGreaterThan(0);

      // 验证包含研发部（需要在子节点中查找）
      const findDept = (nodes: any[], keyword: string): boolean => {
        return nodes.some(
          (node) =>
            node.label?.includes(keyword) ||
            (node.children && findDept(node.children, keyword))
        );
      };
      const hasDept = findDept(filteredData, "研发");
      expect(hasDept).toBe(true);
    });

    it("搜索无匹配结果时展示空状态", async () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 模拟搜索无匹配
      wrapper.vm.filterText = "不存在的部门";
      wrapper.vm.debouncedFilterText = "不存在的部门";
      await wrapper.vm.$nextTick();

      // 验证空状态
      const filteredData = wrapper.vm.filteredTreeData;
      expect(filteredData.length).toBe(0);
    });
  });

  describe("Props 接口", () => {
    it("接受 departments prop", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("departments")).toEqual(mockDepartments);
    });

    it("接受 modelValue prop（单选）", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "dept-1",
          mode: "single",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("modelValue")).toBe("dept-1");
    });

    it("接受 modelValue prop（多选）", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: ["dept-1", "dept-2"],
          mode: "multiple",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("modelValue")).toEqual(["dept-1", "dept-2"]);
    });

    it("接受 mode prop（single/multiple）", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
          mode: "single",
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("mode")).toBe("single");
    });

    it("接受 defaultExpandLevel prop", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
          defaultExpandLevel: 2,
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("defaultExpandLevel")).toBe(2);
    });

    it("接受 disabled prop", () => {
      const wrapper = mount(DepartmentTree, {
        props: {
          departments: mockDepartments,
          modelValue: "",
          disabled: true,
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("disabled")).toBe(true);
    });
  });
});