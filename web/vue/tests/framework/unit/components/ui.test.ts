import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { Button, Card, Loading, Input, Modal } from "@/components/common";

describe("P0 Components", () => {
  describe("Button", () => {
    it("renders correctly with default props", () => {
      const wrapper = mount(Button, {
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
        const wrapper = mount(Button, {
          props: { variant },
        });

        expect(wrapper.find("button").classes()).toContain(expected);
      });
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(Button, {
          props: { size },
        });

        expect(wrapper.find("button").exists()).toBe(true);
      });
    });

    it("emits click event", async () => {
      const wrapper = mount(Button);

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeTruthy();
    });

    it("does not emit click when disabled", async () => {
      const wrapper = mount(Button, {
        props: { disabled: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });

    it("does not emit click when loading", async () => {
      const wrapper = mount(Button, {
        props: { loading: true },
      });

      await wrapper.trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });
  });

  describe("Card", () => {
    it("renders correctly", () => {
      const wrapper = mount(Card, {
        slots: { default: "Card content" },
      });

      expect(wrapper.text()).toContain("Card content");
    });

    it("renders with title", () => {
      const wrapper = mount(Card, {
        props: { title: "Card Title" },
      });

      expect(wrapper.text()).toContain("Card Title");
    });

    it("renders with header slot", () => {
      const wrapper = mount(Card, {
        slots: { header: "Custom Header" },
      });

      expect(wrapper.text()).toContain("Custom Header");
    });

    it("renders with footer slot", () => {
      const wrapper = mount(Card, {
        slots: { footer: "Custom Footer" },
      });

      expect(wrapper.text()).toContain("Custom Footer");
    });
  });

  describe("Loading", () => {
    it("renders correctly", () => {
      const wrapper = mount(Loading);

      expect(wrapper.find(".animate-spin").exists()).toBe(true);
    });

    it("renders with text", () => {
      const wrapper = mount(Loading, {
        props: { text: "Loading..." },
      });

      expect(wrapper.text()).toContain("Loading...");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(Loading, {
          props: { size },
        });

        expect(wrapper.find(".animate-spin").exists()).toBe(true);
      });
    });
  });

  describe("Input", () => {
    it("renders correctly", () => {
      const wrapper = mount(Input);

      expect(wrapper.find("input").exists()).toBe(true);
    });

    it("updates model value", async () => {
      const wrapper = mount(Input, {
        props: { modelValue: "" },
      });

      const input = wrapper.find("input");
      await input.setValue("test value");

      expect(wrapper.emitted("update:modelValue")).toBeTruthy();
      expect(wrapper.emitted("update:modelValue")![0]).toEqual(["test value"]);
    });

    it("renders with error state", () => {
      const wrapper = mount(Input, {
        props: { error: "This field is required" },
      });

      expect(wrapper.text()).toContain("This field is required");
    });

    it("renders with placeholder", () => {
      const wrapper = mount(Input, {
        props: { placeholder: "Enter text" },
      });

      expect(wrapper.find("input").attributes("placeholder")).toBe("Enter text");
    });

    it("renders with different sizes", () => {
      const sizes = ["sm", "md", "lg"] as const;

      sizes.forEach((size) => {
        const wrapper = mount(Input, {
          props: { size },
        });

        expect(wrapper.find("input").exists()).toBe(true);
      });
    });

    it("clears value without throwing", async () => {
      const wrapper = mount(Input, {
        props: { modelValue: "abc", clearable: true },
      });

      await wrapper.find("button").trigger("click");

      expect(wrapper.emitted("update:modelValue")![0]).toEqual([""]);
      expect(wrapper.emitted("clear")).toBeTruthy();
    });

    it("exposes focus and blur methods", () => {
      const wrapper = mount(Input);

      expect(() => wrapper.vm.focus()).not.toThrow();
      expect(() => wrapper.vm.blur()).not.toThrow();
    });
  });

  describe("Modal", () => {
    it("hides close button when closable is false", () => {
      const wrapper = mount(Modal, {
        props: { modelValue: true, closable: false },
        slots: { default: "Modal content" },
        attachTo: document.body,
      });

      expect(document.body.querySelector('[data-slot="dialog-close"]')).toBeNull();
      wrapper.unmount();
    });

    it("emits close when dialog closes", async () => {
      const wrapper = mount(Modal, {
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
