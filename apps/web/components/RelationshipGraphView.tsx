"use client";

import React, { useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { InvestigationGraph, GraphNode } from "@/lib/api";
import { Shield, ExternalLink, Globe, Link2, Sparkles } from "lucide-react";

interface RelationshipGraphViewProps {
  graph: InvestigationGraph;
}

export function RelationshipGraphView({ graph }: RelationshipGraphViewProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Compute circular or force layout positions for nodes
  const { nodes, edges } = useMemo(() => {
    const rfNodes: Node[] = [];
    const rfEdges: Edge[] = [];

    const totalNodes = graph.nodes.length;
    const centerNode = graph.nodes.find((n) => n.type === "query_target") || graph.nodes[0];
    const profileNodes = graph.nodes.filter((n) => n.id !== centerNode?.id);

    // Place Center Target
    if (centerNode) {
      rfNodes.push({
        id: centerNode.id,
        position: { x: 400, y: 300 },
        data: {
          label: (
            <div className="px-4 py-3 bg-gradient-to-br from-emerald-950 to-slate-900 border-2 border-emerald-500 rounded-2xl shadow-glow text-center min-w-[140px]">
              <div className="w-8 h-8 mx-auto mb-1.5 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Shield className="w-4 h-4" />
              </div>
              <div className="text-xs font-bold text-white font-mono">{centerNode.label}</div>
              <div className="text-[10px] text-emerald-400 font-mono tracking-wider uppercase mt-0.5">Target Identifier</div>
            </div>
          ),
          raw: centerNode,
        },
      });
    }

    // Place surrounding nodes in circle
    const radius = Math.max(220, profileNodes.length * 28);
    profileNodes.forEach((node, index) => {
      const angle = (index / profileNodes.length) * 2 * Math.PI;
      const x = 400 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);

      rfNodes.push({
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <div className="px-3 py-2 bg-slate-900/95 border border-slate-700 hover:border-emerald-400/80 rounded-xl shadow-lg transition-all text-left min-w-[150px] cursor-pointer group">
              <div className="flex items-center justify-between gap-1.5 mb-1">
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  {node.platform || "Platform"}
                </span>
                <span className="text-[10px] text-emerald-400 font-mono">
                  {Math.round((node.confidence_existence || 0.8) * 100)}%
                </span>
              </div>
              <div className="text-xs font-semibold text-white truncate group-hover:text-emerald-400">
                {node.label}
              </div>
            </div>
          ),
          raw: node,
        },
      });
    });

    // Edges
    graph.edges.forEach((edge) => {
      const strokeColor =
        edge.confidence_tier === "verified"
          ? "#10b981"
          : edge.confidence_tier === "strongly_supported"
          ? "#14b8a6"
          : "#64748b";

      rfEdges.push({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: edge.confidence_tier === "verified",
        label: edge.relationship_type.replace(/_/g, " "),
        labelStyle: { fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" },
        labelBgStyle: { fill: "#0f172a", fillOpacity: 0.9, rx: 4, ry: 4 },
        style: { stroke: strokeColor, strokeWidth: edge.confidence_tier === "verified" ? 2.5 : 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: strokeColor,
          width: 12,
          height: 12,
        },
      });
    });

    return { nodes: rfNodes, edges: rfEdges };
  }, [graph]);

  return (
    <div className="relative w-full h-[650px] bg-slate-950/90 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => setSelectedNode(node.data.raw as GraphNode)}
        fitView
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="bg-slate-900 border-slate-800 text-slate-300 fill-slate-300" />
        <MiniMap
          nodeColor={() => "#10b981"}
          maskColor="rgba(8, 12, 22, 0.7)"
          className="bg-slate-900 border-slate-800 rounded-lg overflow-hidden"
        />
      </ReactFlow>

      {/* Edge Legend */}
      <div className="absolute top-4 left-4 p-3 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl shadow-lg text-[11px] font-mono space-y-1.5 pointer-events-none">
        <div className="font-semibold text-slate-300 uppercase tracking-wider mb-1">Relationship Evidence</div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span className="text-slate-300">Verified (Cross-Link / Domain)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-teal-400" />
          <span className="text-slate-300">Strongly Supported (Handle match)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
          <span className="text-slate-400">Possible Association</span>
        </div>
      </div>

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <div className="absolute top-4 right-4 w-80 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-2xl animate-in slide-in-from-right duration-200">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
            <span className="text-xs font-mono uppercase tracking-wider text-emerald-400">
              {selectedNode.type === "query_target" ? "Target Node" : "Discovered Account"}
            </span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-xs text-slate-500 hover:text-white"
            >
              ✕
            </button>
          </div>

          <h4 className="font-bold text-white text-sm mb-1">{selectedNode.label}</h4>
          {selectedNode.platform && (
            <p className="text-xs text-slate-400 mb-3">Platform: {selectedNode.platform}</p>
          )}

          <div className="space-y-2 text-xs font-mono mb-4">
            <div className="flex justify-between p-2 bg-slate-950/80 rounded-lg">
              <span className="text-slate-400">Existence:</span>
              <span className="text-emerald-400 font-bold">
                {Math.round((selectedNode.confidence_existence || 0.8) * 100)}%
              </span>
            </div>
            <div className="flex justify-between p-2 bg-slate-950/80 rounded-lg">
              <span className="text-slate-400">Data Reliability:</span>
              <span className="text-cyan-400 font-bold">
                {Math.round((selectedNode.confidence_data || 0.7) * 100)}%
              </span>
            </div>
          </div>

          {selectedNode.profile_url && (
            <a
              href={selectedNode.profile_url}
              target="_blank"
              rel="noreferrer"
              className="w-full py-2 px-3 text-xs font-semibold rounded-xl text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-colors flex items-center justify-center gap-1.5"
            >
              Visit Profile <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}

