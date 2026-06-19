import { useColorMode as useColorModeCore } from "@vueuse/core";

export type ThemeMode = "light" | "dark" | "auto";

/**
 * 主题切换组合式函数
 * 基于 @vueuse/core 的 useColorMode 封装
 * 支持 light / dark / auto 三种模式
 *
 * 与 Tailwind CSS dark mode 兼容：
 * - light 模式：html 元素无 dark class
 * - dark 模式：html 元素有 dark class
 *
 * @see https://vueuse.org/core/usecolormode/
 */
export function useColorMode() {
  const mode = useColorModeCore({
    selector: "html",
    attribute: "class",
    modes: {
      // light 模式不添加任何 class，Tailwind 会使用默认的 light 样式
      light: "",
      // dark 模式添加 'dark' class，触发 Tailwind dark: 变体
      dark: "dark",
      // auto 模式使用系统偏好，@vueuse/core 会自动处理
      auto: "auto",
    },
    initialValue: "light",
    storageKey: "theme-mode",
  });

  const setTheme = (theme: ThemeMode) => {
    mode.value = theme;
  };

  const toggleTheme = () => {
    const next: ThemeMode = mode.value === "light" ? "dark" : "light";
    mode.value = next;
  };

  return {
    /** 当前主题模式 */
    theme: mode,
    /** 设置主题 */
    setTheme,
    /** 切换主题（亮/暗） */
    toggleTheme,
  };
}
