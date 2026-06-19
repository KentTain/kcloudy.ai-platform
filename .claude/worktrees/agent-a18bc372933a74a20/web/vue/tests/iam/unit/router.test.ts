import { describe, expect, it } from "vitest";
import { iamRoutes } from "@/iam/router";

describe("iamRoutes", () => {
  it("uses nested structure with iam parent path", () => {
    const iamRoot = iamRoutes.find((route) => route.path === "iam");
    expect(iamRoot).toBeDefined();
    expect(iamRoot?.children).toBeDefined();
    expect(iamRoot?.children?.some((route) => route.path === "users")).toBe(true);
  });

  it("exposes user management route", () => {
    const iamRoot = iamRoutes.find((route) => route.path === "iam");
    const userRoute = iamRoot?.children?.find((route) => route.path === "users");
    expect(userRoute).toBeDefined();
    expect(userRoute?.meta?.title).toBe("用户管理");
  });
});
