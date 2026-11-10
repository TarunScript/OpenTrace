import React from "react";
import { Lock, Shield, Eye, Trash2, FileCheck, AlertTriangle } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-10 pb-6 border-b border-card-border/60">
        <div className="flex items-center gap-2 mb-2">
          <Lock className="w-5 h-5 text-emerald-400" />
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Privacy, Security & Ethics</h1>
        </div>
        <p className="text-slate-400 text-sm">
          Our commitment to ethical open-source intelligence, data minimization, and regulatory compliance.
        </p>
      </div>

      <div className="space-y-8 text-slate-300 text-sm leading-relaxed">
        {/* Core Philosophy */}
        <section className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            1. Core Ethical OSINT Principles
          </h2>
          <p className="mb-3 text-slate-400">
            OpenTrace exists to help individuals discover, understand, and audit their own publicly exposed
            digital footprint. We operate strictly within the following boundaries:
          </p>
          <ul className="space-y-2 list-disc list-inside text-slate-300 text-xs font-mono">
            <li><strong>Public Only:</strong> Probing is restricted exclusively to public profiles and publicly declared metadata.</li>
            <li><strong>No Credential Bypasses:</strong> OpenTrace never bypasses login walls, CAPTCHAs, or authentication gates.</li>
            <li><strong>No Account Enumeration:</strong> We do not abuse password-reset, account-recovery, or registration endpoints.</li>
            <li><strong>No Data Brokering:</strong> We never sell, monetize, or package personal investigation data.</li>
          </ul>
        </section>

        {/* Indian DPDP Act & Data Protection */}
        <section className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-teal-400" />
            2. Regulatory Alignment & India DPDP Act
          </h2>
          <p className="text-slate-400 mb-3">
            OpenTrace has been designed with the principles of India's Digital Personal Data Protection (DPDP) Act
            and global data privacy frameworks:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <strong className="text-white block mb-1">Right to Erasure (Purge)</strong>
              Users can delete any investigation at any time with a single click. Deletion is instantaneous and purges cached findings.
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <strong className="text-white block mb-1">Purpose Limitation</strong>
              Searches are executed strictly for the stated digital footprint query and are never repurposed.
            </div>
          </div>
        </section>

        {/* Technical Security Controls */}
        <section className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Eye className="w-5 h-5 text-cyan-400" />
            3. Server-Side Request Forgery (SSRF) Protection
          </h2>
          <p className="text-slate-400 text-xs leading-relaxed mb-3">
            To prevent abuse against internal networks and cloud infrastructure, every probe destination is validated
            by our anti-SSRF engine before dispatch. The engine rejects:
          </p>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs text-slate-400 space-y-1">
            <div>• RFC 1918 Private Ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)</div>
            <div>• Loopback and Localhosts (127.0.0.0/8, ::1)</div>
            <div>• Cloud Provider Metadata (169.254.169.254, metadata.google.internal)</div>
            <div>• Non-HTTP/HTTPS protocols (file://, gopher://, dict://)</div>
          </div>
        </section>

        {/* Reporting Misuse */}
        <section className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            4. Reporting Misuse & Security Disclosures
          </h2>
          <p className="text-slate-400 text-xs leading-relaxed">
            If you believe your profile is being inaccurately classified or wish to report a security vulnerability,
            please open an issue or security advisory on our GitHub repository.
          </p>
        </section>
      </div>
    </div>
  );
}

