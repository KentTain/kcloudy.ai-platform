import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppCard from "../ui/AppCard.vue";

describe("AppCard", () => {
  it("renders with default slot content", () => {
    const wrapper = mount(AppCard, {
      slots: {
        default: "Card content",
      },
    });
    expect(wrapper.text()).toContain("Card content");
  });

  it("renders with title prop", () => {
    const wrapper = mount(AppCard, {
      props: {
        title: "Card Title",
      },
      slots: {
        default: "Card content",
      },
    });
    expect(wrapper.text()).toContain("Card Title");
    expect(wrapper.text()).toContain("Card content");
  });

  it("renders with header slot instead of title", () => {
    const wrapper = mount(AppCard, {
      slots: {
        header: "<h3>Custom Header</h3>",
        default: "Card content",
      },
    });
    expect(wrapper.html()).toContain("Custom Header");
  });

  it("applies correct styling classes", () => {
    const wrapper = mount(AppCard, {
      slots: {
        default: "Content",
      },
    });
    expect(wrapper.classes()).toContain("rounded-lg");
    expect(wrapper.classes()).toContain("border");
    expect(wrapper.classes()).toContain("bg-white");
  });
});
