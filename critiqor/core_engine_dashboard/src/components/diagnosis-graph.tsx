import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Expand } from "lucide-react";

export type GraphData = {
  nodes: { id: string; label: string; kind?: string }[];
  edges: { id: string; source: string; target: string; label?: string }[];
};

function kindColor(kind?: string) {
  switch (kind) {
    case "input":
      return "hsl(220 90% 56%)";
    case "agent":
      return "hsl(260 70% 55%)";
    case "tool":
      return "hsl(30 90% 55%)";
    case "judge":
      return "hsl(180 70% 40%)";
    case "violation":
      return "hsl(0 75% 55%)";
    default:
      return "hsl(220 10% 40%)";
  }
}

function Inner({ data }: { data: GraphData }) {
  const rf = useReactFlow();
  const wrapRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const nodes: Node[] = useMemo(
    () =>
      data.nodes.map((n, i) => ({
        id: n.id,
        position: { x: (i % 3) * 220, y: Math.floor(i / 3) * 140 },
        data: { label: n.label, kind: n.kind },
        style: {
          padding: 10,
          borderRadius: 10,
          border: `2px solid ${kindColor(n.kind)}`,
          background: hovered === n.id || selected === n.id ? kindColor(n.kind) : "var(--card)",
          color: hovered === n.id || selected === n.id ? "white" : "var(--foreground)",
          fontSize: 12,
          minWidth: 140,
          textAlign: "center" as const,
          transition: "all 150ms ease",
          boxShadow: hovered === n.id ? "0 6px 20px rgba(0,0,0,.15)" : "none",
          transform: hovered === n.id ? "translateY(-2px)" : "none",
        },
      })),
    [data.nodes, hovered, selected],
  );

  const edges: Edge[] = useMemo(
    () =>
      data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: hovered === e.source || hovered === e.target,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: "var(--muted-foreground)" },
      })),
    [data.edges, hovered],
  );

  const onNodeMouseEnter: NodeMouseHandler = useCallback((_, n) => setHovered(n.id), []);
  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => setHovered(null), []);
  const onNodeClick: NodeMouseHandler = useCallback(
    (_, n) => setSelected((s) => (s === n.id ? null : n.id)),
    [],
  );

  const fullscreen = () => {
    const el = wrapRef.current;
    if (!el) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else el.requestFullscreen?.();
  };

  const reset = () => {
    setSelected(null);
    setHovered(null);
    rf.setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 300 });
  };

  const selectedNode = data.nodes.find((n) => n.id === selected);

  return (
    <div
      ref={wrapRef}
      className="relative h-[480px] w-full rounded-lg border bg-card overflow-hidden"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        onNodeClick={onNodeClick}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} />
        <Controls showInteractive={false} className="!hidden" />
      </ReactFlow>

      <div className="absolute top-2 right-2 flex gap-1 bg-background/90 backdrop-blur border rounded-md p-1 shadow-sm">
        <Button
          size="icon"
          variant="ghost"
          onClick={() => rf.zoomIn({ duration: 200 })}
          title="Zoom in"
        >
          <ZoomIn className="size-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          onClick={() => rf.zoomOut({ duration: 200 })}
          title="Zoom out"
        >
          <ZoomOut className="size-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          onClick={() => rf.fitView({ duration: 300, padding: 0.2 })}
          title="Fit view"
        >
          <Maximize2 className="size-4" />
        </Button>
        <Button size="icon" variant="ghost" onClick={reset} title="Reset view">
          <RotateCcw className="size-4" />
        </Button>
        <Button size="icon" variant="ghost" onClick={fullscreen} title="Fullscreen">
          <Expand className="size-4" />
        </Button>
      </div>

      {selectedNode && (
        <div className="absolute bottom-2 left-2 right-2 md:right-auto md:max-w-sm bg-background/95 backdrop-blur border rounded-md p-3 shadow-md">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            {selectedNode.kind ?? "node"}
          </div>
          <div className="font-medium">{selectedNode.label}</div>
          <div className="text-xs text-muted-foreground mt-1">ID: {selectedNode.id}</div>
        </div>
      )}
    </div>
  );
}

export function DiagnosisGraph({ data }: { data: GraphData }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) {
    return (
      <div className="h-[480px] w-full rounded-lg border bg-card grid place-items-center text-sm text-muted-foreground">
        Loading graph…
      </div>
    );
  }
  return (
    <ReactFlowProvider>
      <Inner data={data} />
    </ReactFlowProvider>
  );
}
