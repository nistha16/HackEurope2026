import { describe, it, expect } from "vitest";
import { compareProviders, detectHiddenFees } from "./providers";

// EUR→MAD with a realistic mid-market rate
const MID_RATE = 10.85;
const AMOUNT = 500;

describe("compareProviders", () => {
  const results = compareProviders(AMOUNT, "EUR", "MAD", MID_RATE);

  it("returns results sorted by total_real_cost ascending", () => {
    for (let i = 1; i < results.length; i++) {
      expect(results[i].total_real_cost).toBeGreaterThanOrEqual(
        results[i - 1].total_real_cost
      );
    }
  });

  it("all money values are in source currency (EUR), not target", () => {
    for (const r of results) {
      // All cost fields should be much smaller than the send amount
      // (if they were in MAD they'd be ~10x larger)
      expect(r.flat_fee).toBeLessThanOrEqual(AMOUNT);
      expect(r.percent_fee).toBeLessThanOrEqual(AMOUNT);
      expect(r.fx_markup_cost).toBeLessThanOrEqual(AMOUNT);
      expect(r.hidden_cost).toBeLessThanOrEqual(AMOUNT);
      expect(r.total_real_cost).toBeLessThanOrEqual(AMOUNT);
    }
  });

  it("hidden_cost equals fx_markup_cost (same value, no double-counting)", () => {
    for (const r of results) {
      expect(r.hidden_cost).toBe(r.fx_markup_cost);
    }
  });

  it("total_real_cost = flat_fee + percent_fee + fx_markup_cost", () => {
    for (const r of results) {
      const expected =
        Math.round((r.flat_fee + r.percent_fee + r.fx_markup_cost) * 100) / 100;
      expect(r.total_real_cost).toBe(expected);
    }
  });

  it("provider_rate <= mid-market rate (markup only makes it worse)", () => {
    for (const r of results) {
      expect(r.provider_rate).toBeLessThanOrEqual(MID_RATE);
    }
  });

  it("recipient_gets is positive and in target currency scale", () => {
    for (const r of results) {
      // With EUR→MAD at ~10.85, recipient should get roughly amount * rate
      expect(r.recipient_gets).toBeGreaterThan(0);
      expect(r.recipient_gets).toBeGreaterThan(AMOUNT); // MAD > EUR numerically
    }
  });

  it("all values are rounded to 2 decimal places", () => {
    for (const r of results) {
      const check = (v: number) => expect(Math.round(v * 100) / 100).toBe(v);
      check(r.flat_fee);
      check(r.percent_fee);
      check(r.fx_markup_cost);
      check(r.total_fee);
      check(r.hidden_cost);
      check(r.total_real_cost);
      check(r.recipient_gets);
    }
  });

  it("no NaN values in any result field", () => {
    for (const r of results) {
      expect(Number.isFinite(r.flat_fee)).toBe(true);
      expect(Number.isFinite(r.percent_fee)).toBe(true);
      expect(Number.isFinite(r.fx_markup_cost)).toBe(true);
      expect(Number.isFinite(r.total_fee)).toBe(true);
      expect(Number.isFinite(r.hidden_cost)).toBe(true);
      expect(Number.isFinite(r.total_real_cost)).toBe(true);
      expect(Number.isFinite(r.provider_rate)).toBe(true);
      expect(Number.isFinite(r.recipient_gets)).toBe(true);
    }
  });
});

describe("detectHiddenFees", () => {
  it("returns score A for zero markup", () => {
    const { transparencyScore, hiddenMarkupPercent } = detectHiddenFees(
      MID_RATE,
      MID_RATE,
      AMOUNT,
      3.5
    );
    expect(hiddenMarkupPercent).toBe(0);
    expect(transparencyScore).toBe("A");
  });

  it("returns score F for 5% markup", () => {
    const markedUpRate = MID_RATE * 0.95;
    const { transparencyScore } = detectHiddenFees(
      markedUpRate,
      MID_RATE,
      AMOUNT,
      0
    );
    expect(transparencyScore).toBe("F");
  });

  it("hiddenCostAmount is in source currency", () => {
    const markedUpRate = MID_RATE * 0.97; // 3% markup
    const { hiddenCostAmount } = detectHiddenFees(
      markedUpRate,
      MID_RATE,
      AMOUNT,
      0
    );
    // 3% of 500 EUR ≈ 15 EUR, not 150+ MAD
    expect(hiddenCostAmount).toBeGreaterThan(10);
    expect(hiddenCostAmount).toBeLessThan(20);
  });

  it("handles midMarketRate of 0 without NaN", () => {
    const { hiddenMarkupPercent, hiddenCostAmount } = detectHiddenFees(
      0,
      0,
      AMOUNT,
      5
    );
    expect(Number.isFinite(hiddenMarkupPercent)).toBe(true);
    expect(Number.isFinite(hiddenCostAmount)).toBe(true);
  });
});
