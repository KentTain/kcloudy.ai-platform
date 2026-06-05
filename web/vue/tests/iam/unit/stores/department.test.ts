import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useDepartmentStore } from "@/iam/stores/department";
import * as departmentApi from "@/iam/api/department";

vi.mock("@/iam/api/department", () => ({
  getDepartments: vi.fn(),
  getDepartmentTree: vi.fn(),
  getDepartment: vi.fn(),
  createDepartment: vi.fn(),
  updateDepartment: vi.fn(),
  deleteDepartment: vi.fn(),
  getDepartmentUsers: vi.fn(),
  addDepartmentUser: vi.fn(),
  removeDepartmentUser: vi.fn(),
  setDepartmentLeader: vi.fn(),
}));

describe("Department Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetchDepartmentTree", () => {
    it("fetches department tree", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          {
            id: "1",
            tenant_id: "tenant-1",
            name: "总公司",
            sort_order: 0,
            status: "active",
            created_at: "2024-01-01",
            children: [],
          },
        ],
      };
      vi.mocked(departmentApi.getDepartmentTree).mockResolvedValue(mockResponse);

      const store = useDepartmentStore();
      await store.fetchDepartmentTree();

      expect(departmentApi.getDepartmentTree).toHaveBeenCalled();
      expect(store.departmentTree).toEqual(mockResponse.data);
    });
  });

  describe("fetchUsers", () => {
    it("fetches department users", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          { id: "1", username: "user1", status: "active", created_at: "2024-01-01" },
        ],
      };
      vi.mocked(departmentApi.getDepartmentUsers).mockResolvedValue(mockResponse);

      const store = useDepartmentStore();
      await store.fetchUsers("1");

      expect(departmentApi.getDepartmentUsers).toHaveBeenCalledWith("1");
      expect(store.departmentUsers).toEqual(mockResponse.data);
    });
  });

  describe("addDepartment", () => {
    it("creates department", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          tenant_id: "tenant-1",
          name: "研发部",
          sort_order: 0,
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(departmentApi.createDepartment).mockResolvedValue(mockResponse);
      vi.mocked(departmentApi.getDepartmentTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useDepartmentStore();
      await store.addDepartment({ name: "研发部" });

      expect(departmentApi.createDepartment).toHaveBeenCalledWith({ name: "研发部" });
    });
  });

  describe("editDepartment", () => {
    it("updates department", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          tenant_id: "tenant-1",
          name: "研发一部",
          sort_order: 0,
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(departmentApi.updateDepartment).mockResolvedValue(mockResponse);
      vi.mocked(departmentApi.getDepartmentTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useDepartmentStore();
      await store.editDepartment("1", { name: "研发一部" });

      expect(departmentApi.updateDepartment).toHaveBeenCalledWith("1", { name: "研发一部" });
    });
  });

  describe("removeDepartment", () => {
    it("deletes department", async () => {
      vi.mocked(departmentApi.deleteDepartment).mockResolvedValue({ code: 0, msg: "success", data: undefined });
      vi.mocked(departmentApi.getDepartmentTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useDepartmentStore();
      await store.removeDepartment("1");

      expect(departmentApi.deleteDepartment).toHaveBeenCalledWith("1");
    });
  });

  describe("updateLeader", () => {
    it("updates department leader", async () => {
      vi.mocked(departmentApi.setDepartmentLeader).mockResolvedValue({ code: 0, msg: "success", data: undefined });
      vi.mocked(departmentApi.getDepartmentTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useDepartmentStore();
      await store.updateLeader("1", "user-1");

      expect(departmentApi.setDepartmentLeader).toHaveBeenCalledWith("1", "user-1");
    });
  });
});
