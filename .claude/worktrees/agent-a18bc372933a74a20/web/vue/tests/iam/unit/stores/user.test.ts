import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useUserStore } from "@/iam/stores/user";
import * as userApi from "@/iam/api/user";

vi.mock("@/iam/api/user", () => ({
  getUsers: vi.fn(),
  getUser: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  disableUser: vi.fn(),
  enableUser: vi.fn(),
  lockUser: vi.fn(),
}));

describe("User Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetchUsers", () => {
    it("fetches user list and sets users", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          items: [
            { id: "1", username: "admin", status: "active", created_at: "2024-01-01" },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      };
      vi.mocked(userApi.getUsers).mockResolvedValue(mockResponse);

      const store = useUserStore();
      await store.fetchUsers({ page: 1 });

      expect(userApi.getUsers).toHaveBeenCalledWith({ page: 1 });
      expect(store.users).toEqual(mockResponse.data.items);
      expect(store.total).toBe(1);
    });
  });

  describe("fetchUser", () => {
    it("fetches single user and sets currentUser", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "admin", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(userApi.getUser).mockResolvedValue(mockResponse);

      const store = useUserStore();
      await store.fetchUser("1");

      expect(userApi.getUser).toHaveBeenCalledWith("1");
      expect(store.currentUser).toEqual(mockResponse.data);
    });
  });

  describe("addUser", () => {
    it("creates user and returns new user", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "newuser", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(userApi.createUser).mockResolvedValue(mockResponse);

      const store = useUserStore();
      const result = await store.addUser({ username: "newuser", password: "password" });

      expect(userApi.createUser).toHaveBeenCalledWith({ username: "newuser", password: "password" });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe("editUser", () => {
    it("updates user", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "admin", nickname: "Admin", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(userApi.updateUser).mockResolvedValue(mockResponse);

      const store = useUserStore();
      await store.editUser("1", { nickname: "Admin" });

      expect(userApi.updateUser).toHaveBeenCalledWith("1", { nickname: "Admin" });
    });
  });

  describe("removeUser", () => {
    it("deletes user", async () => {
      vi.mocked(userApi.deleteUser).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useUserStore();
      await store.removeUser("1");

      expect(userApi.deleteUser).toHaveBeenCalledWith("1");
    });
  });

  describe("changeUserStatus", () => {
    it("enables user", async () => {
      vi.mocked(userApi.enableUser).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useUserStore();
      store.users = [{ id: "1", username: "admin", status: "inactive" as const, created_at: "2024-01-01" }];
      await store.changeUserStatus("1", "enable");

      expect(userApi.enableUser).toHaveBeenCalledWith("1");
    });

    it("disables user", async () => {
      vi.mocked(userApi.disableUser).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useUserStore();
      store.users = [{ id: "1", username: "admin", status: "active" as const, created_at: "2024-01-01" }];
      await store.changeUserStatus("1", "disable");

      expect(userApi.disableUser).toHaveBeenCalledWith("1");
    });

    it("locks user", async () => {
      vi.mocked(userApi.lockUser).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useUserStore();
      store.users = [{ id: "1", username: "admin", status: "active" as const, created_at: "2024-01-01" }];
      await store.changeUserStatus("1", "lock");

      expect(userApi.lockUser).toHaveBeenCalledWith("1");
    });
  });
});
