export type ApiTestStatus = "idle" | "loading" | "success" | "error";

export interface ApiTestResult {
  status: ApiTestStatus;
  data: unknown;
  error: string | null;
  duration: number | null;
}
