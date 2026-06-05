import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CommonButton from "@/components/CommonButton.vue";
import CommonCard from "@/components/CommonCard.vue";
import CommonLoading from "@/components/CommonLoading.vue";
import CommonInput from "@/components/CommonInput.vue";
import CommonModal from "@/components/CommonModal.vue";

describe("P0 Components", () => {
  describe("CommonButton", () => {
    it("renders correctly with default props", () => {
      const wrapper = mount(CommonButton, {
        slots: { default: "Click me" },
      });

      expect(wrapper.text()).toContain("Click me");
      // shadcn Button uses data-variant attribute
      expect(wrapper.find("button").exists()).toBe(true);
    });

    it("renders with business variant classes", () => {
      const cases = [
        { variant: "primary", expected: "bg-primary" },
        { variant: "outline", expected: "border-primary" },
        { variant: "danger", expected: "bg-destructive" },
      ] as const;

      cases.forEach(({ variant, expected }) => {
        const wrapper = mount(CommonButton, {
          props: { variant },
        });

        expect(wrapper.find("button").classes()).toContain(expected);
      });
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(CommonButton, {
          props: { size },
        });

        expect(wrapper.find("button").exists()).toBe(true);
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

      expect(wrapper.find(".animate-spin").exists()).toBe(true);
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

        expect(wrapper.find(".animate-spin").exists()).toBe(true);
      });
    });
  });

  describe("CommonInput", () => {
    it("renders correctly", () => {
      const wrapper = mount(CommonInput);

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

        expect(wrapper.find("input").exists()).toBe(true);
      });
    });

    it("clears value without throwing", async () => {
      const wrapper = mount(CommonInput, {
        props: { modelValue: "abc", clearable: true },
      });

      await wrapper.find("button").trigger("click");

      expect(wrapper.emitted("update:modelValue")![0]).toEqual([""]);
      expect(wrapper.emitted("clear")).toBeTruthy();
    });

    it("exposes focus and blur methods", () => {
      const wrapper = mount(CommonInput);

      expect(() => wrapper.vm.focus()).not.toThrow();
      expect(() => wrapper.vm.blur()).not.toThrow();
    });
  });

  describe("CommonModal", () => {
    it("hides close button when closable is false", () => {
      const wrapper = mount(CommonModal, {
        props: { modelValue: true, closable: false },
        slots: { default: "Modal content" },
        attachTo: document.body,
      });

      expect(document.body.querySelector('[data-slot="dialog-close"]')).toBeNull();
      wrapper.unmount();
    });

    it("emits close when dialog closes", async () => {
      const wrapper = mount(CommonModal, {
        props: { modelValue: true },
        slots: { default: "Modal content" },
        attachTo: document.body,
      });

      await wrapper.findComponent({ name: "DialogRoot" }).vm.$emit("update:open", false);

      expect(wrapper.emitted("update:modelValue")![0]).toEqual([false]);
      expect(wrapper.emitted("close")).toBeTruthy();
      wrapper.unmount();
    });
  });
});
