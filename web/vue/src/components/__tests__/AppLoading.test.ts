import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppLoading from "../ui/AppLoading.vue";

describe("AppLoading", () => {
  it("renders spinner element", () => {
    const wrapper = mount(AppLoading);
    expect(wrapper.find(".animate-spin").exists()).toBe(true);
  });

  it("applies default medium size", () => {
    const wrapper = mount(AppLoading);
    const spinner = wrapper.find(".animate-spin");
    expect(spinner.classes()).toContain("h-8");
    expect(spinner.classes()).toContain("w-8");
  });

  it("applies small size when specified", () => {
    const wrapper = mount(AppLoading, {
      props: {
        size: "sm",
      },
    });
    const spinner = wrapper.find(".animate-spin");
    expect(spinner.classes()).toContain("h-4");
    expect(spinner.classes()).toContain("w-4");
  });

  it("applies large size when specified", () => {
    const wrapper = mount(AppLoading, {
      props: {
        size: "lg",
      },
    });
    const spinner = wrapper.find(".animate-spin");
    expect(spinner.classes()).toContain("h-12");
    expect(spinner.classes()).toContain("w-12");
  });

  it("has correct spinner styling", () => {
    const wrapper = mount(AppLoading);
    const spinner = wrapper.find(".animate-spin");
    expect(spinner.classes()).toContain("rounded-full");
    expect(spinner.classes()).toContain("border-4");
  });
});
