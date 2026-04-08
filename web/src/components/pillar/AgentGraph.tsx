"use client";

import { useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  Node,
  Edge,
  Position,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { GraphStructureResponse } from "@/lib/types";

interface AgentGraphProps {
  graph: GraphStructureResponse;
  activeNode?: string | null;
  visitedNodes?: string[];
  routeDecision?: string | null;
}

// Layout for the 11-node topology. Two parallel ingestion lanes (CV top,
// JD bottom) converge at the matching pipeline.
const nodePositions: Record<string, { x: number; y: number }> = {
  // CV lane (top)
  parse_cv: { x: 20, y: 20 },
  chunk_cv: { x: 200, y: 20 },
  embed_cv_chunks: { x: 380, y: 20 },
  // JD lane (bottom)
  parse_jd: { x: 20, y: 160 },
  extract_requirements: { x: 200, y: 160 },
  // Matching pipeline (converged)
  retrieve_evidence: { x: 560, y: 90 },
  score_match: { x: 740, y: 90 },
  route_candidate: { x: 920, y: 90 },
  // Branches
  screen_candidate: { x: 1100, y: 20 },
  reject_candidate: { x: 1100, y: 180 },
  generate_outreach: { x: 1280, y: 20 },
  __end__: { x: 1460, y: 100 },
};

// Tool → border colour mapping. Lets the graph teach which tool each node uses.
const toolBorders: Record<string, string> = {
  regex: "#22d3ee", // cyan
  embedding: "#a78bfa", // purple
  vector_search: "#f59e0b", // amber
  llm: "#3b82f6", // blue
  logic: "#94a3b8", // slate
};

export function AgentGraph({ graph, activeNode, visitedNodes = [], routeDecision }: AgentGraphProps) {
  const initialNodes = useMemo<Node[]>(() => {
    return graph.nodes.map((n) => {
      const visited = visitedNodes.includes(n.id);
      const active = activeNode === n.id;
      // Tool is now part of the node payload (added in the refactor)
      const tool = (n as { tool?: string }).tool;

      let bg = "#1e293b";
      let border = (tool && toolBorders[tool]) || "#334155";
      let text = "#e2e8f0";

      if (active) {
        bg = "#3b82f6";
        border = "#60a5fa";
        text = "#ffffff";
      } else if (visited) {
        bg = "#1e3a5f";
      }

      const label = tool ? `${n.label}\n(${tool})` : n.label;

      return {
        id: n.id,
        type: "default",
        position: nodePositions[n.id] || { x: 0, y: 0 },
        data: { label },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          background: bg,
          color: text,
          border: `2px solid ${border}`,
          borderRadius: 8,
          padding: 8,
          fontSize: 11,
          fontWeight: 600,
          minWidth: 140,
          textAlign: "center" as const,
          transition: "all 0.3s ease",
          whiteSpace: "pre-line" as const,
        },
      };
    });
  }, [graph.nodes, activeNode, visitedNodes]);

  const initialEdges = useMemo<Edge[]>(() => {
    return graph.edges.map((e, i) => {
      const fromVisited = visitedNodes.includes(e.source);
      const toVisited = visitedNodes.includes(e.target);
      const traversed = fromVisited && toVisited;

      // Highlight the routing decision branch
      let isActiveRoute = false;
      if (e.source === "route_candidate" && routeDecision) {
        if (routeDecision === "screen" || routeDecision === "review") {
          isActiveRoute = e.target === "screen_candidate";
        } else if (routeDecision === "reject") {
          isActiveRoute = e.target === "reject_candidate";
        }
      }

      const colour = traversed || isActiveRoute ? "#3b82f6" : "#334155";

      return {
        id: `${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        label: e.label || undefined,
        animated: traversed,
        style: { stroke: colour, strokeWidth: traversed ? 2.5 : 1.5 },
        labelStyle: { fontSize: 10, fill: "#94a3b8" },
        markerEnd: { type: MarkerType.ArrowClosed, color: colour },
      };
    });
  }, [graph.edges, visitedNodes, routeDecision]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  return (
    <div style={{ width: "100%", height: 420 }} className="rounded-lg border border-border bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background color="#334155" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
