"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Shield,
  Layers,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Lock,
  Network,
  Cpu,
  Database,
  ExternalLink,
  Mail,
  Phone,
  Info,
} from "lucide-react";
import { api, SupportedSite } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [searchTab, setSearchTab] = useState<"username" | "email" | "phone">("username");
  const [query, setQuery] = useState("");
  const [isDeepSearch, setIsDeepSearch] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [supportedSites, setSupportedSites] = useState<SupportedSite[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OTP Verification Challenge State for Email & Phone Self-Audits
  const [otpModalOpen, setOtpModalOpen] = useState(false);
  const [otpChallengeId, setOtpChallengeId] = useState("");
  const [otpTarget, setOtpTarget] = useState("");
  const [otpType, setOtpType] = useState<"email" | "phone">("email");
  const [devOtp, setDevOtp] = useState<string | undefined>(undefined);
  const [otpCode, setOtpCode] = useState("");
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpError, setOtpError] = useState<string | null>(null);

  useEffect(() => {
    api.listSites().then(setSupportedSites).catch(() => {});
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const clean = query.trim().replace(/^@/, "");
    if (!clean) return;

    setLoading(true);
    setError(null);

    // Auto-detect input type if user pastes an email or phone number in any tab
    let effectiveType: "username" | "email" | "phone" = searchTab;
    if (clean.includes("@")) {
      effectiveType = "email";
    } else if (/^\+?[0-9]{7,15}$/.test(clean.replace(/[\s\-\(\)]/g, ""))) {
      effectiveType = "phone";
    }

    try {
      const options: any = {
        deep_search: isDeepSearch,
        max_depth: isDeepSearch ? 2 : 1,
      };
      if (selectedCategory !== "all") {
        options.categories = [selectedCategory];
      }

      const inv = await api.createInvestigation(clean, effectiveType, options);
      router.push(`/investigation/${inv.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to initiate digital footprint investigation.");
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim()) return;

    setOtpVerifying(true);
    setOtpError(null);

    try {
      let report: any;
      if (otpType === "email") {
        report = await api.verifyEmailAudit(otpChallengeId, otpCode.trim());
      } else {
        report = await api.verifyPhoneAudit(otpChallengeId, otpCode.trim());
      }

      setOtpModalOpen(false);
      if (report.investigation_id) {
        router.push(`/investigation/${report.investigation_id}`);
      }
    } catch (err: any) {
      setOtpError(err.message || "Verification code is invalid or has expired.");
      setOtpVerifying(false);
    }
  };

  const categories = [
    { id: "all", label: "All Platforms" },
    { id: "developer", label: "Developer" },
    { id: "social", label: "Social" },
    { id: "forums", label: "Forums" },
    { id: "gaming", label: "Gaming" },
    { id: "tech", label: "Tech" },
    { id: "media", label: "Media" },
  ];

  const quickSearches = ["torvalds", "gvanrossum", "antirez", "mitchellh", "shadcn"];

  return (
    <div className="relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-radial-glow pointer-events-none" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[700px] bg-radial-glow-cyan pointer-events-none" />
      <div className="absolute inset-0 bg-cyber-grid opacity-30 pointer-events-none" />

      {/* Hero Section */}
      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 text-center">
        {/* Release Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-8 shadow-glow">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Curated Multi-Signal OSINT • {supportedSites.length || 24} High-Fidelity Platforms</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight sm:leading-none mb-6">
          Your Digital Footprint,{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            Transparently Discovered.
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-400 mb-10 leading-relaxed">
          OpenTrace empowers individuals and security researchers to audit publicly accessible online
          profiles with multi-dimensional confidence ratings and zero fabricated results.
        </p>

        {/* Search Input Box */}
        <div className="max-w-3xl mx-auto bg-slate-900/90 border border-slate-800 rounded-3xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl">
          {/* Tabs */}
          <div className="flex items-center justify-center gap-2 p-1.5 bg-slate-950/80 border border-slate-800/80 rounded-2xl mb-6 max-w-md mx-auto">
            <button
              type="button"
              onClick={() => { setSearchTab("username"); setError(null); }}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                searchTab === "username"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              Username
            </button>
            <button
              type="button"
              onClick={() => { setSearchTab("email"); setError(null); }}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                searchTab === "email"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Mail className="w-3.5 h-3.5" />
              Email Audit
            </button>
            <button
              type="button"
              onClick={() => { setSearchTab("phone"); setError(null); }}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                searchTab === "phone"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Phone className="w-3.5 h-3.5" />
              Phone Audit
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="relative flex items-center">
              <span className="absolute left-4 font-mono text-slate-500 text-lg font-bold">
                {searchTab === "username" ? "@" : searchTab === "email" ? "✉" : "☎"}
              </span>
              <input
                type="text"
                required
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  searchTab === "username"
                    ? "Enter target handle (e.g. torvalds, tarun.this.side, shadcn)..."
                    : searchTab === "email"
                    ? "Enter email address to audit (e.g. tarunmitblr@gmail.com)..."
                    : "Enter phone number (e.g. 9140598622 or +919140598622)..."
                }
                className="w-full pl-11 pr-36 py-4 bg-slate-950 border border-slate-700/80 rounded-2xl text-white placeholder-slate-500 text-base sm:text-lg focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 font-mono transition-all"
              />
              <button
                type="submit"
                disabled={loading}
                className="absolute right-2 px-5 py-2.5 rounded-xl text-sm font-bold text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-all flex items-center gap-2 shadow-glow disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    Probing...
                  </>
                ) : (
                  <>
                    Investigate
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Category Filter Chips & Deep Search Toggle */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-slate-500 font-mono mr-1">Filter:</span>
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`px-2.5 py-1 rounded-lg font-mono transition-colors ${
                      selectedCategory === cat.id
                        ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-300"
                        : "bg-slate-800/60 text-slate-400 hover:text-white border border-transparent"
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              <label className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-white select-none">
                <input
                  type="checkbox"
                  checked={isDeepSearch}
                  onChange={(e) => setIsDeepSearch(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-emerald-500"
                />
                <span className="font-mono text-xs flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  Deep Search (Depth 2)
                </span>
              </label>
            </div>
          </form>

          {/* Quick example tags */}
          <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
            <span className="text-slate-500 font-mono">Quick Probe:</span>
            {quickSearches.map((u) => (
              <button
                key={u}
                type="button"
                onClick={() => setQuery(u)}
                className="px-2 py-0.5 rounded-md bg-slate-800/70 hover:bg-slate-700 text-slate-300 font-mono text-[11px] transition-colors border border-slate-700/50"
              >
                @{u}
              </button>
            ))}
          </div>

          {error && (
            <div className="mt-4 p-3.5 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-start gap-2 text-left">
              <Info className="w-4 h-4 flex-shrink-0 text-red-400 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>

      {/* Feature Pillar Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 border-t border-card-border/60">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
            Engineered for Precision, Not Speculation
          </h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Most OSINT tools treat HTTP 200 as profile existence. OpenTrace enforces multi-signal verification
            and separate confidence dimensions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl hover:border-emerald-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">3 Confidence Dimensions</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              We never combine independent metrics into a single misleading score. We distinctly measure{" "}
              <strong className="text-slate-200">Existence Confidence</strong>,{" "}
              <strong className="text-slate-200">Data Reliability</strong>, and{" "}
              <strong className="text-slate-200">Identity Association</strong>.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl hover:border-teal-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-4">
              <Network className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">Evidence-Linked Graph</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Visualizes account connections only when backed by public evidence: matching personal domains,
              explicit cross-references, or handle consistency across verified communities.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl hover:border-cyan-500/40 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">Zero Bypass & Anti-SSRF</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Strict isolation against private IP ranges and cloud metadata endpoints. OpenTrace never bypasses
              CAPTCHAs, credentials, or private access controls.
            </p>
          </div>
        </div>
      </div>

      {/* OTP Ownership Verification Modal */}
      {otpModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-5">
              <Shield className="w-6 h-6" />
            </div>

            <h3 className="text-xl font-bold text-white mb-2">
              Verify {otpType === "email" ? "Email" : "Phone"} Ownership
            </h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              OpenTrace enforces authorized self-audits to prevent malicious surveillance. A verification challenge was generated for:
              <span className="block mt-1 font-mono text-emerald-400 text-sm font-semibold truncate">
                {otpTarget}
              </span>
            </p>

            {devOtp && (
              <div className="mb-5 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <span className="text-[11px] text-emerald-400 block font-semibold">Testing Code (Local Dev):</span>
                  <span className="font-mono text-base font-extrabold text-white tracking-widest">{devOtp}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setOtpCode(devOtp)}
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 font-mono text-xs transition-colors"
                >
                  Use Code
                </button>
              </div>
            )}

            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase tracking-wider">
                  6-Digit Verification Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  required
                  autoFocus
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="Enter 6-digit code..."
                  className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white font-mono text-center text-xl tracking-[0.3em] placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                />
              </div>

              {otpError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center gap-2">
                  <Info className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{otpError}</span>
                </div>
              )}

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setOtpModalOpen(false)}
                  disabled={otpVerifying}
                  className="flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={otpVerifying || !otpCode.trim()}
                  className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-all flex items-center justify-center gap-2 shadow-glow disabled:opacity-50"
                >
                  {otpVerifying ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      Auditing...
                    </>
                  ) : (
                    "Verify & Audit"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
