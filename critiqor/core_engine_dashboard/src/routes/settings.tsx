import { createFileRoute } from "@tanstack/react-router";
import { EyeOff, Globe, Lock, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { PageShell } from "@/components/page-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Visibility — Critiqor" }] }),
  component: SettingsPage,
});

const options = [
  {
    id: "private",
    label: "Private",
    detail: "Requires an access token in the terminal.",
    icon: Lock,
  },
  {
    id: "shared",
    label: "Shared",
    detail: "Requires an invite code from the run owner.",
    icon: Users,
  },
  {
    id: "anonymous",
    label: "Anonymous",
    detail: "Does not attach user information to shared evaluation data.",
    icon: EyeOff,
  },
  {
    id: "public",
    label: "Public",
    detail: "Anyone with the URL can access the published evaluation.",
    icon: Globe,
  },
] as const;

function SettingsPage() {
  const [visibility, setVisibility] = useState<(typeof options)[number]["id"]>("private");
  const [inviteCode, setInviteCode] = useState("");
  useEffect(() => {
    const credential = sessionStorage.getItem("critiqor_access_credential") || "";
    fetch("/api/access", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ credential }),
    })
      .then(async (response) =>
        response.ok ? response.json() : fetch("/api/access").then((item) => item.json()),
      )
      .then((data) => {
        setVisibility(data.visibility);
        setInviteCode(data.inviteCode || "");
      });
  }, []);
  const select = (id: typeof visibility) => {
    toast.info(`Run critiqor config to switch to ${id} and relaunch the dashboard.`);
  };
  return (
    <PageShell
      title="Visibility"
      description="Control who can access runtime evaluations and identifying information."
    >
      <div className="grid gap-4 md:grid-cols-2">
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => select(option.id)}
            className="text-left"
            aria-pressed={visibility === option.id}
          >
            <Card
              className={`h-full transition-all hover:border-primary/50 ${visibility === option.id ? "border-primary ring-2 ring-primary/15" : ""}`}
            >
              <CardContent className="flex gap-4 p-5">
                <div
                  className={`grid size-10 shrink-0 place-items-center rounded-lg ${visibility === option.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                >
                  <option.icon className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold">{option.label}</h2>
                    {visibility === option.id && <Badge>Selected</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{option.detail}</p>
                </div>
              </CardContent>
            </Card>
          </button>
        ))}
      </div>
      <Card>
        <CardContent className="p-5">
          <h2 className="font-bold">Active dashboard visibility</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Configured in <code>critiqor config</code>. Relaunch the dashboard after changing it.
          </p>
          <div className="mt-4 rounded-lg border bg-muted p-3 font-mono text-sm">
            {visibility === "shared"
              ? `Invite code: ${inviteCode || "Authenticate to reveal"}`
              : visibility === "private"
                ? "A new access token was generated for this launch."
                : `${visibility[0].toUpperCase()}${visibility.slice(1)} access requires no code.`}
          </div>
        </CardContent>
      </Card>
    </PageShell>
  );
}
