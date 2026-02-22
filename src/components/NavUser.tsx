"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export function NavUser() {
  const { user, logout } = useAuth();

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
      {user.isPremium && (
        <span className="rounded-full bg-emerald-100 text-emerald-700 px-2 py-0.5 text-xs font-medium">
          Premium
        </span>
      )}
      <span className="text-sm text-muted-foreground max-w-[120px] truncate">
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
