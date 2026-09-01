export type ThemeMode = "system" | "light" | "dark";

const storageKey = "critiqor-theme";

export function applyTheme(mode: ThemeMode) {
  const dark =
    mode === "dark" ||
    (mode === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem(storageKey, mode);
}

export function savedTheme(): ThemeMode {
  const value = window.localStorage.getItem(storageKey);
  return value === "light" || value === "dark" ? value : "system";
}
