import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useAuthStore } from "@/iam/stores/auth";
import * as authApi from "@/iam/api/auth";
import { useUserStore } from "@/framework/stores";

vi.mock("@/iam/api/auth", () => ({
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  getCurrentUser: vi.fn(),
}));

vi.mock("@/framework/stores", () => ({
  useUserStore: vi.fn(),
}));

describe("Auth Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("login", () => {
    it("calls login API and stores token", async () => {
      const mockSetToken = vi.fn();
      const mockSetUserInfo = vi.fn();
      vi.mocked(useUserStore).mockReturnValue({
        setToken: mockSetToken,
        setUserInfo: mockSetUserInfo,
        userInfo: null,
      } as any);

      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          access_token: "test-token",
          refresh_token: "test-refresh",
          expires_in: 3600,
          token_type: "Bearer",
        },
      };
      vi.mocked(authApi.login).mockResolvedValue(mockResponse);

      vi.mocked(authApi.getCurrentUser).mockResolvedValue({
        code: 0,
        msg: "success",
        data: {
          id: "1",
          username: "admin",
          status: "active",
          created_at: "2024-01-01",
        },
      });

      const store = useAuthStore();
      await store.login({ account: "admin", password: "password" });

      expect(authApi.login).toHaveBeenCalledWith({
        account: "admin",
        password: "password",
      });
      expect(mockSetToken).toHaveBeenCalledWith("test-token");
    });
  });

  describe("logout", () => {
    it("calls logout API and clears state", async () => {
      const mockLogout = vi.fn();
      vi.mocked(useUserStore).mockReturnValue({
        logout: mockLogout,
        setToken: vi.fn(),
        setUserInfo: vi.fn(),
        userInfo: null,
      } as any);

      vi.mocked(authApi.logout).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useAuthStore();
      await store.logout();

      expect(authApi.logout).toHaveBeenCalled();
      expect(mockLogout).toHaveBeenCalled();
    });
  });

  describe("refreshToken", () => {
    it("calls refreshToken API and updates token", async () => {
      const mockSetToken = vi.fn();
      vi.mocked(useUserStore).mockReturnValue({
        setToken: mockSetToken,
        setUserInfo: vi.fn(),
        userInfo: null,
      } as any);

      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          access_token: "new-token",
          refresh_token: "new-refresh",
          expires_in: 3600,
          token_type: "Bearer",
        },
      };
      vi.mocked(authApi.refreshToken).mockResolvedValue(mockResponse);

      // Set refresh token in localStorage
      localStorage.setItem("refresh_token", "old-refresh");

      const store = useAuthStore();
      await store.refreshToken();

      expect(authApi.refreshToken).toHaveBeenCalledWith("old-refresh");
      expect(mockSetToken).toHaveBeenCalledWith("new-token");
    });
  });

  describe("isTokenExpired", () => {
    it("returns true when no token expires_at", () => {
      vi.mocked(useUserStore).mockReturnValue({
        setToken: vi.fn(),
        setUserInfo: vi.fn(),
        userInfo: null,
      } as any);

      const store = useAuthStore();
      expect(store.isTokenExpired).toBe(true);
    });

    it("returns true when token is expired", () => {
      vi.mocked(useUserStore).mockReturnValue({
        setToken: vi.fn(),
        setUserInfo: vi.fn(),
        userInfo: null,
      } as any);

      // Need to create a new store instance after setting localStorage
      localStorage.setItem("token_expires_at", String(Date.now() - 1000));
      setActivePinia(createPinia());

      const store = useAuthStore();
      expect(store.isTokenExpired).toBe(true);
    });

    it("returns false when token is not expired", () => {
      vi.mocked(useUserStore).mockReturnValue({
        setToken: vi.fn(),
        setUserInfo: vi.fn(),
        userInfo: null,
      } as any);

      localStorage.setItem("token_expires_at", String(Date.now() + 3600000));
      setActivePinia(createPinia());

      const store = useAuthStore();
      expect(store.isTokenExpired).toBe(false);
    });
  });
});
