import React from "react";
import Link from "next/link";
import { Shield, Lock, Terminal, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-card-border/60 bg-background/90 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-5 h-5 text-emerald-400" />
              <span className="font-bold text-white font-mono tracking-wider">OPENTRACE</span>
            </div>
            <p className="text-slate-400 text-sm max-w-md leading-relaxed">
              Open-Source Digital Footprint Intelligence Platform. Providing transparent, evidence-backed
              public presence audits without fabricated statistics or arbitrary subscription paywalls.
            </p>
            <div className="mt-4 flex items-center gap-3 text-xs text-slate-500 font-mono">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Multi-Signal OSINT Active
              </span>
              <span>•</span>
              <span>Apache-2.0 License</span>
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="font-semibold text-white uppercase text-[11px] tracking-wider mb-3">Investigation</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/" className="hover:text-emerald-400 transition-colors">
                  Username Search
                </Link>
              </li>
              <li>
                <Link href="/sites" className="hover:text-emerald-400 transition-colors">
                  Supported Site Registry
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-emerald-400 transition-colors">
                  Investigation History
                </Link>
              </li>
              <li>
                <a href="http://localhost:8000/api/docs" target="_blank" rel="noreferrer" className="hover:text-emerald-400 transition-colors flex items-center gap-1">
                  API Reference <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="font-semibold text-white uppercase text-[11px] tracking-wider mb-3">Ethics & Privacy</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/privacy" className="hover:text-emerald-400 transition-colors">
                  Privacy Policy & Retention
                </Link>
              </li>
              <li>
                <span className="text-slate-500">SSRF & Anti-Abuse Controls</span>
              </li>
              <li>
                <span className="text-slate-500">DPDP Act (India) Alignment</span>
              </li>
              <li>
                <span className="text-slate-500">Zero Password/Bypass Pledge</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
          <p>© {new Date().getFullYear()} OpenTrace. Open Source Software under Apache-2.0 License.</p>
          <p className="font-mono">"Your digital footprint, transparently discovered."</p>
        </div>
      </div>
    </footer>
  );
}

