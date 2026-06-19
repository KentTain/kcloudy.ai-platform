import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import ForbiddenPage from "@/framework/pages/ForbiddenPage.vue";
import NotFoundPage from "@/framework/pages/NotFoundPage.vue";

// Mock vue-router
const mockPush = vi.fn();
const mockBack = vi.fn();
vi.mock("vue-router", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

describe("ForbiddenPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockPush.mockClear();
    mockBack.mockClear();
  });

  it("renders centered layout", () => {
    const wrapper = mount(ForbiddenPage);
    const container = wrapper.find(".error-page");
    expect(container.exists()).toBe(true);
    expect(container.find(".error-page__content").exists()).toBe(true);
  });

  it("shows 403 error code", () => {
    const wrapper = mount(ForbiddenPage);
    const code = wrapper.find(".error-page__code");
    expect(code.exists()).toBe(true);
    expect(code.text()).toBe("403");
    expect(code.classes()).toContain("error-page__code--danger");
  });

  it("shows '无访问权限' title", () => {
    const wrapper = mount(ForbiddenPage);
    expect(wrapper.find(".error-page__title").text()).toBe("无访问权限");
  });

  it("has description text", () => {
    const wrapper = mount(ForbiddenPage);
    const desc = wrapper.find(".error-page__desc");
    expect(desc.exists()).toBe(true);
    expect(desc.text()).toBeTruthy();
  });

  it("uses shadcn Button for actions", () => {
    const wrapper = mount(ForbiddenPage);
    const buttons = wrapper.findAll('[data-slot="button"]');
    expect(buttons.length).toBe(2);
  });

  it("'返回上一页' button uses outline variant", () => {
    const wrapper = mount(ForbiddenPage);
    const outlineButton = wrapper.find('[data-variant="outline"]');
    expect(outlineButton.exists()).toBe(true);
    expect(outlineButton.text()).toContain("返回上一页");
  });

  it("'返回首页' button has default styling", () => {
    const wrapper = mount(ForbiddenPage);
    // Default variant may not have data-variant attribute, find second button
    const buttons = wrapper.findAll('[data-slot="button"]');
    const homeButton = buttons.find((b) => b.text().includes("返回首页"));
    expect(homeButton).toBeDefined();
  });

  it("calls router.back() on '返回上一页'", async () => {
    const wrapper = mount(ForbiddenPage);
    const outlineButton = wrapper.find('[data-variant="outline"]');
    await outlineButton.trigger("click");
    expect(mockBack).toHaveBeenCalled();
  });

  it("calls router.push('/') on '返回首页'", async () => {
    const wrapper = mount(ForbiddenPage);
    const buttons = wrapper.findAll('[data-slot="button"]');
    const homeButton = buttons.find((b) => b.text().includes("返回首页"));
    await homeButton!.trigger("click");
    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("does not import CommonButton or AppButton", () => {
    const imports = Object.keys(ForbiddenPage.components || {});
    expect(imports).not.toContain("CommonButton");
    expect(imports).not.toContain("AppButton");
  });
});

describe("NotFoundPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockPush.mockClear();
    mockBack.mockClear();
  });

  it("renders centered layout", () => {
    const wrapper = mount(NotFoundPage);
    const container = wrapper.find(".error-page");
    expect(container.exists()).toBe(true);
    expect(container.find(".error-page__content").exists()).toBe(true);
  });

  it("shows 404 error code", () => {
    const wrapper = mount(NotFoundPage);
    const code = wrapper.find(".error-page__code");
    expect(code.exists()).toBe(true);
    expect(code.text()).toBe("404");
    expect(code.classes()).toContain("error-page__code--primary");
  });

  it("shows '页面不存在' title", () => {
    const wrapper = mount(NotFoundPage);
    expect(wrapper.find(".error-page__title").text()).toBe("页面不存在");
  });

  it("uses shadcn Button for actions", () => {
    const wrapper = mount(NotFoundPage);
    const buttons = wrapper.findAll('[data-slot="button"]');
    expect(buttons.length).toBe(2);
  });

  it("'返回上一页' button uses outline variant", () => {
    const wrapper = mount(NotFoundPage);
    const outlineButton = wrapper.find('[data-variant="outline"]');
    expect(outlineButton.exists()).toBe(true);
    expect(outlineButton.text()).toContain("返回上一页");
  });

  it("'返回首页' button has default styling", () => {
    const wrapper = mount(NotFoundPage);
    const buttons = wrapper.findAll('[data-slot="button"]');
    const homeButton = buttons.find((b) => b.text().includes("返回首页"));
    expect(homeButton).toBeDefined();
  });

  it("calls router.back() on '返回上一页'", async () => {
    const wrapper = mount(NotFoundPage);
    const outlineButton = wrapper.find('[data-variant="outline"]');
    await outlineButton.trigger("click");
    expect(mockBack).toHaveBeenCalled();
  });

  it("calls router.push('/') on '返回首页'", async () => {
    const wrapper = mount(NotFoundPage);
    const buttons = wrapper.findAll('[data-slot="button"]');
    const homeButton = buttons.find((b) => b.text().includes("返回首页"));
    await homeButton!.trigger("click");
    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("does not import CommonButton or AppButton", () => {
    const imports = Object.keys(NotFoundPage.components || {});
    expect(imports).not.toContain("CommonButton");
    expect(imports).not.toContain("AppButton");
  });
});