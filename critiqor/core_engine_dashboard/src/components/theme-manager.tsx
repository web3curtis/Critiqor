import { useEffect } from "react";
import { applyTheme, savedTheme } from "@/lib/theme";

export function ThemeManager() {
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => applyTheme(savedTheme());
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return null;
}
