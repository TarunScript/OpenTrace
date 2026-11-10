"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { History, Search, Trash2, ArrowRight, Shield, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { api, InvestigationSummary } from "@/lib/api";
import { formatTimeAgo } from "@/lib/utils";

export default function HistoryPage() {
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterQuery, setFilterQuery] = useState("");

  const loadHistory = async () => {
    try {
      const data = await api.listInvestigations();
      setInvestigations(data);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this investigation?")) return;

    try {
      await api.deleteInvestigation(id);
      setInvestigations((prev) => prev.filter((inv) => inv.id !== id));
    } catch (err: any) {
      alert("Failed to delete: " + err.message);
    }
  };

  const filtered = investigations.filter((inv) =>
    inv.target_value.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-card-border/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-emerald-400" />
            <h1 className="text-2xl font-bold text-white font-mono">Investigation History</h1>
          </div>
          <p className="text-xs text-slate-400">
            Audit logs and previous digital footprint searches conducted in this environment
          </p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter by target..."
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-56 font-mono"
          />
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400 text-sm">
          <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Loading audit logs...
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-16 text-center bg-slate-900/40 border border-slate-800 rounded-2xl">
          <Shield className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">No Investigations Found</h3>
          <p className="text-xs text-slate-400 mb-4 max-w-sm mx-auto">
            Run your first footprint intelligence query from the search console.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-colors"
          >
            Start Investigation
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((inv) => (
            <Link
              key={inv.id}
              href={`/investigation/${inv.id}`}
              className="p-4 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-emerald-500/50 rounded-2xl shadow-md transition-all flex items-center justify-between gap-4 group"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 font-mono font-bold">
                  @
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-white font-mono text-sm group-hover:text-emerald-400 transition-colors">
                      @{inv.target_value}
                    </h3>
                    <span
                      className={`text-[10px] uppercase font-mono px-2 py-0.2 rounded-full border ${
                        inv.status === "completed"
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                          : inv.status === "searching"
                          ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                          : "bg-slate-500/10 border-slate-500/30 text-slate-400"
                      }`}
                    >
                      {inv.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400 font-mono mt-1">
                    <span>{inv.verified_count} verified profiles</span>
                    <span>•</span>
                    <span>{inv.total_sites_checked} sites checked</span>
                    <span>•</span>
                    <span>{formatTimeAgo(inv.created_at)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={(e) => handleDelete(inv.id, e)}
                  className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                  title="Delete Investigation"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-emerald-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

