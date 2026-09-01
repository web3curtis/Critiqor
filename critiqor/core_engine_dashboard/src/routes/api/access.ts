import { createFileRoute } from "@tanstack/react-router";
import { dashboardAccess } from "@/lib/api-auth.server";

export const Route = createFileRoute("/api/access")({
  server: {
    handlers: {
      GET: async () => {
        const access = dashboardAccess();
        return Response.json({
          visibility: access.visibility,
          requiresCredential: ["private", "shared"].includes(access.visibility),
        });
      },
      POST: async ({ request }) => {
        const access = dashboardAccess();
        const body = await request.json().catch(() => ({}));
        const supplied = String(body.credential || "");
        const ok =
          !["private", "shared"].includes(access.visibility) ||
          (!!access.credential && supplied === access.credential);
        return Response.json(
          {
            ok,
            visibility: access.visibility,
            ...(ok && access.visibility === "shared" ? { inviteCode: access.credential } : {}),
          },
          { status: ok ? 200 : 401 },
        );
      },
    },
  },
});
