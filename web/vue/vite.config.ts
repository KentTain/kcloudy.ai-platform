import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_API_TARGET || "http://127.0.0.1:8080";

  return {
    plugins: [tailwindcss(), vue()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
      extensions: [".js", ".ts", ".vue"],
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        // 业务模块 API 代理
        "/tenant": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/iam": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/ai": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/demo": {
          target: apiTarget,
          changeOrigin: true,
        },
        // 其他代理规则
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
        "/admin/v1": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/console": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/health": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
