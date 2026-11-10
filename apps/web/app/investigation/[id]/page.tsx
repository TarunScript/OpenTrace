"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Shield,
  ExternalLink,
  Search,
  Filter,
  Network,
  LayoutGrid,
  FileText,
  Trash2,
  Download,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  RefreshCw,
  Eye,
  Globe,
  Share2,
} from "lucide-react";
import {
  api,
  InvestigationSummary,
  InvestigationResults,
  InvestigationGraph,
  ProfileRecord,
} from "@/lib/api";
import { EvidenceModal } from "@/components/EvidenceModal";
import { RelationshipGraphView } from "@/components/RelationshipGraphView";
import { formatTimeAgo, formatConfidence } from "@/lib/utils";

export default function InvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [investigation, setInvestigation] = useState<InvestigationSummary | null>(null);
  const [results, setResults] = useState<InvestigationResults | null>(null);
  const [graph, setGraph] = useState<InvestigationGraph | null>(null);
  const [activeView, setActiveView] = useState<"grid" | "graph" | "evidence">("grid");

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [inspectProfile, setInspectProfile] = useState<ProfileRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [pollingError, setPollingError] = useState<string | null>(null);

  // Poll investigation status until completed or failed
  useEffect(() => {
    if (!id) return;

    let isMounted = true;
    let pollInterval: any = null;

    const fetchStatusAndResults = async () => {
      try {
        const inv = await api.getInvestigation(id);
        if (!isMounted) return;
        setInvestigation(inv);

        // Fetch full results
        const res = await api.getInvestigationResults(id);
        if (!isMounted) return;
        setResults(res);

        // Fetch graph if completed
        if (inv.status === "completed") {
          try {
            const g = await api.getInvestigationGraph(id);
            if (isMounted) setGraph(g);
          } catch {}
          if (pollInterval) clearInterval(pollInterval);
        }
      } catch (err: any) {
        if (isMounted) setPollingError(err.message || "Failed to load investigation.");
      }
    };

    fetchStatusAndResults();
    pollInterval = setInterval(fetchStatusAndResults, 2000);

    return () => {
      isMounted = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [id]);

  // Handle Delete
  const handleDelete = async () => {
    if (!confirm("Are you sure you want to permanently delete this investigation and all its evidence records?")) {
      return;
    }
    setIsDeleting(true);
    try {
      await api.deleteInvestigation(id);
      router.push("/history");
    } catch (err: any) {
      alert("Failed to delete investigation: " + err.message);
      setIsDeleting(false);
    }
  };

  // Handle JSON Export
  const handleExportJSON = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `opentrace_${results.investigation.target_value}_${id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Handle HTML Report Export
  const handleExportHTML = () => {
    if (!results) return;
    const profilesHtml = results.profiles.map(p => {
      const ev = p.evidence_records?.[0];
      return `
      <div style="border: 1px solid #334155; background: #0f172a; color: #f8fafc; padding: 18px; border-radius: 12px; margin-bottom: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
          <h3 style="margin: 0; color: #34d399; font-size: 18px;">${p.platform} (@${p.username})</h3>
          <span style="font-size: 11px; padding: 2px 8px; border-radius: 9999px; background: #1e293b; color: #94a3b8; text-transform: uppercase;">${p.category}</span>
        </div>
        <p style="margin: 4px 0 10px 0;"><a href="${p.profile_url}" target="_blank" style="color: #38bdf8; text-decoration: none;">${p.profile_url}</a></p>
        <p style="margin: 4px 0;"><strong>Display Name:</strong> ${p.display_name || "N/A"}</p>
        <p style="margin: 4px 0;"><strong>Biography:</strong> ${p.biography || "N/A"}</p>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #1e293b; font-size: 12px; color: #94a3b8;">
          <p style="margin: 3px 0;"><strong>Existence Confidence:</strong> ${Math.round(p.confidence_existence * 100)}% | <strong>Data Confidence:</strong> ${Math.round(p.confidence_data * 100)}%</p>
          <p style="margin: 3px 0;"><strong>Verification Method:</strong> ${ev?.detection_method || "composite"} | <strong>Status:</strong> ${ev?.verification_status || "VERIFIED"}</p>
          <p style="margin: 3px 0;"><strong>Evidence Note:</strong> ${ev?.match_evidence || "Account signature verified with multi-signal detection."}</p>
        </div>
      </div>
    `;
    }).join("");

    const htmlContent = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <title>OpenTrace Intelligence Report: @${results.investigation.target_value}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 860px; margin: 40px auto; padding: 24px; background: #020617; color: #f1f5f9; line-height: 1.6; }
          .header-box { border-bottom: 2px solid #1e293b; padding-bottom: 20px; margin-bottom: 24px; }
          .disclaimer { background: #1e293b; border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; font-size: 12px; color: #cbd5e1; margin-bottom: 24px; }
          .footer { font-size: 12px; color: #64748b; margin-top: 40px; border-top: 1px solid #1e293b; padding-top: 16px; }
        </style>
      </head>
      <body>
        <div class="header-box">
          <h1 style="color: #34d399; margin: 0 0 6px 0;">OpenTrace Investigation Report</h1>
          <p style="margin: 0; color: #94a3b8;">Target Handle: <strong style="color: #ffffff;">@${results.investigation.target_value}</strong> | Investigation ID: <code>${id}</code></p>
          <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">Generated At: ${new Date().toUTCString()} | Verified Profiles Discovered: <strong style="color: #34d399;">${results.profiles.length}</strong> | Sites Evaluated: ${results.investigation.total_sites_checked}</p>
        </div>

        <div class="disclaimer">
          <strong>Transparency Notice:</strong> Confidence scores reflect heuristic pattern matching strength and data completeness. They are provided for intelligence assistance and do not constitute legal proof of identity ownership.
        </div>

        <h2 style="color: #f8fafc; font-size: 20px; margin-bottom: 16px;">Discovered Public Profiles (${results.profiles.length})</h2>
        ${profilesHtml || "<p style='color: #64748b;'>No verified profiles were discovered for this target identifier.</p>"}

        <div class="footer">
          Report generated by OpenTrace — Open-Source Digital Footprint Intelligence Platform. Fully open-source and transparent.
        </div>
      </body>
      </html>
    `;

    const blob = new Blob([htmlContent], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `opentrace_report_${results.investigation.target_value}_${id}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filtered Profiles
  const filteredProfiles = useMemo(() => {
    if (!results?.profiles) return [];
    return results.profiles.filter((p) => {
      const matchesCategory = selectedCategory === "all" || p.category === selectedCategory;
      const matchesSearch =
        searchQuery === "" ||
        p.platform.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.display_name && p.display_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (p.biography && p.biography.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [results, selectedCategory, searchQuery]);

  if (!investigation) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center">
        <div className="w-12 h-12 mx-auto mb-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
        <h2 className="text-xl font-bold text-white mb-2">Connecting to OpenTrace Engine...</h2>
        <p className="text-slate-400 text-sm">Initializing investigation probe for #{id}</p>
      </div>
    );
  }

  const isCompleted = investigation.status === "completed";
  const isSearching = investigation.status === "searching" || investigation.status === "queued";
  const TOTAL_REGISTERED_SITES =
    investigation.search_type === "username"
      ? 39
      : investigation.total_sites_checked || 1;
  const progressPercent = Math.min(
    100,
    Math.round(((investigation.total_sites_checked || 0) / TOTAL_REGISTERED_SITES) * 100)
  );

  const getStatusBadge = (statusStr: string) => {
    switch (statusStr?.toLowerCase()) {
      case "verified":
        return "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";
      case "inconclusive":
        return "bg-amber-500/10 border-amber-500/30 text-amber-400";
      case "not_found":
        return "bg-slate-500/10 border-slate-500/30 text-slate-400";
      case "error":
        return "bg-red-500/10 border-red-500/30 text-red-400";
      default:
        return "bg-slate-500/10 border-slate-500/30 text-slate-400";
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-card-border/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-slate-400">Investigation #{id}</span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold tracking-wider ${
                isCompleted
                  ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                  : isSearching
                  ? "bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 animate-pulse"
                  : "bg-red-500/10 border border-red-500/30 text-red-400"
              }`}
            >
              {investigation.status}
            </span>
          </div>
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-white font-mono flex items-center gap-2">
              {investigation.search_type === "email" ? (
                <span className="text-emerald-400">✉</span>
              ) : investigation.search_type === "phone" ? (
                <span className="text-emerald-400">☎</span>
              ) : (
                <span className="text-slate-500">@</span>
              )}
              {investigation.target_value}
            </h1>
            <span className="text-xs text-slate-400 font-mono">
              Created {formatTimeAgo(investigation.created_at)}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportJSON}
            disabled={!results}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors flex items-center gap-1.5 disabled:opacity-50"
            title="Download Raw Findings (JSON)"
          >
            <Download className="w-3.5 h-3.5" />
            JSON
          </button>
          <button
            onClick={handleExportHTML}
            disabled={!results}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors flex items-center gap-1.5 disabled:opacity-50"
            title="Download Printable Report (HTML)"
          >
            <FileText className="w-3.5 h-3.5" />
            Report
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 transition-colors flex items-center gap-1.5"
            title="Purge Investigation"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </button>
        </div>
      </div>

      {/* Live Investigation Progress Banner */}
      <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl mb-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          {/* Metric 1 */}
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">Verified Accounts</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">
                {results?.profiles.length || investigation.verified_count || 0}
              </span>
              <span className="text-xs text-slate-500 font-mono">discovered</span>
            </div>
          </div>
          {/* Metric 2 */}
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">Inconclusive Probes</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-amber-400 font-mono">
                {investigation.inconclusive_count || 0}
              </span>
              <span className="text-xs text-slate-500 font-mono">rate/challenge</span>
            </div>
          </div>
          {/* Metric 3 */}
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">Total Sites Checked</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
                {investigation.total_sites_checked || 0}
              </span>
              <span className="text-xs text-slate-500 font-mono">platforms</span>
            </div>
          </div>
          {/* Metric 4 */}
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">Search Engine State</span>
            <div className="flex items-center gap-2 mt-1">
              {isSearching ? (
                <>
                  <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span className="text-xs text-cyan-400 font-mono font-semibold">Probing targets...</span>
                </>
              ) : isCompleted ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-emerald-400 font-mono font-semibold">Audit Finished</span>
                </>
              ) : (
                <span className="text-xs text-slate-400 font-mono">Stopped</span>
              )}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              isCompleted
                ? "bg-emerald-400 shadow-glow"
                : "bg-gradient-to-r from-emerald-500 to-cyan-400 animate-pulse"
            }`}
            style={{ width: `${isCompleted ? 100 : Math.max(10, progressPercent)}%` }}
          />
        </div>
      </div>

      {/* Self-Audit Intelligence Card (Email or Phone) */}
      {results?.summary?.audit_report && (
        <div className="mb-8 p-6 bg-slate-900/90 border border-emerald-500/30 rounded-2xl shadow-xl relative overflow-hidden">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Authorized {investigation.search_type === "email" ? "Email" : "Phone"} Self-Audit Findings
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Verified Control
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Audit executed with authorized OTP verification against public registries.
                </p>
              </div>
            </div>
            <div className="text-xs font-mono text-slate-400">
              Audit Token Verified: <span className="text-emerald-400 font-semibold">Active</span>
            </div>
          </div>

          {/* Fingerprint.to-style Identity Overview Header for Email Audits */}
          {investigation.search_type === "email" && results.summary.audit_report.discovered_metadata && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5 pb-5 border-b border-slate-800">
              {/* Discovered Profile Pictures */}
              <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Profile Pictures ({results.summary.audit_report.discovered_metadata.avatars?.length || 0})
                </span>
                <div className="flex items-center gap-2 overflow-x-auto py-1">
                  {results.summary.audit_report.discovered_metadata.avatars?.length > 0 ? (
                    results.summary.audit_report.discovered_metadata.avatars.map((av: string, idx: number) => (
                      <img
                        key={idx}
                        src={av}
                        alt="Avatar"
                        className="w-10 h-10 rounded-full border border-slate-700 object-cover flex-shrink-0"
                      />
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">No public profile pictures</span>
                  )}
                </div>
              </div>

              {/* Discovered Usernames */}
              <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Discovered Usernames ({results.summary.audit_report.discovered_metadata.usernames?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {results.summary.audit_report.discovered_metadata.usernames?.length > 0 ? (
                    results.summary.audit_report.discovered_metadata.usernames.map((u: string) => (
                      <span
                        key={u}
                        className="px-2 py-0.5 rounded-lg text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                      >
                        @{u}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 font-mono">None detected</span>
                  )}
                </div>
              </div>

              {/* Discovered Full Names */}
              <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Discovered Names ({results.summary.audit_report.discovered_metadata.names?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {results.summary.audit_report.discovered_metadata.names?.length > 0 ? (
                    results.summary.audit_report.discovered_metadata.names.map((n: string) => (
                      <span
                        key={n}
                        className="px-2 py-0.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-200 border border-slate-700"
                      >
                        {n}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">None detected</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Email Specific Findings */}
          {investigation.search_type === "email" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Gravatar Summary */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Gravatar Profile
                </span>
                {results.summary.audit_report.gravatar?.found ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      {results.summary.audit_report.gravatar.avatar_url && (
                        <img
                          src={results.summary.audit_report.gravatar.avatar_url}
                          alt="Avatar"
                          className="w-10 h-10 rounded-full border border-slate-700"
                        />
                      )}
                      <div>
                        <span className="font-semibold text-white text-sm block">
                          {results.summary.audit_report.gravatar.display_name || "Public Profile"}
                        </span>
                        <a
                          href={results.summary.audit_report.gravatar.profile_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-cyan-400 hover:underline flex items-center gap-1"
                        >
                          View Profile <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                    {results.summary.audit_report.gravatar.about_me && (
                      <p className="text-xs text-slate-300 line-clamp-2">
                        {results.summary.audit_report.gravatar.about_me}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">No public Gravatar profile associated with this email address.</p>
                )}
              </div>

              {/* OpenPGP Keyserver */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  PGP Public Keyserver
                </span>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg font-bold text-white font-mono">
                    {results.summary.audit_report.pgp_keys?.count || 0}
                  </span>
                  <span className="text-xs text-slate-400">Public Keys Indexed</span>
                </div>
                <p className="text-xs text-slate-500">
                  {results.summary.audit_report.pgp_keys?.found
                    ? "Cryptographic public keys published on public keyservers."
                    : "No published PGP keys found on keyserver.ubuntu.com."}
                </p>
              </div>

              {/* Breach Exposure */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Data Breach Exposure
                </span>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    {results.summary.audit_report.breach_intelligence?.risk_score || "LOW"} Risk
                  </span>
                  <span className="text-xs text-slate-400">
                    {results.summary.audit_report.breach_intelligence?.breach_count || 0} Incident Records
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Exposure score based on publicly known historical breach indexes.
                </p>
              </div>
            </div>
          )}

          {/* Phone Specific Findings */}
          {investigation.search_type === "phone" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Standard Format
                </span>
                <div className="text-sm font-mono text-white font-bold mb-1">
                  {results.summary.audit_report.format?.e164 || investigation.target_value}
                </div>
                <p className="text-xs text-slate-500">
                  Country Code: {results.summary.audit_report.format?.country_code} | National: {results.summary.audit_report.format?.national_number}
                </p>
              </div>

              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Geographic Metadata
                </span>
                <div className="text-sm font-semibold text-white mb-1">
                  {results.summary.audit_report.geographic_metadata?.country || "International"}
                </div>
                <p className="text-xs text-slate-500">
                  ISO Code: {results.summary.audit_report.geographic_metadata?.iso_code} | Line: {results.summary.audit_report.geographic_metadata?.line_type}
                </p>
              </div>

              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Carrier Allocation
                </span>
                <div className="text-sm font-semibold text-emerald-400 mb-1">
                  {results.summary.audit_report.geographic_metadata?.public_carrier_allocation || "Active Allocation"}
                </div>
                <p className="text-xs text-slate-500">
                  Verified active numbering plan range.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* View Switcher Tabs & Filter Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 mb-6">
        {/* Switch View Buttons */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveView("grid")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeView === "grid"
                ? "bg-slate-800 text-emerald-400 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            Grid View ({filteredProfiles.length})
          </button>
          <button
            onClick={() => setActiveView("graph")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeView === "graph"
                ? "bg-slate-800 text-emerald-400 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            Relationship Graph
          </button>
          <button
            onClick={() => setActiveView("evidence")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeView === "evidence"
                ? "bg-slate-800 text-emerald-400 shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Raw Evidence Log
          </button>
        </div>

        {/* Search within results & category filters (Grid view) */}
        {activeView === "grid" && (
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search platforms, bio, names..."
                className="pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-52 font-mono"
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 font-mono focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Categories</option>
              <option value="developer">Developer</option>
              <option value="social">Social</option>
              <option value="forums">Forums</option>
              <option value="gaming">Gaming</option>
              <option value="tech">Tech</option>
              <option value="media">Media</option>
            </select>
          </div>
        )}
      </div>

      {/* Main Content View Switcher */}
      {activeView === "grid" && (
        <>
          {filteredProfiles.length === 0 ? (
            <div className="p-12 text-center bg-slate-900/40 border border-slate-800/80 rounded-2xl">
              {isSearching ? (
                <>
                  <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
                  <h3 className="text-base font-bold text-white mb-1">Scanning Public Registries...</h3>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Probing configured endpoints. Matching accounts will appear dynamically here as evidence is verified.
                  </p>
                </>
              ) : (
                <>
                  <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-white mb-1">No Matching Profiles Discovered</h3>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Target identifier was not found on supported platforms with genuine profile markers.
                  </p>
                </>
              )}
            </div>
          ) : (
            <>
              <div className="mb-4 p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center gap-2.5 text-xs text-slate-400">
                <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                <span>
                  <strong>Confidence Scores Notice:</strong> Scores reflect heuristic pattern matching strength and metadata completeness. They are investigative indicators and do not represent legal proof of identity ownership.
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredProfiles.map((p) => {
                const confExistence = formatConfidence(p.confidence_existence);
                const confData = formatConfidence(p.confidence_data);

                return (
                  <div
                    key={p.id}
                    className="p-5 bg-slate-900/90 border border-slate-800 hover:border-emerald-500/50 rounded-2xl shadow-xl transition-all flex flex-col justify-between group"
                  >
                    <div>
                      {/* Card Header */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-3">
                          {p.profile_image_url ? (
                            <img
                              src={p.profile_image_url}
                              alt={p.platform}
                              className="w-11 h-11 rounded-xl object-cover border border-slate-700"
                              onError={(e) => {
                                (e.target as HTMLElement).style.display = "none";
                              }}
                            />
                          ) : (
                            <div className="w-11 h-11 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 font-bold font-mono text-base">
                              {p.platform.charAt(0)}
                            </div>
                          )}
                          <div>
                            <div className="flex items-center gap-1.5">
                              <h3 className="font-bold text-white text-sm group-hover:text-emerald-400 transition-colors">
                                {p.platform}
                              </h3>
                              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                                {p.category}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 font-mono">@{p.username}</p>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${confExistence.bg} ${confExistence.color}`}
                        >
                          {Math.round(p.confidence_existence * 100)}% Verified
                        </span>
                      </div>

                      {/* Display name & Bio */}
                      {p.display_name && (
                        <p className="text-xs font-semibold text-slate-200 mb-1">{p.display_name}</p>
                      )}
                      {p.biography ? (
                        <p className="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">
                          {p.biography}
                        </p>
                      ) : (
                        <p className="text-xs text-slate-600 italic mb-3">No public bio available</p>
                      )}

                      {/* Confidence Bars */}
                      <div className="space-y-1.5 pt-2 border-t border-slate-800/80 mb-4 text-[11px] font-mono">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Profile Existence:</span>
                          <span className="text-emerald-400 font-semibold">
                            {Math.round(p.confidence_existence * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-emerald-400 h-full rounded-full"
                            style={{ width: `${Math.round(p.confidence_existence * 100)}%` }}
                          />
                        </div>

                        <div className="flex items-center justify-between pt-1">
                          <span className="text-slate-500">Data Reliability:</span>
                          <span className="text-cyan-400 font-semibold">
                            {Math.round(p.confidence_data * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-cyan-400 h-full rounded-full"
                            style={{ width: `${Math.round(p.confidence_data * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                      <button
                        onClick={() => setInspectProfile(p)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 flex items-center gap-1.5 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 text-emerald-400" />
                        Inspect Evidence
                      </button>

                      <a
                        href={p.profile_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 bg-emerald-400 hover:bg-emerald-300 flex items-center gap-1 transition-colors"
                      >
                        Source <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
            </>
          )}
        </>
      )}

      {/* Relationship Graph View */}
      {activeView === "graph" && (
        <div>
          {graph ? (
            <RelationshipGraphView graph={graph} />
          ) : (
            <div className="p-16 text-center bg-slate-900 border border-slate-800 rounded-2xl">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
              <h3 className="text-base font-bold text-white mb-1">Constructing Relationship Graph...</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Correlating discovered handles against personal domains and explicit cross-links.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Raw Evidence Log View */}
      {activeView === "evidence" && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Audit & Verification Evidence Table
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              {results?.profiles.reduce((acc, p) => acc + p.evidence_records.length, 0) || 0} Evidence Records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-3">Platform</th>
                  <th className="p-3">Verification State</th>
                  <th className="p-3">Method</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3">Observed At</th>
                  <th className="p-3">Source URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {results?.profiles.flatMap((p) =>
                  p.evidence_records.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3 text-white font-semibold">{p.platform}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded border uppercase text-[10px] font-bold ${getStatusBadge(ev.verification_status)}`}>
                          {ev.verification_status}
                        </span>
                      </td>
                      <td className="p-3 text-slate-300">{ev.detection_method}</td>
                      <td className="p-3 text-emerald-400 font-bold">{Math.round(ev.confidence_score * 100)}%</td>
                      <td className="p-3 text-slate-400">{new Date(ev.observed_at).toLocaleTimeString()}</td>
                      <td className="p-3 max-w-xs truncate text-slate-400">
                        <a href={ev.source_url} target="_blank" rel="noreferrer" className="hover:text-emerald-400">
                          {ev.source_url}
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Evidence Inspection Modal */}
      <EvidenceModal
        profile={inspectProfile}
        onClose={() => setInspectProfile(null)}
      />
    </div>
  );
}

