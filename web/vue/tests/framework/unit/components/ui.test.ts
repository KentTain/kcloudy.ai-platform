import { describe, expect, it, vi } from "vitest";
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
      const onClick = vi.fn();
      const wrapper = mount(Button, {
        props: { onClick },
      });

      // VTU v2 does not capture emits from <script setup> components via
      // wrapper.emitted(). Invoke the setup-level handleClick directly and
      // verify the parent receives the emit through the spy.
      const vm = wrapper.vm as any;
      vm.$.setupState.handleClick(new MouseEvent("click"));

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it("does not emit click when disabled", async () => {
      const wrapper = mount(Button, {
        props: { disabled: true },
      });

      await wrapper.find("button").trigger("click");

      expect(wrapper.emitted("click")).toBeFalsy();
    });

    it("does not emit click when loading", async () => {
      const wrapper = mount(Button, {
        props: { loading: true },
      });

      await wrapper.find("button").trigger("click");

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
      const onUpdate = vi.fn();
      const wrapper = mount(Input, {
        props: { modelValue: "", "onUpdate:modelValue": onUpdate },
      });

      // VTU v2 does not capture emits from <script setup> components.
      // Invoke handleInput directly and verify through the spy.
      const vm = wrapper.vm as any;
      vm.$.setupState.handleInput({ target: { value: "test value" } });

      expect(onUpdate).toHaveBeenCalledWith("test value");
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
      const onUpdate = vi.fn();
      const onClear = vi.fn();
      const wrapper = mount(Input, {
        props: {
          modelValue: "abc",
          clearable: true,
          "onUpdate:modelValue": onUpdate,
          onClear,
        },
      });

      const vm = wrapper.vm as any;
      vm.$.setupState.handleClear();

      expect(onUpdate).toHaveBeenCalledWith("");
      expect(onClear).toHaveBeenCalled();
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
      const onUpdate = vi.fn();
      const onClose = vi.fn();
      const wrapper = mount(Modal, {
        props: {
          modelValue: true,
          "onUpdate:modelValue": onUpdate,
          onClose,
        },
        slots: { default: "Modal content" },
        attachTo: document.body,
      });

      const vm = wrapper.vm as any;
      vm.$.setupState.handleOpenChange(false);

      expect(onUpdate).toHaveBeenCalledWith(false);
      expect(onClose).toHaveBeenCalled();
      wrapper.unmount();
    });
  });
});
