import * as React from "react";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  hiddenCost: number;
  markupPercent: number;
  currency: string;
  className?: string;
};

export function HiddenFeeAlert({
  hiddenCost,
  markupPercent,
  currency,
  className,
}: Props) {
  if (hiddenCost <= 0) return null;

  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-800",
        className
      )}
    >
      <AlertTriangle className="h-4 w-4 flex-shrink-0 text-orange-500 mt-0.5" />
      <span>
        <span className="font-semibold">
          {currency} {hiddenCost.toFixed(2)} hidden
        </span>{" "}
        in the exchange rate — {markupPercent.toFixed(2)}% worse than
        mid-market.
      </span>
    </div>
  );
}
