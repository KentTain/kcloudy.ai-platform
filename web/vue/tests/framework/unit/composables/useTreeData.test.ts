/**
 * useTreeData 组合式函数单元测试
 *
 * 覆盖场景：
 * - 数据转换（默认/自定义字段映射、响应式数据源）
 * - 选中状态管理（单选/多选、modelValue 双向绑定、获取选中节点）
 * - 搜索过滤（关键词过滤、清空搜索、搜索无结果）
 * - 节点查找（按 ID 查找、查找不存在节点、获取祖先节点）
 * - 选择操作方法（toggleSelect、clearSelection）
 * - 展开状态（toggleExpand、expandToLevel、defaultExpandLevel）
 */
import { beforeEach, describe, expect, it } from "vitest";
import { nextTick, ref } from "vue";
import { useTreeData } from "@/framework/composables/useTreeData";

// ============================================================================
// 测试数据
// ============================================================================

/** 默认字段结构的测试数据 */
const defaultData = [
  {
    id: "1",
    name: "根节点 1",
    children: [
      { id: "1-1", name: "子节点 1-1" },
      {
        id: "1-2",
        name: "子节点 1-2",
        children: [
          { id: "1-2-1", name: "孙节点 1-2-1" },
        ],
      },
    ],
  },
  { id: "2", name: "根节点 2" },
  {
    id: "3",
    name: "根节点 3",
    children: [
      { id: "3-1", name: "子节点 3-1" },
    ],
  },
];

/** 自定义字段结构的测试数据 */
const customFieldData = [
  {
    code: "c1",
    title: "自定义节点 1",
    items: [
      { code: "c1-1", title: "自定义子节点 1-1" },
    ],
  },
  { code: "c2", title: "自定义节点 2" },
];

/** 带额外属性的测试数据 */
const dataWithExtras = [
  {
    id: "e1",
    name: "额外属性节点",
    disabled: true,
    isLeaf: false,
    extraField: "extra-value",
  },
];

// ============================================================================
// 测试套件
// ============================================================================

