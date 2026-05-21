import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppButton from "@/framework/components/ui/AppButton.vue";
import AppCard from "@/framework/components/ui/AppCard.vue";
import AppLoading from "@/framework/components/ui/AppLoading.vue";
import AppInput from "@/framework/components/ui/AppInput.vue";

describe("P0 Components", () => {
  describe("AppButton", () => {
    it("renders correctly with default props", () => {
      const wrapper = mount(AppButton, {
        slots: { default: "Click me" },
      });

      expect(wrapper.text()).toContain("Click me");
      expect(wrapper.find(".app-button--primary").exists()).toBe(true);
    });

    it("renders with different variants", () => {
      const variants = ["primary", "secondary", "outline", "ghost", "danger"] as const;

      variants.forEach((variant) => {
        const wrapper = mount(AppButton, {
          props: { variant },
        });

        expect(wrapper.find(`.app-button--${variant}`).exists()).toBe(true);
      });
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(AppButton, {
          props: { size },
        });

        expect(wrapper.find(`.app-button--${size}`).exists()).toBe(true);
      });
    });

    it("emits click event", async () => {
      const wrapper = mount(AppButton);

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeTruthy();
    });

    it("does not emit click when disabled", async () => {
      const wrapper = mount(AppButton, {
        props: { disabled: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });

    it("does not emit click when loading", async () => {
      const wrapper = mount(AppButton, {
        props: { loading: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });
  });

  describe("AppCard", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppCard, {
        slots: { default: "Card content" },
      });

      expect(wrapper.text()).toContain("Card content");
    });

    it("renders with title", () => {
      const wrapper = mount(AppCard, {
        props: { title: "Card Title" },
      });

      expect(wrapper.text()).toContain("Card Title");
    });

    it("renders with header slot", () => {
      const wrapper = mount(AppCard, {
        slots: { header: "Custom Header" },
      });

      expect(wrapper.text()).toContain("Custom Header");
    });

    it("renders with footer slot", () => {
      const wrapper = mount(AppCard, {
        slots: { footer: "Custom Footer" },
      });

      expect(wrapper.text()).toContain("Custom Footer");
    });
  });

  describe("AppLoading", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppLoading);

      expect(wrapper.find(".app-loading").exists()).toBe(true);
    });

    it("renders with text", () => {
      const wrapper = mount(AppLoading, {
        props: { text: "Loading..." },
      });

      expect(wrapper.text()).toContain("Loading...");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(AppLoading, {
          props: { size },
        });

        expect(wrapper.find(`.app-loading--${size}`).exists()).toBe(true);
      });
    });
  });

  describe("AppInput", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppInput);

      expect(wrapper.find(".app-input").exists()).toBe(true);
      expect(wrapper.find("input").exists()).toBe(true);
    });

    it("updates model value", async () => {
      const wrapper = mount(AppInput, {
        props: { modelValue: "" },
      });

      const input = wrapper.find("input");
      await input.setValue("test value");

      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
      expect(wrapper.emitted("update:modelValue")![0]).toEqual(["test value"]);
    });

    it("renders with error state", () => {
      const wrapper = mount(AppInput, {
        props: { error: "This field is required" },
      });

      expect(wrapper.find(".app-input--error").exists()).toBe(true);
      expect(wrapper.text()).toContain("This field is required");
    });

    it("renders with placeholder", () => {
      const wrapper = mount(AppInput, {
        props: { placeholder: "Enter text" },
      });

      expect(wrapper.find("input").attributes("placeholder")).toBe("Enter text");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(AppInput, {
          props: { size },
        });

        expect(wrapper.find(`.app-input--${size}`).exists()).toBe(true);
      });
    });
  });
});
