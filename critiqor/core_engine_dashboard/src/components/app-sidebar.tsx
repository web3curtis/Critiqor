import { Link, useRouterState } from "@tanstack/react-router";
import { useState } from "react";
import {
  BookOpen,
  ChevronDown,
  Eye,
  FileSearch,
  Github,
  Globe2,
  LayoutDashboard,
  Palette,
  PlayCircle,
  Stethoscope,
  Wrench,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import logo from "@/assets/critiqor-logo.png";
import { useCritiqor } from "@/lib/critiqor-store";

const groups = [
  {
    title: "Overview",
    items: [{ title: "Overview", url: "/", icon: LayoutDashboard }],
  },
  {
    title: "Workspace",
    items: [
      { title: "Runs", url: "/runs", icon: PlayCircle },
      { title: "Diagnosis", url: "/diagnoses", icon: Stethoscope },
      { title: "Playbook", url: "/playbook", icon: Wrench },
    ],
  },
  {
    title: "Settings",
    items: [
      { title: "Evidence Explorer", url: "/evidence", icon: FileSearch },
      { title: "Visibility", url: "/settings", icon: Eye },
      { title: "Appearance", url: "/appearance", icon: Palette },
    ],
  },
] as const;

function NavigationGroup({ group, runId }: { group: (typeof groups)[number]; runId?: string }) {
  const [open, setOpen] = useState(true);
  const pathname = useRouterState({ select: (router) => router.location.pathname });
  const active = (url: string) => (url === "/" ? pathname === "/" : pathname.startsWith(url));
  const search = runId ? ({ run_id: runId } as never) : undefined;
  return (
    <SidebarGroup className="py-1 group-data-[collapsible=icon]:px-0">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between rounded-md px-2 py-1 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-sidebar-foreground/55 hover:bg-sidebar-accent hover:text-sidebar-foreground group-data-[collapsible=icon]:hidden"
        aria-expanded={open}
      >
        <span>{group.title}</span>
        <ChevronDown className={`size-3.5 transition-transform ${open ? "" : "-rotate-90"}`} />
      </button>
      {open && (
        <SidebarGroupContent className="mt-1">
          <SidebarMenu>
            {group.items.map((item) => (
              <SidebarMenuItem key={`${group.title}-${item.title}`}>
                <SidebarMenuButton
                  asChild
                  isActive={active(item.url)}
                  tooltip={item.title}
                  className="h-9 rounded-lg transition-colors hover:bg-sidebar-accent data-[active=true]:bg-primary data-[active=true]:text-primary-foreground group-data-[collapsible=icon]:mx-auto"
                >
                  <Link to={item.url} search={search}>
                    <item.icon className="size-4" />
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      )}
    </SidebarGroup>
  );
}

export function AppSidebar() {
  const runId = useCritiqor((state) => state.executive.runId);
  const search = runId ? ({ run_id: runId } as never) : undefined;
  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border/70">
      <SidebarHeader className="px-3 py-4 group-data-[collapsible=icon]:p-2">
        <Link
          to="/"
          search={search}
          className="flex items-center gap-2.5 rounded-lg p-1 hover:bg-sidebar-accent"
        >
          <img
            src={logo}
            alt="Critiqor"
            className="size-10 shrink-0 scale-110 rounded-lg border border-sidebar-border bg-black object-cover group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:scale-100"
          />
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <div className="font-semibold tracking-tight leading-tight">Critiqor</div>
            <div className="text-[10px] uppercase tracking-widest text-sidebar-foreground/50">
              Runtime evaluation
            </div>
          </div>
        </Link>
      </SidebarHeader>
      <SidebarContent className="px-2 group-data-[collapsible=icon]:px-1">
        {groups.map((group) => (
          <NavigationGroup key={group.title} group={group} runId={runId} />
        ))}
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border/70 p-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Documentation" className="h-9 rounded-lg">
              <a
                href="https://critiqor-71f5274a.mintlify.site/introduction"
                target="_blank"
                rel="noreferrer"
              >
                <BookOpen className="size-4" />
                <span>Documentation</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Website" className="h-9 rounded-lg">
              <a
                href="https://critiqor-runtime-insight.vercel.app/"
                target="_blank"
                rel="noreferrer"
              >
                <Globe2 className="size-4" />
                <span>Website</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Repository" className="h-9 rounded-lg">
              <a href="https://github.com/web3curtis/Critiqor" target="_blank" rel="noreferrer">
                <Github className="size-4" />
                <span>Repo</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
