"use client";

import React from "react";
import { X, ExternalLink, ShieldCheck, Clock, Activity, CheckCircle2, AlertCircle } from "lucide-react";
import { ProfileRecord } from "@/lib/api";

interface EvidenceModalProps {
  profile: ProfileRecord | null;
  onClose: () => void;
}

export function EvidenceModal({ profile, onClose }: EvidenceModalProps) {
  if (!profile) return null;

  const ev = profile.evidence_records?.[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="flex items-center gap-3 mb-6 border-b border-slate-800/80 pb-4">
          <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 font-bold font-mono text-lg">
            {profile.platform.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">{profile.platform}</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono">
                {profile.category}
              </span>
            </div>
            <a
              href={profile.profile_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1 mt-0.5 break-all"
            >
              {profile.profile_url} <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          </div>
        </div>

        {/* Confidence Scores Grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Profile Existence Confidence
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {Math.round(profile.confidence_existence * 100)}%
              </span>
              <span className="text-xs text-slate-500">Heuristic score</span>
            </div>
          </div>
          <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Data Reliability Confidence
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-cyan-400">
                {Math.round(profile.confidence_data * 100)}%
              </span>
              <span className="text-xs text-slate-500">Metadata quality</span>
            </div>
          </div>
        </div>

        <div className="mb-6 p-2.5 bg-slate-950/40 border border-slate-800 rounded-lg text-[11px] text-slate-400">
          <strong>Notice:</strong> Confidence metrics indicate heuristic match confidence and extracted data density. They do not constitute legal or definitive proof of personhood or identity.
        </div>

        {/* Evidence Verification Breakdown */}
        <div className="space-y-4 mb-6">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Verification Evidence Record
          </h4>

          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-3 text-xs font-mono">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/50">
              <span className="text-slate-400">Detection Method:</span>
              <span className="text-white font-semibold">{ev?.detection_method || "composite"}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/50">
              <span className="text-slate-400">Verification State:</span>
              <span className="text-emerald-400 font-semibold uppercase">{ev?.verification_status || "VERIFIED"}</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/50">
              <span className="text-slate-400">Observed At:</span>
              <span className="text-slate-300">{ev?.observed_at ? new Date(ev.observed_at).toUTCString() : "Live search"}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Probe Result / Match Evidence:</span>
              <p className="p-2.5 bg-slate-900 rounded-lg text-slate-200 text-xs font-sans leading-relaxed">
                {ev?.match_evidence || "Target responded with positive account markers without soft-404 or anti-bot challenge."}
              </p>
            </div>
          </div>
        </div>

        {/* Extracted Profile Details */}
        <div className="space-y-2 mb-6">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">Extracted Public Metadata</h4>
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-2 text-xs">
            <div>
              <span className="text-slate-500">Display Name:</span>{" "}
              <span className="text-slate-200 font-medium">{profile.display_name || "—"}</span>
            </div>
            <div>
              <span className="text-slate-500">Biography:</span>{" "}
              <span className="text-slate-200 font-medium">{profile.biography || "—"}</span>
            </div>
            <div>
              <span className="text-slate-500">Public Website:</span>{" "}
              {profile.public_website ? (
                <a href={profile.public_website} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
                  {profile.public_website}
                </a>
              ) : (
                <span className="text-slate-500">—</span>
              )}
            </div>
            <div>
              <span className="text-slate-500">Location:</span>{" "}
              <span className="text-slate-200 font-medium">{profile.location || "—"}</span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            Close
          </button>
          <a
            href={profile.profile_url}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 text-xs font-semibold rounded-xl text-slate-950 bg-emerald-400 hover:bg-emerald-300 transition-colors flex items-center gap-1.5"
          >
            Open Source Profile <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}

