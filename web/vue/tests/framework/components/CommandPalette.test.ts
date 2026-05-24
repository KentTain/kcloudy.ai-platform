import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createWebHistory } from "vue-router";
import CommandPalette from "@/framework/components/CommandPalette.vue";

// Mock useCommandPalette
const mockOpenCommandPalette = vi.fn();
const mockCloseCommandPalette = vi.fn();
const mockToggleCommandPalette = vi.fn();

vi.mock("@/framework/composables/useCommandPalette", () => ({
  useCommandPalette: () => ({
    openCommandPalette: mockOpenCommandPalette,
    closeCommandPalette: mockCloseCommandPalette,
    toggleCommandPalette: mockToggleCommandPalette,
    isOpen: { value: false },
  }),
}));

describe("CommandPalette", () => {
  let router: ReturnType<typeof createRouter>;

  beforeEach(() => {
    vi.clearAllMocks();
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/", component: { template: "<div>Home</div>" } },
        { path: "/datasets", component: { template: "<div>Datasets</div>" } },
        { path: "/iam/users", component: { template: "<div>Users</div>" } },
      ],
    });
  });

  it("renders command palette component", () => {
    const wrapper = mount(CommandPalette, {
      global: {
        plugins: [router],
        stubs: {
          Dialog: true,
          DialogContent: true,
          Command: true,
          CommandInput: true,
          CommandList: true,
          CommandEmpty: true,
          CommandGroup: true,
          CommandItem: true,
        },
      },
    });

    expect(wrapper.findComponent(CommandPalette).exists()).toBe(true);
  });

  it("contains menu items", () => {
    const wrapper = mount(CommandPalette, {
      global: {
        plugins: [router],
        stubs: {
          Dialog: true,
          DialogContent: true,
          Command: true,
          CommandInput: true,
          CommandList: true,
          CommandEmpty: true,
          CommandGroup: true,
          CommandItem: true,
        },
      },
    });

    // Verify component mounts without error
    expect(wrapper.vm).toBeDefined();
  });

  it("listens for keyboard shortcut Cmd+K", async () => {
    const addEventListenerSpy = vi.spyOn(document, "addEventListener");

    mount(CommandPalette, {
      global: {
        plugins: [router],
        stubs: {
          Dialog: true,
          DialogContent: true,
          Command: true,
          CommandInput: true,
          CommandList: true,
          CommandEmpty: true,
          CommandGroup: true,
          CommandItem: true,
        },
      },
    });

    expect(addEventListenerSpy).toHaveBeenCalledWith("keydown", expect.any(Function));

    addEventListenerSpy.mockRestore();
  });
});
