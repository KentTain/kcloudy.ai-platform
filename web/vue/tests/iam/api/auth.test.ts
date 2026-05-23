import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  login,
  logout,
  refreshToken,
  getCurrentUser,
  updateCurrentUser,
  changePassword,
  getLoginHistory,
} from "@/iam/api/auth";
import * as client from "@/framework/api/client";

// Mock the API client
vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
}));

describe("Auth API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("login", () => {
    it("calls POST /v1/iam/auth/login with credentials", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          access_token: "token",
          refresh_token: "refresh",
          expires_in: 3600,
          token_type: "Bearer",
        },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await login({ account: "admin", password: "password" });

      expect(client.post).toHaveBeenCalledWith("/v1/iam/auth/login", {
        account: "admin",
        password: "password",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("logout", () => {
    it("calls POST /v1/iam/auth/logout", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await logout();

      expect(client.post).toHaveBeenCalledWith("/v1/iam/auth/logout");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("refreshToken", () => {
    it("calls POST /v1/iam/auth/token/refresh with refresh token", async () => {
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
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await refreshToken("old-refresh-token");

      expect(client.post).toHaveBeenCalledWith("/v1/iam/auth/token/refresh", {
        refresh_token: "old-refresh-token",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getCurrentUser", () => {
    it("calls GET /v1/iam/user/me", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          username: "admin",
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getCurrentUser();

      expect(client.get).toHaveBeenCalledWith("/v1/iam/user/me");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateCurrentUser", () => {
    it("calls PUT /v1/iam/user/me with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          username: "admin",
          nickname: "Admin User",
          email: "admin@example.com",
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await updateCurrentUser({
        nickname: "Admin User",
        email: "admin@example.com",
      });

      expect(client.put).toHaveBeenCalledWith("/v1/iam/user/me", {
        nickname: "Admin User",
        email: "admin@example.com",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("changePassword", () => {
    it("calls PUT /v1/iam/user/password with passwords", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await changePassword("old-pass", "new-pass");

      expect(client.put).toHaveBeenCalledWith("/v1/iam/user/password", {
        old_password: "old-pass",
        new_password: "new-pass",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getLoginHistory", () => {
    it("calls GET /v1/iam/auth/login-history with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          items: [
            {
              id: "1",
              user_id: "1",
              login_at: "2024-01-01T00:00:00Z",
              ip_address: "127.0.0.1",
              status: "success",
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getLoginHistory({ page: 1, page_size: 20 });

      expect(client.get).toHaveBeenCalledWith("/v1/iam/auth/login-history", {
        page: 1,
        page_size: 20,
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
