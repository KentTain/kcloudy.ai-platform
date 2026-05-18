import { afterEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppModal from "../ui/AppModal.vue";

describe("AppModal", () => {
  let wrapper: ReturnType<typeof mount>;

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
    // Clean up any modal content in body
    document.body.innerHTML = "";
  });

  it("does not render when open is false", () => {
    wrapper = mount(AppModal, {
      props: {
        open: false,
      },
      slots: {
        default: "Modal content",
      },
    });
    expect(wrapper.html()).not.toContain("Modal content");
  });

  it("renders when open is true", () => {
    wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: "Modal content",
      },
      attachTo: document.body,
    });
    // Teleport moves content to body, so check document.body
    expect(document.body.textContent).toContain("Modal content");
  });

  it("renders with title prop", () => {
    wrapper = mount(AppModal, {
      props: {
        open: true,
        title: "Modal Title",
      },
      slots: {
        default: "Modal content",
      },
      attachTo: document.body,
    });
    expect(document.body.textContent).toContain("Modal Title");
  });

  it("emits close event when overlay is clicked", async () => {
    wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: "Modal content",
      },
      attachTo: document.body,
    });
    // The overlay is the outer div with fixed inset
    const overlay = document.querySelector(".fixed.inset-0");
    if (overlay) {
      overlay.dispatchEvent(new MouseEvent("click"));
    }
    expect(wrapper.emitted("close")).toBeTruthy();
  });

  it("emits close event on Escape key press", async () => {
    wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: "Modal content",
      },
      attachTo: document.body,
    });

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(wrapper.emitted("close")).toBeTruthy();
  });

  it("renders footer slot when provided", () => {
    wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: "Modal content",
        footer: "<button>Footer Button</button>",
      },
      attachTo: document.body,
    });
    expect(document.body.textContent).toContain("Footer Button");
  });
});
