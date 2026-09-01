import { createFileRoute } from "@tanstack/react-router";
import { Laptop, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/page-shell";
import { Card, CardContent } from "@/components/ui/card";
import { applyTheme, savedTheme, type ThemeMode } from "@/lib/theme";

export const Route = createFileRoute("/appearance")({
  head: () => ({ meta: [{ title: "Appearance — Critiqor" }] }),
  component: AppearancePage,
});

const options = [
  { id: "system", label: "System", detail: "Follow your operating system.", icon: Laptop },
  {
    id: "light",
    label: "Light",
    detail: "Bright surfaces with dark high-contrast text.",
    icon: Sun,
  },
  { id: "dark", label: "Dark", detail: "Low-glare surfaces with soft-white text.", icon: Moon },
] as const;

function AppearancePage() {
  const [mode, setMode] = useState<ThemeMode>("system");
  useEffect(() => setMode(savedTheme()), []);
  const select = (next: ThemeMode) => {
    setMode(next);
    applyTheme(next);
  };
  return (
    <PageShell title="Appearance" description="Choose how Critiqor looks on this device.">
      <div className="grid gap-4 md:grid-cols-3">
        {options.map((option) => (
          <button key={option.id} onClick={() => select(option.id)} className="text-left">
            <Card
              className={`h-full transition-all hover:border-primary/50 ${mode === option.id ? "border-primary ring-2 ring-primary/15" : ""}`}
            >
              <CardContent className="p-5">
                <div
                  className={`grid size-10 place-items-center rounded-lg ${mode === option.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                >
                  <option.icon className="size-5" />
                </div>
                <h2 className="mt-4 font-semibold">{option.label}</h2>
                <p className="mt-1 text-sm text-muted-foreground">{option.detail}</p>
              </CardContent>
            </Card>
          </button>
        ))}
      </div>
    </PageShell>
  );
}
