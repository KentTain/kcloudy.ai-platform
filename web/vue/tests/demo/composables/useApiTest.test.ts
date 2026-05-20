// tests/demo/composables/useApiTest.test.ts
import { describe, expect, it, vi } from "vitest";
import { useApiTest } from "@/demo/composables/useApiTest";

describe("useApiTest", () => {
  it("initializes with idle status", () => {
    const { result } = useApiTest();
    expect(result.value.status).toBe("idle");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeNull();
  });

  it("sets status to success and captures data on successful execute", async () => {
    const mockFn = vi.fn().mockResolvedValue({ status: "ok" });
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.status).toBe("success");
    expect(result.value.data).toEqual({ status: "ok" });
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeGreaterThanOrEqual(0);
  });

  it("sets status to error and captures error message on failed execute", async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error("Network error"));
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.status).toBe("error");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBe("Network error");
    expect(result.value.duration).toBeGreaterThanOrEqual(0);
  });

  it("uses default error message for non-Error rejections", async () => {
    const mockFn = vi.fn().mockRejectedValue("string error");
    const { result, execute } = useApiTest(mockFn);

    await execute();

    expect(result.value.error).toBe("请求失败");
  });

  it("sets status to loading during execution", async () => {
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    const mockFn = vi.fn().mockReturnValue(promise);
    const { result, execute } = useApiTest(mockFn);

    const execPromise = execute();
    expect(result.value.status).toBe("loading");

    resolvePromise!({ ok: true });
    await execPromise;

    expect(result.value.status).toBe("success");
  });

  it("reset() returns result to idle state", async () => {
    const mockFn = vi.fn().mockResolvedValue({ ok: true });
    const { result, execute, reset } = useApiTest(mockFn);

    await execute();
    expect(result.value.status).toBe("success");

    reset();

    expect(result.value.status).toBe("idle");
    expect(result.value.data).toBeNull();
    expect(result.value.error).toBeNull();
    expect(result.value.duration).toBeNull();
  });
});
