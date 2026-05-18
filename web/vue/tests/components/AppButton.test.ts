import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppButton from "@/components/ui/AppButton.vue";

describe("AppButton", () => {
  it("renders with default props", () => {
    const wrapper = mount(AppButton, {
      slots: {
        default: "Click me",
      },
    });
    expect(wrapper.text()).toContain("Click me");
  });

  it("applies primary variant classes by default", () => {
    const wrapper = mount(AppButton, {
      slots: {
        default: "Primary",
      },
    });
    expect(wrapper.classes()).toContain("bg-blue-600");
    expect(wrapper.classes()).toContain("text-white");
  });

  it("applies secondary variant classes", () => {
    const wrapper = mount(AppButton, {
      props: {
        variant: "secondary",
      },
      slots: {
        default: "Secondary",
      },
    });
    expect(wrapper.classes()).toContain("bg-gray-200");
    expect(wrapper.classes()).toContain("text-gray-800");
  });

  it("applies disabled styles", () => {
    const wrapper = mount(AppButton, {
      props: {
        disabled: true,
      },
      slots: {
        default: "Disabled",
      },
    });
    expect(wrapper.classes()).toContain("disabled:bg-blue-300");
    expect(wrapper.element.hasAttribute("disabled")).toBe(true);
  });

  it("emits click event when not disabled", async () => {
    const wrapper = mount(AppButton, {
      slots: {
        default: "Click me",
      },
    });
    await wrapper.trigger("click");
    expect(wrapper.emitted("click")).toBeTruthy();
  });

  it("does not emit click when disabled", async () => {
    const wrapper = mount(AppButton, {
      props: {
        disabled: true,
      },
      slots: {
        default: "Disabled",
      },
    });
    await wrapper.trigger("click");
    expect(wrapper.emitted("click")).toBeFalsy();
  });
});
