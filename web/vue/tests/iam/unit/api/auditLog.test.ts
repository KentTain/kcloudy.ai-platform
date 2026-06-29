import { describe, expect, it, vi, beforeEach } from "vitest";
import { getAuditLogs, getAuditOptions } from "@/iam/api/auditLog";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
}));

describe("AuditLog API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getAuditLogs", () => {
    it("calls GET /iam/admin/v1/audit-logs with params", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: [],
        total: 0,
        page: 1,
        page_size: 20,
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getAuditLogs({ page: 1, page_size: 20 });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/audit-logs", {
        params: { page: 1, page_size: 20 },
      });
      expect(result).toEqual(mockResponse);
    });

    it("calls GET /iam/admin/v1/audit-logs with filter params", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: [],
        total: 0,
        page: 1,
        page_size: 20,
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getAuditLogs({
        page: 1,
        page_size: 20,
        business_domain: "user",
        operation_type: "user.user_create",
        resource_type: "user",
        time_range: "7d",
      });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/audit-logs", {
        params: {
          page: 1,
          page_size: 20,
          business_domain: "user",
          operation_type: "user.user_create",
          resource_type: "user",
          time_range: "7d",
        },
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getAuditOptions", () => {
    it("calls GET /iam/admin/v1/audit-logs/options", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: {
          business_domains: [
            { value: "user", label: "用户" },
          ],
          actions: [
            { value: "user.user_create", label: "用户创建" },
          ],
          resource_types: [
            { value: "user", label: "用户" },
          ],
        },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getAuditOptions();

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/audit-logs/options");
      expect(result).toEqual(mockResponse);
    });
  });
});
