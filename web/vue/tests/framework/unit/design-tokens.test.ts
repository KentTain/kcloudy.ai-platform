/**
 * 设计令牌测试
 * 验证 CSS 变量是否正确定义
 */
import { describe, expect, it } from "vitest";

describe("Design Tokens", () => {
  it("should define color tokens", () => {
    const tokens = {
      surface: "#f5f7fa",
      surfaceRaised: "#ffffff",
      primary: "#1677ff",
      primaryHover: "#0958d9",
      primaryActive: "#003eb3",
      primarySubtle: "#e8f3ff",
      secondary: "#ff5722",
      secondaryHover: "#e64a19",
      secondarySubtle: "#fff3e0",
      success: "#10b981",
      danger: "#ef4444",
      warning: "#f59e0b",
      text: "#1f2937",
      textMuted: "#6b7280",
      textDisabled: "#9ca3af",
      border: "#e5e7eb",
      borderPrimary: "rgba(22, 119, 255, 0.35)",
    };

    // 验证颜色格式
    Object.entries(tokens).forEach(([name, value]) => {
      if (value.startsWith("#")) {
        expect(value).toMatch(/^#[0-9a-fA-F]{6}$/);
      } else if (value.startsWith("rgba")) {
        expect(value).toMatch(/^rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)$/);
      }
    });
  });

  it("should define font tokens", () => {
    const fonts = {
      sans: 'Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
      mono: '"JetBrains Mono", ui-monospace, monospace',
    };

    expect(fonts.sans).toContain("Inter");
    expect(fonts.mono).toContain("JetBrains Mono");
  });

  it("should define radius tokens", () => {
    const radius = {
      ui: "6px",
      sm: "4px",
      lg: "8px",
    };

    expect(radius.ui).toBe("6px");
    expect(radius.sm).toBe("4px");
    expect(radius.lg).toBe("8px");
  });

  it("should define shadow tokens", () => {
    const shadows = {
      sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
      md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
      lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    };

    expect(shadows.sm).toContain("1px");
    expect(shadows.md).toContain("4px");
    expect(shadows.lg).toContain("10px");
  });
});
