import providersData from "@/data/providers.json";
import type { Provider, ComparisonResult } from "@/types";

const providers: Provider[] = providersData as Provider[];

export function getProviders(): Provider[] {
  return providers;
}

export function compareProviders(
  amount: number,
  sourceCurrency: string,
  targetCurrency: string,
  midMarketRate: number
): ComparisonResult[] {
  const corridor = `${sourceCurrency}-${targetCurrency}`;

  const results: ComparisonResult[] = providers
    .filter((provider) => {
      return (
        provider.supported_corridors.includes(corridor) &&
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

      const idealRecipientGets = amount * midMarketRate;
      const hiddenCost = idealRecipientGets - recipientGets;
      const totalRealCost = totalFee;

      const { transparencyScore } = detectHiddenFees(
        providerRate,
        midMarketRate,
        amount,
        flatFee + percentFee
      );

      return {
        provider,
        send_amount: amount,
        flat_fee: flatFee,
        percent_fee: percentFee,
        fx_markup_cost: fxMarkupCost,
        total_fee: totalFee,
        exchange_rate: midMarketRate,
        provider_rate: providerRate,
        recipient_gets: recipientGets,
        hidden_cost: hiddenCost,
        total_real_cost: totalRealCost,
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
