"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export function NavUser() {
  const { user, isPremium, logout } = useAuth();
  const [showNoCredits, setShowNoCredits] = React.useState(false);

  if (!user) {
    return (
      <Link
        href="/login"
        className="text-muted-foreground hover:text-foreground transition-colors text-sm"
      >
        Sign in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {isPremium ? (
        <>
          <span className="rounded-full bg-emerald-100 text-emerald-700 px-2 py-0.5 text-xs font-semibold ring-1 ring-emerald-300">
            ★ Premium
          </span>
          <div className="relative">
            <button
              onClick={() => setShowNoCredits(!showNoCredits)}
              className="text-xs font-medium text-emerald-600 hover:text-emerald-800 transition-colors"
            >
              Reports
            </button>
            {showNoCredits && (
              <div className="absolute right-0 top-6 z-50 w-56 rounded-xl border bg-white p-3 shadow-lg text-xs text-zinc-600">
                Cannot complete this as credits were not given for this demo.
                <button
                  onClick={() => setShowNoCredits(false)}
                  className="ml-2 text-zinc-400 hover:text-zinc-600"
                >
                  ✕
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        <span className="rounded-full bg-zinc-100 text-zinc-500 px-2 py-0.5 text-xs font-medium">
          Member
        </span>
      )}
      <span className="text-sm text-muted-foreground max-w-30 truncate">
        {user.email}
      </span>
      <button
        onClick={logout}
        className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
      >
        Sign out
      </button>
    </div>
  );
}
