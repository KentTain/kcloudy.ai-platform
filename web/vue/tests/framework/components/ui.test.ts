import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CommonButton from "@/components/ui/CommonButton.vue";
import CommonCard from "@/components/ui/CommonCard.vue";
import CommonLoading from "@/components/ui/CommonLoading.vue";
import CommonInput from "@/components/ui/CommonInput.vue";

describe("P0 Components", () => {
  describe("CommonButton", () => {
    it("renders correctly with default props", () => {
      const wrapper = mount(CommonButton, {
        slots: { default: "Click me" },
      });

      expect(wrapper.text()).toContain("Click me");
      expect(wrapper.find(".common-button--primary").exists()).toBe(true);
    });

    it("renders with different variants", () => {
      const variants = ["primary", "secondary", "outline", "ghost", "danger"] as const;

      variants.forEach((variant) => {
        const wrapper = mount(CommonButton, {
          props: { variant },
        });

        expect(wrapper.find(`.common-button--${variant}`).exists()).toBe(true);
      });
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(CommonButton, {
          props: { size },
        });

        expect(wrapper.find(`.common-button--${size}`).exists()).toBe(true);
      });
    });

    it("emits click event", async () => {
      const wrapper = mount(CommonButton);

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeTruthy();
    });

    it("does not emit click when disabled", async () => {
      const wrapper = mount(CommonButton, {
        props: { disabled: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });

    it("does not emit click when loading", async () => {
      const wrapper = mount(CommonButton, {
        props: { loading: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });
  });

  describe("CommonCard", () => {
    it("renders correctly", () => {
      const wrapper = mount(CommonCard, {
        slots: { default: "Card content" },
      });

      expect(wrapper.text()).toContain("Card content");
    });

    it("renders with title", () => {
      const wrapper = mount(CommonCard, {
        props: { title: "Card Title" },
      });

      expect(wrapper.text()).toContain("Card Title");
    });

    it("renders with header slot", () => {
      const wrapper = mount(CommonCard, {
        slots: { header: "Custom Header" },
      });

      expect(wrapper.text()).toContain("Custom Header");
    });

    it("renders with footer slot", () => {
      const wrapper = mount(CommonCard, {
        slots: { footer: "Custom Footer" },
      });

      expect(wrapper.text()).toContain("Custom Footer");
    });
  });

  describe("CommonLoading", () => {
    it("renders correctly", () => {
      const wrapper = mount(CommonLoading);

      expect(wrapper.find(".common-loading").exists()).toBe(true);
    });

    it("renders with text", () => {
      const wrapper = mount(CommonLoading, {
        props: { text: "Loading..." },
      });

      expect(wrapper.text()).toContain("Loading...");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(CommonLoading, {
          props: { size },
        });

        expect(wrapper.find(`.common-loading--${size}`).exists()).toBe(true);
      });
    });
  });

  describe("CommonInput", () => {
    it("renders correctly", () => {
      const wrapper = mount(CommonInput);

      expect(wrapper.find(".common-input").exists()).toBe(true);
      expect(wrapper.find("input").exists()).toBe(true);
    });

    it("updates model value", async () => {
      const wrapper = mount(CommonInput, {
        props: { modelValue: "" },
      });

      const input = wrapper.find("input");
      await input.setValue("test value");

      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
      expect(wrapper.emitted("update:modelValue")![0]).toEqual(["test value"]);
    });

    it("renders with error state", () => {
      const wrapper = mount(CommonInput, {
        props: { error: "This field is required" },
      });

      expect(wrapper.find(".common-input--error").exists()).toBe(true);
      expect(wrapper.text()).toContain("This field is required");
    });

    it("renders with placeholder", () => {
      const wrapper = mount(CommonInput, {
        props: { placeholder: "Enter text" },
      });

      expect(wrapper.find("input").attributes("placeholder")).toBe("Enter text");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(CommonInput, {
          props: { size },
        });

        expect(wrapper.find(`.common-input--${size}`).exists()).toBe(true);
      });
    });
  });
});
