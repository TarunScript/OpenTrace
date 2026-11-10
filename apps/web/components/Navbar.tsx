"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Search, Globe, History, Lock, User, LogOut, Github } from "lucide-react";
import { api, UserProfile } from "@/lib/api";
import { AuthModal } from "@/components/AuthModal";

export function Navbar() {
  const pathname = usePathname();
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  useEffect(() => {
    api.getMe().then((user) => setCurrentUser(user));
  }, []);

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
  };

  const navLinks = [
    { href: "/", label: "Investigate", icon: Search },
    { href: "/sites", label: "Registry", icon: Globe },
    { href: "/history", label: "History", icon: History },
    { href: "/privacy", label: "Privacy & Ethics", icon: Lock },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-card-border/60 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:border-emerald-400/60 transition-all duration-300 shadow-glow">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white font-mono">OPENTRACE</span>
                <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono">
                  v1.0 MVP
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground hidden sm:block">Digital Footprint Intelligence</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Actions & Auth */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/opentrace/opentrace"
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors"
              title="GitHub Repository"
            >
              <Github className="w-5 h-5" />
            </a>

            {currentUser ? (
              <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
                <User className="w-3.5 h-3.5 text-emerald-400" />
                <span className="max-w-[120px] truncate">{currentUser.email}</span>
                <button
                  onClick={handleLogout}
                  className="ml-1 text-slate-500 hover:text-red-400 transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthOpen(true)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
              >
                <User className="w-3.5 h-3.5 text-emerald-400" />
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(user) => setCurrentUser(user)}
      />
    </>
  );
}

