import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useOrganizationStore } from "@/iam/stores/organization";
import * as organizationApi from "@/iam/api/organization";

vi.mock("@/iam/api/organization", () => ({
  getOrganizations: vi.fn(),
  getOrganizationTree: vi.fn(),
  getOrganization: vi.fn(),
  createOrganization: vi.fn(),
  updateOrganization: vi.fn(),
  deleteOrganization: vi.fn(),
  getOrganizationUsers: vi.fn(),
  addOrganizationUser: vi.fn(),
  removeOrganizationUser: vi.fn(),
  setOrganizationLeader: vi.fn(),
}));

describe("Organization Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetchOrganizationTree", () => {
    it("fetches organization tree", async () => {
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
      vi.mocked(organizationApi.getOrganizationTree).mockResolvedValue(mockResponse);

      const store = useOrganizationStore();
      await store.fetchOrganizationTree();

      expect(organizationApi.getOrganizationTree).toHaveBeenCalled();
      expect(store.organizationTree).toEqual(mockResponse.data);
    });
  });

  describe("fetchUsers", () => {
    it("fetches organization users", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          { id: "1", username: "user1", status: "active", created_at: "2024-01-01" },
        ],
      };
      vi.mocked(organizationApi.getOrganizationUsers).mockResolvedValue(mockResponse);

      const store = useOrganizationStore();
      await store.fetchUsers("1");

      expect(organizationApi.getOrganizationUsers).toHaveBeenCalledWith("1");
      expect(store.organizationUsers).toEqual(mockResponse.data);
    });
  });

  describe("addOrganization", () => {
    it("creates organization", async () => {
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
      vi.mocked(organizationApi.createOrganization).mockResolvedValue(mockResponse);
      vi.mocked(organizationApi.getOrganizationTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useOrganizationStore();
      await store.addOrganization({ name: "研发部" });

      expect(organizationApi.createOrganization).toHaveBeenCalledWith({ name: "研发部" });
    });
  });

  describe("editOrganization", () => {
    it("updates organization", async () => {
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
      vi.mocked(organizationApi.updateOrganization).mockResolvedValue(mockResponse);
      vi.mocked(organizationApi.getOrganizationTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useOrganizationStore();
      await store.editOrganization("1", { name: "研发一部" });

      expect(organizationApi.updateOrganization).toHaveBeenCalledWith("1", { name: "研发一部" });
    });
  });

  describe("removeOrganization", () => {
    it("deletes organization", async () => {
      vi.mocked(organizationApi.deleteOrganization).mockResolvedValue({ code: 0, msg: "success", data: undefined });
      vi.mocked(organizationApi.getOrganizationTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useOrganizationStore();
      await store.removeOrganization("1");

      expect(organizationApi.deleteOrganization).toHaveBeenCalledWith("1");
    });
  });

  describe("updateLeader", () => {
    it("updates organization leader", async () => {
      vi.mocked(organizationApi.setOrganizationLeader).mockResolvedValue({ code: 0, msg: "success", data: undefined });
      vi.mocked(organizationApi.getOrganizationTree).mockResolvedValue({ code: 0, msg: "success", data: [] });

      const store = useOrganizationStore();
      await store.updateLeader("1", "user-1");

      expect(organizationApi.setOrganizationLeader).toHaveBeenCalledWith("1", "user-1");
    });
  });
});
