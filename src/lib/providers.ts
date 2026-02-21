import providersData from "@/data/providers.json";
import { CURRENCIES, type Provider, type ComparisonResult } from "@/types";

const ALL_CURRENCY_CODES = CURRENCIES.map((c) => c.code);

const providers: Provider[] = providersData as Provider[];

function supportsCurrency(provider: Provider, currency: string): boolean {
  return provider.currencies.includes("*")
    ? ALL_CURRENCY_CODES.includes(currency)
    : provider.currencies.includes(currency);
}

export function getProviders(): Provider[] {
  return providers;
}

export function compareProviders(
  amount: number,
  sourceCurrency: string,
  targetCurrency: string,
  midMarketRate: number
): ComparisonResult[] {
  const results: ComparisonResult[] = providers
    .filter((provider) => {
      return (
        supportsCurrency(provider, sourceCurrency) &&
        supportsCurrency(provider, targetCurrency) &&
        amount >= provider.min_amount &&
        amount <= provider.max_amount
      );
    })
    .map((provider) => {
      const flatFee = provider.fee_flat;
      const percentFee = (provider.fee_percent / 100) * amount;
      const fxMarkupCost = (provider.fx_markup_percent / 100) * amount;
      const totalFee = flatFee + percentFee + fxMarkupCost;

      const providerRate =
        midMarketRate * (1 - provider.fx_markup_percent / 100);
      const amountAfterFees = amount - flatFee - percentFee;
      const recipientGets = amountAfterFees * providerRate;

      const totalRealCost = totalFee;
      // hidden_cost is the portion of cost buried in the FX rate markup
      // (in source currency, same units as all other cost fields)
      const hiddenCost = fxMarkupCost;

      const { transparencyScore } = detectHiddenFees(
        providerRate,
        midMarketRate,
        amount,
        flatFee + percentFee
      );

      const r2 = (n: number) => Math.round(n * 100) / 100;

      return {
        provider,
        send_amount: amount,
        flat_fee: r2(flatFee),
        percent_fee: r2(percentFee),
        fx_markup_cost: r2(fxMarkupCost),
        total_fee: r2(totalFee),
        exchange_rate: midMarketRate,
        provider_rate: Number(providerRate.toFixed(4)),
        recipient_gets: r2(recipientGets),
        hidden_cost: r2(hiddenCost),
        total_real_cost: r2(totalRealCost),
        transparency_score: transparencyScore,
      };
    })
    .sort((a, b) => a.total_real_cost - b.total_real_cost);

  return results;
}

export function detectHiddenFees(
  providerRate: number,
  midMarketRate: number,
  amount: number,
  advertisedFee: number
): {
  hiddenMarkupPercent: number;
  hiddenCostAmount: number;
  totalRealCost: number;
  transparencyScore: "A" | "B" | "C" | "D" | "F";
} {
  const hiddenMarkupPercent =
    midMarketRate > 0
      ? ((midMarketRate - providerRate) / midMarketRate) * 100
      : 0;

  const hiddenCostAmount = (hiddenMarkupPercent / 100) * amount;
  const totalRealCost = advertisedFee + hiddenCostAmount;

  let transparencyScore: "A" | "B" | "C" | "D" | "F";
  if (hiddenMarkupPercent < 0.1) {
    transparencyScore = "A";
  } else if (hiddenMarkupPercent < 1.0) {
    transparencyScore = "B";
  } else if (hiddenMarkupPercent < 2.5) {
    transparencyScore = "C";
  } else if (hiddenMarkupPercent < 4.0) {
    transparencyScore = "D";
  } else {
    transparencyScore = "F";
  }

  return {
    hiddenMarkupPercent,
    hiddenCostAmount,
    totalRealCost,
    transparencyScore,
  };
}