describe("useTreeData", () => {
  // ==========================================================================
  // 数据转换能力
  // ==========================================================================
  describe("数据转换", () => {
    it("默认字段映射 - 使用 id/name/children 字段", () => {
      const { treeData } = useTreeData({ source: defaultData });

      expect(treeData.value).toHaveLength(3);
      expect(treeData.value[0].id).toBe("1");
      expect(treeData.value[0].name).toBe("根节点 1");
      expect(treeData.value[0].children).toBeDefined();
      expect(treeData.value[0].children).toHaveLength(2);
    });

    it("自定义字段映射 - 使用 code/title/items 字段", () => {
      const { treeData } = useTreeData({
        source: customFieldData,
        fieldMapping: { id: "code", name: "title", children: "items" },
      });

      expect(treeData.value).toHaveLength(2);
      expect(treeData.value[0].id).toBe("c1");
      expect(treeData.value[0].name).toBe("自定义节点 1");
      expect(treeData.value[0].children).toBeDefined();
      expect(treeData.value[0].children![0].id).toBe("c1-1");
      expect(treeData.value[0].children![0].name).toBe("自定义子节点 1-1");
    });

    it("部分自定义字段映射 - 保留未指定字段的默认值", () => {
      const partialData = [
        { uid: "u1", label: "用户 1", children: [{ uid: "u1-1", label: "子用户" }] },
      ];
      const { treeData } = useTreeData({
        source: partialData,
        fieldMapping: { id: "uid", name: "label" },
      });

      expect(treeData.value).toHaveLength(1);
      expect(treeData.value[0].id).toBe("u1");
      expect(treeData.value[0].name).toBe("用户 1");
      expect(treeData.value[0].children).toBeDefined();
    });

    it("响应式数据源 - source 改变时 treeData 自动更新", async () => {
      const source = ref(defaultData);
      const { treeData } = useTreeData({ source });

      expect(treeData.value).toHaveLength(3);

      // 修改数据源
      source.value = [{ id: "new-1", name: "新节点" }];
      await nextTick();

      expect(treeData.value).toHaveLength(1);
      expect(treeData.value[0].id).toBe("new-1");
      expect(treeData.value[0].name).toBe("新节点");
    });

    it("空数据源 - 返回空数组", () => {
      const { treeData } = useTreeData({ source: [] });

      expect(treeData.value).toEqual([]);
    });

    it("undefined 数据源 - 返回空数组", () => {
      const source = ref<typeof defaultData | undefined>(undefined);
      const { treeData } = useTreeData({ source });

      expect(treeData.value).toEqual([]);
    });

    it("保留额外属性 - 非映射字段被保留在节点上", () => {
      const { treeData } = useTreeData({ source: dataWithExtras });

      expect(treeData.value).toHaveLength(1);
      expect(treeData.value[0].disabled).toBe(true);
      expect(treeData.value[0].extraField).toBe("extra-value");
    });
  });

  // ==========================================================================
  // 选中状态管理
  // ==========================================================================
  describe("选中状态管理", () => {
    describe("单选模式 (mode: 'single')", () => {
      it("toggleSelect 选中一个节点", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "single",
        });

        toggleSelect("1");

        expect(selectedIds.value).toEqual(["1"]);
      });

      it("toggleSelect 取消选中已选节点", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "single",
        });

        toggleSelect("1");
        toggleSelect("1");

        expect(selectedIds.value).toEqual([]);
      });

      it("选中另一个节点时替换之前的选中", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "single",
        });

        toggleSelect("1");
        toggleSelect("2");

        expect(selectedIds.value).toEqual(["2"]);
      });
    });

    describe("多选模式 (mode: 'multiple')", () => {
      it("toggleSelect 选中多个节点", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "multiple",
        });

        toggleSelect("1");
        toggleSelect("2");
        toggleSelect("3");

        expect(selectedIds.value).toEqual(["1", "2", "3"]);
      });

      it("toggleSelect 取消选中某个节点", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "multiple",
        });

        toggleSelect("1");
        toggleSelect("2");
        toggleSelect("1"); // 取消选中 1

        expect(selectedIds.value).toEqual(["2"]);
      });

      it("多次切换同一节点保持正确状态", () => {
        const { toggleSelect, selectedIds } = useTreeData({
          source: defaultData,
          mode: "multiple",
        });

        toggleSelect("1");
        toggleSelect("1");
        toggleSelect("1");

        expect(selectedIds.value).toEqual(["1"]);
      });
    });

    describe("modelValue 双向绑定", () => {
      it("使用外部 modelValue Ref - 修改时 selectedIds 同步", () => {
        const modelValue = ref<(string | number)[]>([]);
        const { selectedIds } = useTreeData({
          source: defaultData,
          modelValue,
          mode: "multiple",
        });

        expect(selectedIds.value).toEqual([]);

        modelValue.value = ["1", "3"];
        expect(selectedIds.value).toEqual(["1", "3"]);
      });

      it("使用外部 modelValue Ref - toggleSelect 修改 modelValue", () => {
        const modelValue = ref<(string | number)[]>([]);
        const { toggleSelect } = useTreeData({
          source: defaultData,
          modelValue,
          mode: "multiple",
        });

        toggleSelect("1");
        expect(modelValue.value).toEqual(["1"]);

        toggleSelect("2");
        expect(modelValue.value).toEqual(["1", "2"]);
      });

      it("使用外部 modelValue Ref - clearSelection 清空", () => {
        const modelValue = ref<(string | number)[]>(["1", "2"]);
        const { clearSelection } = useTreeData({
          source: defaultData,
          modelValue,
        });

        clearSelection();
        expect(modelValue.value).toEqual([]);
      });

      it("默认单例模式 - 未提供 modelValue 时使用内部状态", () => {
        const { selectedIds, toggleSelect } = useTreeData({
          source: defaultData,
        });

        expect(selectedIds.value).toEqual([]);

        toggleSelect("1");
        expect(selectedIds.value).toEqual(["1"]);
      });
    });

    describe("clearSelection", () => {
      it("清空所有已选节点", () => {
        const { toggleSelect, clearSelection, selectedIds } = useTreeData({
          source: defaultData,
          mode: "multiple",
        });

        toggleSelect("1");
        toggleSelect("2");
        clearSelection();

        expect(selectedIds.value).toEqual([]);
      });

      it("空状态调用 clearSelection 不报错", () => {
        const { clearSelection, selectedIds } = useTreeData({
          source: defaultData,
        });

        expect(() => clearSelection()).not.toThrow();
        expect(selectedIds.value).toEqual([]);
      });
    });

    describe("selectedNodes", () => {
      it("返回选中节点的完整对象", () => {
        const { toggleSelect, selectedNodes } = useTreeData({
          source: defaultData,
          mode: "multiple",
        });

        toggleSelect("1");
        toggleSelect("2");

        expect(selectedNodes.value).toHaveLength(2);
        expect(selectedNodes.value[0].id).toBe("1");
        expect(selectedNodes.value[0].name).toBe("根节点 1");
        expect(selectedNodes.value[1].id).toBe("2");
        expect(selectedNodes.value[1].name).toBe("根节点 2");
      });

      it("未选中时返回空数组", () => {
        const { selectedNodes } = useTreeData({ source: defaultData });

        expect(selectedNodes.value).toEqual([]);
      });

      it("选中的节点不存在于树中时被过滤掉", () => {
        const modelValue = ref<(string | number)[]>(["non-existent-id"]);
        const { selectedNodes } = useTreeData({
          source: defaultData,
          modelValue,
        });

        expect(selectedNodes.value).toEqual([]);
      });
    });
  });

  // ==========================================================================
  // 搜索过滤能力
  // ==========================================================================
  describe("搜索过滤", () => {
    it("searchable: false 时 filteredData 等于 treeData", () => {
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: false,
      });

      expect(filteredData.value).toHaveLength(3);
    });

    it("按关键词过滤节点 - 匹配时才返回", () => {
      const searchQuery = ref("根节点 1");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toHaveLength(1);
      expect(filteredData.value[0].id).toBe("1");
    });

    it("搜索匹配子节点时保留祖先路径", () => {
      const searchQuery = ref("孙节点");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toHaveLength(1);
      expect(filteredData.value[0].id).toBe("1");
      expect(filteredData.value[0].children).toBeDefined();
      // 祖先路径保留，但只有匹配的子孙节点路径保留
      const child = filteredData.value[0].children!.find((c) => c.id === "1-2");
      expect(child).toBeDefined();
      expect(child!.children![0].id).toBe("1-2-1");
    });

    it("搜索过滤大小写不敏感", () => {
      const searchQuery = ref("节点 1");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      // 应该匹配 "根节点 1", "子节点 1-1", "子节点 1-2", "孙节点 1-2-1" 等
      expect(filteredData.value.length).toBeGreaterThan(0);
    });

    it("清空搜索关键词 - 恢复完整数据", () => {
      const searchQuery = ref("孙节点");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value.length).toBeGreaterThan(0);

      searchQuery.value = "";
      expect(filteredData.value).toHaveLength(3);
    });

    it("搜索无结果 - 返回空数组", () => {
      const searchQuery = ref("不存在的节点");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toEqual([]);
    });

    it("搜索关键词为空格时返回全部数据", () => {
      const searchQuery = ref("   ");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toHaveLength(3);
    });

    it("searchQuery 为 Ref 时响应式更新", async () => {
      const searchQuery = ref("");
      const { filteredData } = useTreeData({
        source: defaultData,
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toHaveLength(3);

      searchQuery.value = "根节点 2";
      await nextTick();

      expect(filteredData.value).toHaveLength(1);
      expect(filteredData.value[0].id).toBe("2");
    });

    it("搜索空树 - 不报错", () => {
      const searchQuery = ref("test");
      const { filteredData } = useTreeData({
        source: [],
        searchable: true,
        searchQuery,
      });

      expect(filteredData.value).toEqual([]);
    });
  });

  // ==========================================================================
  // 节点查找能力
  // ==========================================================================
  describe("节点查找", () => {
    it("findNode 按 ID 查找根节点", () => {
      const { findNode } = useTreeData({ source: defaultData });

      const node = findNode("2");
      expect(node).toBeDefined();
      expect(node!.id).toBe("2");
      expect(node!.name).toBe("根节点 2");
    });

    it("findNode 查找直接子节点", () => {
      const { findNode } = useTreeData({ source: defaultData });

      const node = findNode("1-1");
      expect(node).toBeDefined();
      expect(node!.id).toBe("1-1");
      expect(node!.name).toBe("子节点 1-1");
    });

    it("findNode 查找深层孙节点", () => {
      const { findNode } = useTreeData({ source: defaultData });

      const node = findNode("1-2-1");
      expect(node).toBeDefined();
      expect(node!.id).toBe("1-2-1");
      expect(node!.name).toBe("孙节点 1-2-1");
    });

    it("findNode 查找不存在的节点 - 返回 undefined", () => {
      const { findNode } = useTreeData({ source: defaultData });

      const node = findNode("non-existent");
      expect(node).toBeUndefined();
    });

    it("findNode 在空树中查找 - 返回 undefined", () => {
      const { findNode } = useTreeData({ source: [] });

      const node = findNode("1");
      expect(node).toBeUndefined();
    });

    it("findNode 支持 number 类型 id", () => {
      const numericData = [
        { id: 1, name: "节点 1" },
        { id: 2, name: "节点 2" },
      ];
      const { findNode } = useTreeData({ source: numericData });

      const node = findNode(2);
      expect(node).toBeDefined();
      expect(node!.id).toBe(2);
      expect(node!.name).toBe("节点 2");
    });
  });

  // ==========================================================================
  // 获取祖先节点
  // ==========================================================================
  describe("getAncestors", () => {
    it("获取根节点的直接子节点的祖先 - 返回根节点", () => {
      const { getAncestors } = useTreeData({ source: defaultData });

      const ancestors = getAncestors("1-1");
      expect(ancestors).toHaveLength(1);
      expect(ancestors[0].id).toBe("1");
      expect(ancestors[0].name).toBe("根节点 1");
    });

    it("获取深层节点的祖先链 - 从根到直接父节点", () => {
      const { getAncestors } = useTreeData({ source: defaultData });

      const ancestors = getAncestors("1-2-1");
      expect(ancestors).toHaveLength(2);
      // 从根到直接父节点排序
      expect(ancestors[0].id).toBe("1");
      expect(ancestors[0].name).toBe("根节点 1");
      expect(ancestors[1].id).toBe("1-2");
      expect(ancestors[1].name).toBe("子节点 1-2");
    });

    it("获取根节点的祖先 - 返回空数组", () => {
      const { getAncestors } = useTreeData({ source: defaultData });

      const ancestors = getAncestors("1");
      expect(ancestors).toEqual([]);
    });

    it("查找不存在节点的祖先 - 返回空数组", () => {
      const { getAncestors } = useTreeData({ source: defaultData });

      const ancestors = getAncestors("non-existent");
      expect(ancestors).toEqual([]);
    });

    it("祖先节点包含完整的节点信息", () => {
      const { getAncestors } = useTreeData({ source: defaultData });

      const ancestors = getAncestors("3-1");
      expect(ancestors).toHaveLength(1);
      expect(ancestors[0].id).toBe("3");
      expect(ancestors[0].name).toBe("根节点 3");
      expect(ancestors[0].children).toBeDefined();
    });
  });

  // ==========================================================================
  // 展开状态
  // ==========================================================================
  describe("展开状态", () => {
    describe("toggleExpand", () => {
      it("展开一个节点", () => {
        const { toggleExpand, expandedIds } = useTreeData({
          source: defaultData,
        });

        toggleExpand("1");
        expect(expandedIds.value.has("1")).toBe(true);
      });

      it("折叠已展开的节点", () => {
        const { toggleExpand, expandedIds } = useTreeData({
          source: defaultData,
        });

        toggleExpand("1");
        toggleExpand("1");
        expect(expandedIds.value.has("1")).toBe(false);
      });

      it("展开多个节点", () => {
        const { toggleExpand, expandedIds } = useTreeData({
          source: defaultData,
        });

        toggleExpand("1");
        toggleExpand("3");
        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
        expect(expandedIds.value.size).toBe(2);
      });
    });

    describe("expandToLevel", () => {
      it("展开到第 1 层 - 仅展开根节点的直接子节点（需要有子节点才展开）", () => {
        const { expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        expandToLevel(1);

        // 第 0 层的节点有子节点时才展开
        // 节点 "1" 和 "3" 有子节点，节点 "2" 没有
        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
        expect(expandedIds.value.has("2")).toBe(false); // 无子节点
      });

      it("展开到第 2 层 - 包含二级子节点", () => {
        const { expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        expandToLevel(2);

        // 根节点有子节点的 → 展开
        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);

        // 1-2 有孙节点 → 展开
        expect(expandedIds.value.has("1-2")).toBe(true);

        // 1-1 和 3-1 在第 1 层有子节点吗？没有。所以不会展开
        expect(expandedIds.value.has("1-1")).toBe(false);
      });

      it("expandToLevel(0) - 不做任何展开", () => {
        const { expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        expandToLevel(0);
        expect(expandedIds.value.size).toBe(0);
      });

      it("expandToLevel 负数 - 不做任何展开", () => {
        const { toggleExpand, expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        toggleExpand("1");
        expect(expandedIds.value.size).toBe(1);

        expandToLevel(-1);
        expect(expandedIds.value.size).toBe(0);
      });

      it("expandToLevel 先清空再设置展开状态", () => {
        const { toggleExpand, expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        toggleExpand("1");
        toggleExpand("3");
        expect(expandedIds.value.size).toBe(2);

        expandToLevel(1);
        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
        // 之前的展开状态被清空后重新设置
      });

      it("展开到超出树深度的层级 - 安全处理", () => {
        const { expandToLevel, expandedIds } = useTreeData({
          source: defaultData,
        });

        // 树最多 3 层，展开到 10 层
        expect(() => expandToLevel(10)).not.toThrow();

        // 所有有子节点的节点都被展开
        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("1-2")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
      });
    });

    describe("defaultExpandLevel", () => {
      it("defaultExpandLevel 初始化时自动展开到指定层级", () => {
        const { expandedIds } = useTreeData({
          source: defaultData,
          defaultExpandLevel: 1,
        });

        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
      });

      it("defaultExpandLevel: 0 时不展开", () => {
        const { expandedIds } = useTreeData({
          source: defaultData,
          defaultExpandLevel: 0,
        });

        expect(expandedIds.value.size).toBe(0);
      });

      it("defaultExpandLevel: 2 展开两层", () => {
        const { expandedIds } = useTreeData({
          source: defaultData,
          defaultExpandLevel: 2,
        });

        expect(expandedIds.value.has("1")).toBe(true);
        expect(expandedIds.value.has("1-2")).toBe(true);
        expect(expandedIds.value.has("3")).toBe(true);
      });
    });
  });

  // ==========================================================================
  // 边界情况与综合测试
  // ==========================================================================
  describe("边界情况", () => {
    it("单节点树 - 所有功能正常", () => {
      const { treeData, findNode, getAncestors, toggleSelect } = useTreeData({
        source: [{ id: "solo", name: "唯一节点" }],
        mode: "single",
      });

      expect(treeData.value).toHaveLength(1);
      expect(findNode("solo")).toBeDefined();
      expect(getAncestors("solo")).toEqual([]);

      toggleSelect("solo");
      expect(findNode("solo")).toBeDefined();
    });

    it("深层嵌套树 - 查找与祖先遍历正确", () => {
      const deepData = [
        {
          id: "L0",
          name: "Level 0",
          children: [
            {
              id: "L1",
              name: "Level 1",
              children: [
                {
                  id: "L2",
                  name: "Level 2",
                  children: [
                    { id: "L3", name: "Level 3" },
                  ],
                },
              ],
            },
          ],
        },
      ];

      const { findNode, getAncestors } = useTreeData({ source: deepData });

      expect(findNode("L3")).toBeDefined();
      const ancestors = getAncestors("L3");
      expect(ancestors).toHaveLength(3);
      expect(ancestors.map((a) => a.id)).toEqual(["L0", "L1", "L2"]);
    });

    it("无子节点的数据 - 正常工作", () => {
      const flatData = [
        { id: "a", name: "节点 A" },
        { id: "b", name: "节点 B" },
      ];

      const { treeData, toggleExpand, expandedIds } = useTreeData({
        source: flatData,
      });

      expect(treeData.value).toHaveLength(2);
      // 对无子节点执行 toggleExpand 不应报错
      expect(() => toggleExpand("a")).not.toThrow();
      expect(expandedIds.value.has("a")).toBe(true);
    });

    it("使用 ref 作为 source 传入", () => {
      const source = ref(defaultData);
      const { treeData } = useTreeData({ source });

      expect(treeData.value).toHaveLength(3);
    });

    it("所有返回的方法和状态都存在", () => {
      const result = useTreeData({ source: defaultData });

      expect(result.treeData).toBeDefined();
      expect(result.selectedIds).toBeDefined();
      expect(result.selectedNodes).toBeDefined();
      expect(result.filteredData).toBeDefined();
      expect(result.expandedIds).toBeDefined();
      expect(typeof result.findNode).toBe("function");
      expect(typeof result.getAncestors).toBe("function");
      expect(typeof result.toggleSelect).toBe("function");
      expect(typeof result.clearSelection).toBe("function");
      expect(typeof result.toggleExpand).toBe("function");
      expect(typeof result.expandToLevel).toBe("function");
    });
  });
});
