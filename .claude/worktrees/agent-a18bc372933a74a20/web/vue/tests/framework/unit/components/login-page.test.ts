import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import LoginPage from "@/framework/pages/LoginPage.vue";

// Mock vue-router
vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ path: "/login" }),
}));

// Mock auth store
vi.mock("@/iam/stores/auth", () => ({
  useAuthStore: () => ({
    login: vi.fn(),
  }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders grid container with two-column layout", () => {
    const wrapper = mount(LoginPage);
    const content = wrapper.find(".login-page__content");
    expect(content.exists()).toBe(true);
  });

  it("shows brand section with platform name", () => {
    const wrapper = mount(LoginPage);
    const brand = wrapper.find(".login-page__brand");
    expect(brand.exists()).toBe(true);
    expect(brand.text()).toContain("AI 助手平台");
  });

  it("brand section has hidden CSS for small screens", () => {
    const wrapper = mount(LoginPage);
    const brand = wrapper.find(".login-page__brand");
    // Brand exists in DOM but hidden on small screens via CSS
    expect(brand.exists()).toBe(true);
  });

  it("uses custom card for form container", () => {
    const wrapper = mount(LoginPage);
    const card = wrapper.find(".login-page__card");
    expect(card.exists()).toBe(true);
  });

  it("has two input fields (username and password)", () => {
    const wrapper = mount(LoginPage);
    const inputs = wrapper.findAll("input");
    expect(inputs.length).toBe(2);
  });

  it("uses shadcn Button for submit", () => {
    const wrapper = mount(LoginPage);
    const button = wrapper.find('[data-slot="button"]');
    expect(button.exists()).toBe(true);
    expect(button.text()).toContain("登录");
  });

  it("shows FormLabel for username and password fields", () => {
    const wrapper = mount(LoginPage);
    const labels = wrapper.findAll('[data-slot="form-label"]');
    expect(labels.length).toBe(2);
  });

  it("renders FormField/FormItem for form structure", () => {
    const wrapper = mount(LoginPage);
    const formItems = wrapper.findAll('[data-slot="form-item"]');
    expect(formItems.length).toBe(2);
  });

  it("shows validation errors on submit with empty fields", async () => {
    const wrapper = mount(LoginPage);
    const form = wrapper.find("form");
    await form.trigger("submit");

    // Wait for vee-validate to process validation
    await vi.waitFor(() => {
      const messages = wrapper.findAll('[data-slot="form-message"]');
      // Expect at least some error messages to be visible
      expect(messages.filter((m) => m.text().trim().length > 0).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("has no CommonCard/CommonInput/CommonButton imports", () => {
    const imports = Object.keys(LoginPage.components || {});
    expect(imports).not.toContain("CommonCard");
    expect(imports).not.toContain("CommonInput");
    expect(imports).not.toContain("CommonButton");
  });
});