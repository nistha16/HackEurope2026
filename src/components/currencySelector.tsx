"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Currency = {
  code: string; // "EUR"
  name: string; // "Euro"
  flag: string; // "🇪🇺"
};

type Props = {
  label?: string;
  value: string;
  onValueChange: (value: string) => void;
  currencies: Currency[];
  disabled?: boolean;
  className?: string;
};

export function CurrencySelector({
  label,
  value,
  onValueChange,
  currencies,
  disabled,
  className,
}: Props) {
  const selected = currencies.find((c) => c.code === value);

  return (
    <div className={cn("w-full", className)}>
      {label ? (
        <div className="mb-2 text-sm font-medium text-muted-foreground">
          {label}
        </div>
      ) : null}

      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger className="h-12 rounded-2xl">
          <SelectValue
            placeholder="Select currency"
            aria-label={selected ? `${selected.code} ${selected.name}` : "Select currency"}
          >
            {selected ? (
              <span className="flex items-center gap-2">
                <span className="text-lg">{selected.flag}</span>
                <span className="font-semibold">{selected.code}</span>
                <span className="text-muted-foreground hidden sm:inline">
                  — {selected.name}
                </span>
              </span>
            ) : null}
          </SelectValue>
        </SelectTrigger>

        <SelectContent className="max-h-72">
          {currencies.map((c) => (
            <SelectItem key={c.code} value={c.code} className="py-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{c.flag}</span>
                <span className="font-semibold">{c.code}</span>
                <span className="text-muted-foreground">— {c.name}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}