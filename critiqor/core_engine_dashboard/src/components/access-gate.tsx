import { useEffect, useState, type ReactNode } from "react";
import { LockKeyhole } from "lucide-react";

export function AccessGate({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<string>("");
  const [allowed, setAllowed] = useState(false);
  const [credential, setCredential] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    fetch("/api/access")
      .then((r) => r.json())
      .then((data) => {
        setMode(data.visibility);
        if (!data.requiresCredential) setAllowed(true);
        else if (sessionStorage.getItem("critiqor_access_credential"))
          verify(sessionStorage.getItem("critiqor_access_credential") || "");
      });
  }, []);
  const verify = async (value: string) => {
    const response = await fetch("/api/access", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ credential: value }),
    });
    if (!response.ok) {
      setError(mode === "shared" ? "Invalid invite code." : "Invalid access token.");
      return;
    }
    sessionStorage.setItem("critiqor_access_credential", value);
    setAllowed(true);
  };
  if (allowed) return <>{children}</>;
  if (!mode)
    return (
      <div className="grid min-h-screen place-items-center bg-background text-foreground">
        Loading access policy…
      </div>
    );
  return (
    <main className="grid min-h-screen place-items-center bg-background p-6 text-foreground">
      <form
        className="w-full max-w-md rounded-2xl border bg-card p-8 shadow-xl"
        onSubmit={(event) => {
          event.preventDefault();
          verify(credential);
        }}
      >
        <div className="mb-5 grid size-12 place-items-center rounded-xl bg-primary/15 text-primary">
          <LockKeyhole />
        </div>
        <h1 className="text-2xl font-bold">
          {mode === "shared" ? "Shared dashboard" : "Private dashboard"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter the {mode === "shared" ? "invite code" : "new access token"} printed by the Critiqor
          CLI for this launch.
        </p>
        <label className="mt-6 block text-sm font-semibold">
          {mode === "shared" ? "Invite code" : "Access token"}
        </label>
        <input
          autoFocus
          value={credential}
          onChange={(event) => setCredential(event.target.value)}
          className="mt-2 w-full rounded-lg border bg-background px-3 py-2.5 font-mono"
        />
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
        <button className="mt-5 w-full rounded-lg bg-primary px-4 py-2.5 font-semibold text-primary-foreground">
          Open dashboard
        </button>
      </form>
    </main>
  );
}
