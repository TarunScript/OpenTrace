import Link from "next/link";
import { Shield, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-4 py-24 text-center">
      <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400">
        <Shield className="w-8 h-8" />
      </div>
      <h1 className="text-3xl font-extrabold text-white font-mono mb-3">404 — Page Not Found</h1>
      <p className="text-slate-400 text-sm mb-8">
        The investigation or endpoint you requested does not exist or has been removed.
      </p>
      <Link
        href="/"
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-400 text-slate-950 hover:bg-emerald-300 transition-colors shadow-glow"
      >
        <ArrowLeft className="w-4 h-4" />
        Return to Investigation Console
      </Link>
    </div>
  );
}
