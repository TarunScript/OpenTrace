import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimeAgo(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffSec < 60) return "just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  } catch {
    return dateString;
  }
}

export function formatConfidence(score: number): { label: string; color: string; bg: string } {
  if (score >= 0.85) {
    return { label: "High Confidence", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
  }
  if (score >= 0.6) {
    return { label: "Moderate", color: "text-teal-400", bg: "bg-teal-500/10 border-teal-500/30" };
  }
  if (score >= 0.35) {
    return { label: "Low / Ambiguous", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30" };
  }
  return { label: "Unverified", color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/30" };
}

