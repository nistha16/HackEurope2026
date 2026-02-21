"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CURRENCIES } from "@/types";
import { CurrencySelector } from "@/components/ui/currencySelector";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowLeftRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type CompareResponse = {
  comparisonId?: string;
  // include whatever your /api/compare returns
};

export function CompareForm() {
  const router = useRouter();

  const [amount, setAmount] = React.useState<string>("500");
  const [source, setSource] = React.useState<string>("EUR");
  const [target, setTarget] = React.useState<string>("MAD");

  const [isSwapping, setIsSwapping] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const numericAmount = Number(amount);

  function validate(): string | null {
    if (!amount || Number.isNaN(numericAmount)) return "Enter a valid amount.";
    if (numericAmount <= 0) return "Amount must be greater than 0.";
    if (source === target) return "Source and target currencies must be different.";
    return null;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const v = validate();
    setError(v);
    if (v) return;

    setLoading(true);
    try {
      const res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount: numericAmount,
          source_currency: source,
          target_currency: target,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Compare request failed");
      }

      const data: CompareResponse = await res.json();

      // Preferred: navigate to results using returned id
      if (data.comparisonId) {
        router.push(`/compare/results?id=${encodeURIComponent(data.comparisonId)}`);
      } else {
        // Fallback: pass query params
        router.push(
          `/compare/results?amount=${encodeURIComponent(numericAmount)}&source=${encodeURIComponent(
            source
          )}&target=${encodeURIComponent(target)}`
        );
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  function onSwap() {
    setIsSwapping(true);
    // tiny delay for animation to feel real
    window.setTimeout(() => {
      setSource(target);
      setTarget(source);
      setIsSwapping(false);
    }, 160);
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-3xl mx-auto"
      aria-label="SendSmart comparison form"
    >
      <div className="rounded-3xl border bg-background shadow-sm p-4 sm:p-6">
        <div className="flex flex-col gap-4 sm:gap-5">
          {/* Amount */}
          <div>
            <div className="mb-2 text-sm font-medium text-muted-foreground">
              Amount
            </div>

            <div className="relative">
              <div className="absolute inset-y-0 left-4 flex items-center text-muted-foreground font-semibold">
                {source}
              </div>

              <Input
                inputMode="decimal"
                pattern="^[0-9]*[.,]?[0-9]*$"
                className="h-14 rounded-2xl pl-12 text-lg sm:text-xl font-semibold"
                value={amount}
                onChange={(e) => {
                  // allow only numbers + dot/comma
                  const next = e.target.value.replace(/[^0-9.,]/g, "");
                  setAmount(next);
                }}
                onBlur={() => {
                  // normalize commas -> dots
                  if (amount.includes(",")) setAmount(amount.replace(",", "."));
                }}
                placeholder="500"
                aria-label="Amount"
              />
              <div className="mt-2 text-xs text-muted-foreground">
                Min: 1
              </div>
            </div>
          </div>

          {/* Currency selectors + swap */}
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-3 sm:gap-4 items-end">
            <CurrencySelector
              label="From"
              value={source}
              onValueChange={setSource}
              currencies={CURRENCIES}
              disabled={loading}
            />

            <div className="flex justify-center">
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={onSwap}
                disabled={loading}
                className={cn(
                  "h-12 w-12 rounded-2xl",
                  isSwapping && "ring-2 ring-offset-2"
                )}
                aria-label="Swap currencies"
              >
                <ArrowLeftRight
                  className={cn(
                    "h-5 w-5 transition-transform duration-200",
                    isSwapping && "rotate-180"
                  )}
                />
              </Button>
            </div>

            <CurrencySelector
              label="To"
              value={target}
              onValueChange={setTarget}
              currencies={CURRENCIES}
              disabled={loading}
            />
          </div>

          {/* Error */}
          {error ? (
            <div className="text-sm text-red-600">{error}</div>
          ) : null}

          {/* Compare button */}
          <div className="flex justify-end">
            <Button
              type="submit"
              className="h-12 rounded-2xl px-6"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Comparing…
                </>
              ) : (
                "Compare"
              )}
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}