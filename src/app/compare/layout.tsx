import * as React from "react";
import Link from "next/link";
import { NavUser } from "@/components/NavUser";

export default function CompareLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <nav className="w-full border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-14">
          <Link href="/" className="text-lg font-bold tracking-tight">
            Fibre<span className="text-emerald-600">Transfer</span>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link
              href="/compare"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Compare
            </Link>
            <Link
              href="/predict"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Predict
            </Link>
            <Link
              href="/subscribe"
              className="rounded-full bg-emerald-600 text-white px-3 py-1 text-xs font-medium hover:bg-emerald-700 transition-colors"
            >
              Premium
            </Link>
            <NavUser />
          </div>
        </div>
      </nav>
      {children}
    </>
  );
}
