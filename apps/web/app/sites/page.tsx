"use client";

import React, { useState, useEffect } from "react";
import { Globe, Search, Filter, CheckCircle2, Shield, ExternalLink } from "lucide-react";
import { api, SupportedSite } from "@/lib/api";

export default function SitesPage() {
  const [sites, setSites] = useState<SupportedSite[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.listSites().then((data) => {
      setSites(data);
      setLoading(false);
    });
  }, []);

  const filtered = sites.filter((s) => {
    const matchesCat = selectedCategory === "all" || s.category === selectedCategory;
    const matchesQuery =
      query === "" ||
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.category.toLowerCase().includes(query.toLowerCase()) ||
      s.url_pattern.toLowerCase().includes(query.toLowerCase());
    return matchesCat && matchesQuery;
  });

  const categories = [
    { id: "all", label: "All" },
    { id: "developer", label: "Developer" },
    { id: "social", label: "Social" },
    { id: "forums", label: "Forums" },
    { id: "gaming", label: "Gaming" },
    { id: "tech", label: "Tech" },
    { id: "media", label: "Media" },
    { id: "blogging", label: "Blogging" },
    { id: "messaging", label: "Messaging" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-card-border/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Globe className="w-5 h-5 text-emerald-400" />
            <h1 className="text-2xl font-bold text-white font-mono">Supported Site Registry</h1>
          </div>
          <p className="text-xs text-slate-400">
            Curated list of public services with multi-signal detection definitions
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search platform by name, url..."
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-64 font-mono"
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex flex-wrap items-center gap-1.5 mb-8">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCategory(c.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
              selectedCategory === c.id
                ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 font-semibold"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400 text-sm">
          <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Loading curated registry...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((site) => (
            <div
              key={site.name}
              className="p-4 bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 rounded-2xl shadow transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-emerald-400 font-mono text-sm">
                      {site.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-sm">{site.name}</h3>
                      <span className="text-[10px] font-mono uppercase text-slate-500">{site.category}</span>
                    </div>
                  </div>
                  <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                    <CheckCircle2 className="w-3 h-3" />
                    Active
                  </span>
                </div>

                <div className="p-2.5 bg-slate-950/70 border border-slate-800/60 rounded-xl my-2 text-[11px] font-mono text-slate-400 truncate">
                  {site.url_pattern}
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
                <span>Method: {site.check_type}</span>
                <span className="text-emerald-500">SSRF Protected</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

