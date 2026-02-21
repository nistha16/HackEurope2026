"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import type { ComparisonResult } from "@/types";

type Score = ComparisonResult["transparency_score"];

const SCORE_CONFIG: Record<
  Score,
  { bg: string; text: string; description: string }
> = {
  A: { bg: "bg-green-100",  text: "text-green-800",  description: "Excellent — uses mid-market rate with near-zero markup (<0.1%)." },
  B: { bg: "bg-blue-100",   text: "text-blue-800",   description: "Good — small FX markup under 1%." },
  C: { bg: "bg-yellow-100", text: "text-yellow-800", description: "Fair — moderate FX markup between 1% and 2.5%." },
  D: { bg: "bg-orange-100", text: "text-orange-800", description: "Poor — high FX markup between 2.5% and 4%." },
  F: { bg: "bg-red-100",    text: "text-red-800",    description: "Failing — significant hidden costs, markup over 4%." },
};

type Props = { score: Score; className?: string };

export function TransparencyScore({ score, className }: Props) {
  const { bg, text, description } = SCORE_CONFIG[score];

  return (
    <div className="relative inline-block group">
      <span
        className={cn(
          "inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold cursor-default select-none",
          bg, text, className
        )}
        aria-label={`Transparency score: ${score}`}
      >
        {score}
      </span>

      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20 w-56 pointer-events-none">
        <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 text-center shadow-xl">
          <p className="font-semibold mb-1">Grade {score}</p>
          <p className="text-gray-300">{description}</p>
        </div>
        <div className="w-2 h-2 bg-gray-900 rotate-45 mx-auto -mt-1" />
      </div>
    </div>
  );
}
