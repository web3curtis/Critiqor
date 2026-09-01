import { useEffect, useState } from "react";
import { Copy, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const currentVersion = "0.2.17";

const newerThan = (next: string, current: string) => {
  const left = next.split(".").map(Number);
  const right = current.split(".").map(Number);
  return left.some(
    (value, index) =>
      value > (right[index] ?? 0) && left.slice(0, index).every((part, i) => part === right[i]),
  );
};

export function UpdateNotice() {
  const [latest, setLatest] = useState<string>();
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    fetch("https://pypi.org/pypi/critiqor/json")
      .then((response) => response.json())
      .then((payload) => {
        const version = String(payload?.info?.version ?? "");
        if (version && newerThan(version, currentVersion)) setLatest(version);
      })
      .catch(() => undefined);
  }, []);
  if (!latest || dismissed) return null;
  const update = async () => {
    await navigator.clipboard.writeText("python3 -m pip install --upgrade critiqor");
    toast.success("Update command copied. Run it in your terminal, then restart Critiqor.");
  };
  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-sm">
      <span className="font-medium">Critiqor {latest} is available.</span>
      <Button size="sm" variant="outline" onClick={update}>
        <Copy className="size-3.5" />
        Update Now
      </Button>
      <button
        className="ml-auto rounded p-1 hover:bg-amber-500/10"
        onClick={() => setDismissed(true)}
        aria-label="Dismiss update"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}
