import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppPage from "@/framework/layouts/components/AppPage.vue";

describe("AppPage", () => {
  describe("页面头部区域渲染", () => {
    it("渲染 title、eyebrow、description", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "用户管理",
          eyebrow: "系统管理",
          description: "管理系统中所有用户账号。",
        },
      });

      // eyebrow 小字标题上方提示文字
      const eyebrow = wrapper.find("p.text-muted-foreground.text-xs.font-medium");
      expect(eyebrow.exists()).toBe(true);
      expect(eyebrow.text()).toBe("系统管理");

      // title 页面主标题
      const title = wrapper.find("h1.text-2xl.font-semibold.tracking-normal");
      expect(title.exists()).toBe(true);
      expect(title.text()).toBe("用户管理");

      // description 页面功能描述
      const description = wrapper.find("p.text-muted-foreground.max-w-3xl.text-sm");
      expect(description.exists()).toBe(true);
      expect(description.text()).toBe("管理系统中所有用户账号。");
    });

    it("不传 eyebrow 时不渲染对应元素", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "用户管理",
        },
      });

      const eyebrow = wrapper.find("p.text-muted-foreground.text-xs.font-medium");
      expect(eyebrow.exists()).toBe(false);
    });

    it("不传 description 时不渲染对应元素", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "用户管理",
        },
      });

      // 只检查 description 相关的 p 标签，排除 eyebrow
      const descriptions = wrapper.findAll("p.text-muted-foreground.max-w-3xl.text-sm");
      expect(descriptions.length).toBe(0);
    });
  });

  describe("操作区渲染", () => {
    it("使用 actions slot 时渲染操作区", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
        slots: {
          actions: '<button class="test-btn">新建用户</button>',
        },
      });

      const actionsContainer = wrapper.find(".flex.shrink-0.flex-wrap.items-center.gap-2");
      expect(actionsContainer.exists()).toBe(true);
      expect(actionsContainer.find(".test-btn").exists()).toBe(true);
      expect(actionsContainer.text()).toContain("新建用户");
    });

    it("不使用 actions slot 时不渲染操作区容器", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const actionsContainer = wrapper.find(".flex.shrink-0.flex-wrap.items-center.gap-2");
      expect(actionsContainer.exists()).toBe(false);
    });
  });

  describe("页面内容区渲染", () => {
    it("渲染 default slot 内容", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
        slots: {
          default: '<div class="test-content">页面内容</div>',
        },
      });

      expect(wrapper.find(".test-content").exists()).toBe(true);
      expect(wrapper.text()).toContain("页面内容");
    });
  });

  describe("页面变体", () => {
    it("默认 variant 为 list，使用 bg-background", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("bg-background");
      expect(main.classes()).not.toContain("bg-muted/20");
    });

    it("variant 为 workbench 时使用 bg-muted/20", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "智能问答",
          variant: "workbench",
        },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("bg-muted/20");
    });

    it("variant 为 detail 时使用 bg-background", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "用户详情",
          variant: "detail",
        },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("bg-background");
    });

    it("variant 为 governance 时使用 bg-background", () => {
      const wrapper = mount(AppPage, {
        props: {
          title: "权限管理",
          variant: "governance",
        },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("bg-background");
    });
  });

  describe("容器高度", () => {
    it("容器高度为 calc(100svh - 3.5rem)", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("h-[calc(100svh-3.5rem)]");
    });

    it("启用 overflow-auto 允许内容滚动", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const main = wrapper.find("main");
      expect(main.classes()).toContain("overflow-auto");
    });
  });

  describe("页面间距与布局", () => {
    it("内容容器使用正确的间距样式", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const container = wrapper.find(".mx-auto.flex.min-h-full.w-full.flex-col.gap-5");
      expect(container.exists()).toBe(true);
      expect(container.classes()).toContain("p-4");
      expect(container.classes()).toContain("md:p-6");
      expect(container.classes()).toContain("gap-5");
    });

    it("头部区域使用响应式布局", () => {
      const wrapper = mount(AppPage, {
        props: { title: "用户管理" },
      });

      const header = wrapper.find("header");
      expect(header.classes()).toContain("flex");
      expect(header.classes()).toContain("flex-col");
      expect(header.classes()).toContain("gap-3");
      expect(header.classes()).toContain("md:flex-row");
      expect(header.classes()).toContain("md:items-end");
      expect(header.classes()).toContain("md:justify-between");
    });

    it("标题使用 truncate 类确保不超出容器宽度", () => {
      const wrapper = mount(AppPage, {
        props: { title: "这是一个非常非常非常非常非常长的标题" },
      });

      const title = wrapper.find("h1");
      expect(title.classes()).toContain("truncate");
    });
  });
});
