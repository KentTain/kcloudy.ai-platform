import { describe, expect, it, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import PermissionTree from "@/iam/components/PermissionTree.vue";
import type { Permission } from "@/iam/types";

// Mock permissions data
const mockPermissions: Permission[] = [
  {
    id: "perm-1",
    code: "user:create",
    name: "创建用户",
    resource: "user",
    action: "create",
    description: "创建新用户",
    created_at: "2024-01-01",
  },
  {
    id: "perm-2",
    code: "user:read",
    name: "查看用户",
    resource: "user",
    action: "read",
    description: "查看用户列表",
    created_at: "2024-01-01",
  },
  {
    id: "perm-3",
    code: "user:update",
    name: "编辑用户",
    resource: "user",
    action: "update",
    description: "编辑用户信息",
    created_at: "2024-01-01",
  },
  {
    id: "perm-4",
    code: "role:create",
    name: "创建角色",
    resource: "role",
    action: "create",
    description: "创建新角色",
    created_at: "2024-01-01",
  },
  {
    id: "perm-5",
    code: "role:read",
    name: "查看角色",
    resource: "role",
    action: "read",
    description: "查看角色列表",
    created_at: "2024-01-01",
  },
];

// Common stubs for Element Plus components
const globalStubs = {
  "el-tree": true,
  "el-input": true,
  "el-icon": true,
  Search: true,
};

describe("PermissionTree", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("基础渲染", () => {
    it("组件存在且可挂载", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.exists()).toBe(true);
    });

    it("渲染权限树容器", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.find(".permission-tree").exists()).toBe(true);
    });
  });

  describe("按资源分组展示", () => {
    it("权限按资源分组，资源作为父节点", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证分组数据
      const treeData = wrapper.vm.treeData;
      expect(treeData).toBeDefined();
      expect(treeData.length).toBe(2); // user 和 role 两个资源组

      // 验证 user 资源组
      const userGroup = treeData.find((g: any) => g.id === "resource-user");
      expect(userGroup).toBeDefined();
      expect(userGroup.label).toBe("user");
      expect(userGroup.children.length).toBe(3);

      // 验证 role 资源组
      const roleGroup = treeData.find((g: any) => g.id === "resource-role");
      expect(roleGroup).toBeDefined();
      expect(roleGroup.label).toBe("role");
      expect(roleGroup.children.length).toBe(2);
    });

    it("权限节点包含名称、编码和描述", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      const treeData = wrapper.vm.treeData;
      const userGroup = treeData.find((g: any) => g.id === "resource-user");
      const createPerm = userGroup.children.find(
        (c: any) => c.id === "perm-1"
      );

      expect(createPerm.label).toBe("创建用户");
      expect(createPerm.code).toBe("user:create");
      expect(createPerm.description).toBe("创建新用户");
    });
  });

  describe("多选功能", () => {
    it("支持 v-model 双向绑定", async () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: ["perm-1", "perm-2"],
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证初始选中状态
      expect(wrapper.props("modelValue")).toEqual(["perm-1", "perm-2"]);
    });

    it("勾选资源节点时选中该资源下所有权限", async () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 模拟勾选资源节点
      const checkedKeys = wrapper.vm.getCheckedKeysForResource("resource-user");
      expect(checkedKeys).toEqual(["perm-1", "perm-2", "perm-3"]);
    });
  });

  describe("搜索过滤功能", () => {
    it("支持按名称搜索过滤权限", async () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 模拟搜索输入
      wrapper.vm.filterText = "创建";
      await wrapper.vm.$nextTick();

      // 等待防抖（需要额外等待或直接设置 debouncedFilterText）
      wrapper.vm.debouncedFilterText = "创建";
      await wrapper.vm.$nextTick();

      // 验证过滤后的数据
      const filteredData = wrapper.vm.filteredTreeData;
      expect(filteredData.length).toBeGreaterThan(0);

      // 验证只包含匹配的权限
      const hasCreatePermission = filteredData.some((group: any) =>
        group.children?.some(
          (child: any) => child.label?.includes("创建")
        )
      );
      expect(hasCreatePermission).toBe(true);
    });

    it("搜索无匹配结果时展示空状态", async () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 模拟搜索无匹配
      wrapper.vm.filterText = "不存在的权限";
      wrapper.vm.debouncedFilterText = "不存在的权限";
      await wrapper.vm.$nextTick();

      // 验证空状态
      const filteredData = wrapper.vm.filteredTreeData;
      expect(filteredData.length).toBe(0);
    });
  });

  describe("Props 接口", () => {
    it("接受 permissions prop", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("permissions")).toEqual(mockPermissions);
    });

    it("接受 modelValue prop", () => {
      const selectedIds = ["perm-1", "perm-4"];
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: selectedIds,
        },
        global: {
          stubs: globalStubs,
        },
      });

      expect(wrapper.props("modelValue")).toEqual(selectedIds);
    });

    it("接受 disabled prop，禁用时不可操作", () => {
      const wrapper = mount(PermissionTree, {
        props: {
          permissions: mockPermissions,
          modelValue: [],
          disabled: true,
        },
        global: {
          stubs: globalStubs,
        },
      });

      // 验证 disabled 状态传递
      expect(wrapper.props("disabled")).toBe(true);
    });
  });
});
