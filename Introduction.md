# FiberTransfer - Build Plan

**Tagline:** "Stop overpaying to send money home."

## Context

**Event:** HackEurope 2026 - Monzo FinTech Track (€1,000)

**Bounties:**
* Best Use of Claude ($10K)
* Best Stripe Integration (€3K)
* Best Use of ElevenLabs (AirPods)
* Best Use of Gemini (€50K credits)

**Team:** 3 full-stack generalists

**Duration:** 36 hours

**Judging Criteria:** Startup viability, real-world impact, technical depth, polished demo

---

## The Concept

FiberTransfer is the **"Skyscanner for international money transfers."**

### The Problem
Sending money abroad costs 6.49% on average in fees (World Bank RPW Q1 2025). On $905B in global remittances (2024), that's **$59B/year in fees** - with banks charging up to 14.55%. There are 20+ providers (Wise, Western Union, Revolut, Remitly, banks) each with different fees, rates, and speeds. Nobody knows which is cheapest for THEIR specific transfer. If everyone used the cheapest option, the UN estimates families would save $20B+ annually.

### The Solution
A comparison marketplace. Enter amount + currencies → instantly compare ALL online transfer services → ML scores whether today is a good day to send → AI exposes hidden fees → click through to the best provider's website to send.

We are **NOT** a bank. We do **NOT** handle transfers. We compare, users click through, and we earn an affiliate commission.

---

## Startup Model (Credit Karma for Remittances)

**How Credit Karma makes $1.5B/year:** Free credit score → recommend financial products → affiliate commission.

**How FiberTransfer makes money:** Free comparison → route users to cheapest provider → affiliate commission.

| Revenue Source | Per Event | Market Potential |
|----------------|-----------|------------------|
| Affiliate commission (per routed transfer) | €5 - €50 | $700B+ annual remittances |
| Premium timing alerts ("notify me when score > 0.8") | €2.99 / month | 281M migrants worldwide |
| B2B API (banks embed comparison engine) | €0.10 - €0.50 / user / mo. | Every bank needs this |
| "Overpay Scanner" (scan old receipts, show savings) | Free (Acquisition tool) | Converts users instantly |

---

## Data Sources (Real, Not Mocked)

**Key advantage:** Using REAL data gives institutional credibility when presenting to judges.

| Source | Data Provided | Auth Required | Limits |
|--------|---------------|---------------|--------|
| Frankfurter API | Live + historical FX rates (1999-present) | None | Unlimited |
| Open Exchange Rates API | Fallback rates for non-ECB currencies | None | Unlimited |
| World Bank RPW | Provider fees across 367 corridors (2011-2025) | None | Download once |
| ECB SDMX | Institutional reference rates | None | Unlimited |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | Next.js 14 (App Router) | Full-stack web app |
| Styling | Tailwind CSS + shadcn/ui | Polished UI fast |
| Database | Supabase (Postgres + Auth) | Users, transfers, providers |
| ML Service | Python FastAPI | Market timing model |
| AI Reasoning | Claude API (Sonnet) | Market insights, fee explanation |
| Multimodal | Gemini API | Receipt scanning |
| Voice | ElevenLabs API | Voice-powered market briefings |
| Payments | Stripe | Premium subscriptions + detailed reports |
| Charts | Recharts | Historical rate visualization |
| Deployment | Vercel + Railway | Frontend + ML service |

---

## ML Architecture

### Model 1: Market Timing Score ("Is Today a Good Day to Send?")

**The killer feature no comparison site has.**

Instead of predicting future rates (unreliable for FX markets), we answer a simpler, more honest question: **where does today's rate sit compared to recent history?**

**Data pipeline:**
- Fetch **1 year** of daily FX rates from Frankfurter/ECB
- Use the most recent **2 months** (60 days) as the prediction window
- Full 1-year history provides trend context and market insights

**How the score works:**
The model produces a **Timing Score from 0.0 to 1.0** — a percentile ranking of today's rate within the last 2 months of data.

```python
# Core concept: percentile-based scoring
features = {
    'rate_today': float,            # Today's rate
    'rate_2m_avg': float,           # 2-month moving average
    'rate_2m_high': float,          # 2-month high
    'rate_2m_low': float,           # 2-month low
    'rate_percentile_2m': float,    # Where today sits in 2-month range (0-1)
    'rate_7d_trend': float,         # 7-day direction (rising/falling)
    'volatility_2m': float,         # 2-month standard deviation
    'day_of_week': int,             # Weekday patterns
    'rate_vs_1y_avg': float,        # Today vs 1-year average (context)
}
```

**Expected JSON Output:**

```json
{
  "current_rate": 10.85,
  "timing_score": 0.82,
  "recommendation": "SEND_NOW",
  "reasoning": "Today's EUR/MAD rate of 10.85 is better than 82% of days in the past 2 months. The rate has been trending upward for 5 days with low volatility.",
  "market_insights": {
    "two_month_high": 10.95,
    "two_month_low": 10.42,
    "two_month_avg": 10.67,
    "one_year_trend": "UP",
    "volatility": "LOW"
  },
  "historical_rates": [{"date": "2025-02-22", "rate": 10.85}, ...]
}
```

**Score interpretation:**
- **0.8 - 1.0**: Great day to send (rate is in top 20% of recent history)
- **0.5 - 0.8**: Decent day (rate is average or above)
- **0.0 - 0.5**: Below average (rate is worse than most recent days)

**Why this is defensible:** We're not predicting the future. We're telling users a statistical fact — "today's rate is better than X% of recent days." Judges can't challenge a percentile.

### Model 2: Hidden Fee Detector

**Exposes the real cost providers hide in inflated exchange rates.**

```python
def detect_hidden_fees(provider_rate, mid_market_rate, advertised_fee, amount):
    markup = (mid_market_rate - provider_rate) / mid_market_rate * 100
    hidden_cost = amount * markup / 100
    total_real_cost = advertised_fee + hidden_cost

    return {
        "advertised_fee": advertised_fee,
        "hidden_markup": f"{markup:.2f}%",
        "hidden_cost": hidden_cost,
        "total_real_cost": total_real_cost,
        "transparency_score": "A" if markup < 0.1 else "B" if markup < 1.0 else "C" if markup < 2.5 else "D" if markup < 4.0 else "F"
    }
```

---

## API Integrations & Bounty Strategies

### Claude - The Market Analyst

Claude receives the timing score, market data, and comparison results, then generates **multi-step financial reasoning** in plain language.

**What Claude does:**
1. **Interprets the timing score**: "EUR/MAD is at 10.92, in the top 15% of rates over the past 2 months. The market has been stable with low volatility — today is a good day to send."
2. **Explains hidden fees**: "Western Union advertises 'zero fees' but their exchange rate is 3.5% worse than the real rate. On your €500 transfer, that's a hidden cost of €17.50."
3. **Generates personalized advice**: "For amounts under €1,000 to Morocco, Wise is consistently cheapest. Your timing score of 0.82 means today's rate is better than most recent days."

**Why this wins "Best Use of Claude":** It performs multi-step reasoning — combining statistical timing data, fee structures, and market context to generate personalized financial advice. Not just summarization, but genuine analysis that synthesizes multiple data sources into actionable guidance.

### Gemini - The Receipt Scanner

Scan a previous money transfer receipt → Gemini extracts: amount sent, amount received, fees charged, exchange rate used, provider name, date.

Then the app calculates: **"You overpaid by €16.70 on this transfer. Through FiberTransfer, it would have cost €3.50."**

**Why this wins "Best Use of Gemini":** Multimodal understanding of financial documents. It's not just OCR; it's contextual extraction and comparison against real-time market data to calculate lost money.

### ElevenLabs - Voice Market Briefings

Natural language voice interface that reads the daily market insight and comparison results.

**Example conversation:**
- **User:** "Send 500 euros to my mom in Morocco"
- **Coach (ElevenLabs):** "Today's EUR to MAD timing score is 0.82 — a good day to send. Best option: Wise at €3.50 total. Your mom receives 5,387 dirhams, arriving in 2 hours. The rate is better than 82% of days in the past 2 months."

**Why this wins "Best Use of ElevenLabs":** Transforms complex financial data into a simple, accessible voice briefing. Helps users who find financial apps intimidating — they just ask and listen.

### Stripe - Premium + Detailed Reports

**Premium Subscription (€2.99/mo via Stripe Billing):**
- Unlimited comparisons (free tier: 3/day)
- Smart timing alerts ("notify me when my corridor scores above 0.8")
- Full 1-year historical charts
- Receipt scanner access
- Daily market briefings via email

**"Detailed Report" (€0.99 via Stripe Payments):**
- User runs a comparison → offered a downloadable PDF report with:
  - Full provider breakdown with Claude's plain-language analysis
  - Timing score explanation and historical context
  - Historical trend chart for the corridor
  - Personalized recommendation ("best time + best provider for YOUR transfer")
- A real product: sending €5K to family, you'd pay €0.99 to be sure you're getting the best deal
- Revenue: report fee + affiliate commission from the provider

**Why this wins "Best Stripe Integration":** Powers two central revenue streams — recurring subscriptions (Stripe Billing) and transactional report purchases (Stripe Payments). Both are core to the business model, not bolted on. Unlike a "rate lock" (which a comparison site can't actually fulfill), a detailed report is a real, deliverable product.

---

## Database Schema (Supabase)

```sql
-- Users via Supabase Auth
CREATE TABLE profiles (
  id uuid PRIMARY KEY REFERENCES auth.users,
  full_name text,
  email text,
  stripe_customer_id text,
  preferred_corridors jsonb DEFAULT '[]',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE providers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  logo_url text,
  fee_flat decimal(10,2) DEFAULT 0,
  fee_percent decimal(5,3) DEFAULT 0,
  fx_markup_percent decimal(5,3) DEFAULT 0,
  speed_hours int,
  transparency_score text,
  website_url text
);

CREATE TABLE comparisons (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users,
  source_currency text NOT NULL,
  target_currency text NOT NULL,
  amount decimal(10,2) NOT NULL,
  results jsonb NOT NULL,
  best_provider text,
  potential_savings decimal(10,2),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE rate_alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users NOT NULL,
  source_currency text NOT NULL,
  target_currency text NOT NULL,
  target_rate decimal(10,6),
  is_active boolean DEFAULT true
);

CREATE TABLE scanned_receipts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users,
  provider_name text,
  amount_sent decimal(10,2),
  amount_received decimal(10,2),
  fee_paid decimal(10,2),
  rate_used decimal(10,6),
  overpay_amount decimal(10,2)
);
```

---

## Project Structure

### Routes

```
/                              → Landing page
/compare                       → Main comparison page (THE core feature)
/compare/results               → Comparison results
/predict                       → Market timing score + historical chart
/scan                          → Receipt scanner (Gemini)
/voice                         → Voice transfer assistant
/api/compare                   → Comparison engine endpoint
/api/predict                   → ML timing score endpoint
```

### Key Files Structure

```
src/
├── app/
│   ├── page.tsx                          # Landing page
│   ├── compare/page.tsx                  # Comparison form
│   ├── api/
│   │   ├── compare/route.ts              # Comparison engine
│   │   ├── predict/route.ts              # Calls ML service
│   │   ├── scan/route.ts                 # Gemini processing
│   │   ├── explain/route.ts              # Claude explanation
│   │   ├── voice/route.ts                # ElevenLabs TTS
│   │   └── stripe/payment/route.ts       # Stripe payment
├── components/
│   ├── CompareForm.tsx                   # Currency + amount input
│   ├── ProviderRanking.tsx               # Ranked list of providers
│   ├── RatePredictionChart.tsx           # Historical rate chart (Recharts)
│   ├── ReceiptScanner.tsx                # Camera + Gemini
│   └── TransparencyScore.tsx             # A/B/C/F rating badge
├── lib/
│   └── supabase.ts, claude.ts, gemini.ts, stripe.ts
└── data/
    └── providers.json                    # Seeded from World Bank data

ml/
├── main.py                               # FastAPI server
├── predictor.py                          # Market timing model
└── data/fetch_historical.py              # Download from Frankfurter
```

---

## Agile Workflow & Sprints

### Roles

- **Person 1 (P1):** Frontend Lead (React, Tailwind, Recharts, UI/UX, Animations)
- **Person 2 (P2):** Backend Lead (Next.js APIs, Supabase, Stripe, Gemini, Engine)
- **Person 3 (P3):** ML & AI Lead (Python, FastAPI, Claude, ElevenLabs, Pitch)

### Sprint 1: Foundation (Hours 0-12) - "Make it work"

**Goal:** Core comparison engine working end-to-end.

- [ ] **P1:** Init Next.js + Tailwind + shadcn/ui + deploy Vercel
- [ ] **P2:** Setup Supabase (tables, auth) + env vars
- [ ] **P3:** Setup Python FastAPI + deploy Railway
- [ ] **P1:** Build CompareForm component
- [ ] **P2:** Integrate Frankfurter API (live rates + historical fetch)
- [ ] **P3:** Fetch 1 year of historical FX data + cache as CSV
- [ ] **P2:** Build comparison engine logic + seed World Bank provider data
- [ ] **P1:** Build ProviderRanking + ProviderCard components
- [ ] **P3:** Feature engineering + train market timing model
- [ ] **P2:** Build hidden fee detection logic
- [ ] **P1:** Connect frontend compare form → backend comparison API

### Sprint 2: Intelligence Layer (Hours 12-24) - "Make it smart"

**Goal:** ML timing score + AI explanations + prize integrations working.

- [ ] **P3:** Timing score API endpoint (currency pair → score 0-1)
- [ ] **P1:** Build historical rate chart (Recharts) + timing score card
- [ ] **P3:** Claude API market insight endpoint
- [ ] **P1:** Display Claude insights on comparison results
- [ ] **P2:** Stripe Billing: premium subscription flow
- [ ] **P2:** Stripe Payments: "Detailed Report" purchase flow (€0.99)
- [ ] **P2:** Gemini receipt scanner API endpoint
- [ ] **P1:** Receipt scanner UI (camera capture + results)
- [ ] **P3:** ElevenLabs voice market briefing endpoint
- [ ] **P1:** VoiceAssistant component + audio player

### Sprint 3: Polish & Demo (Hours 24-36) - "Make it shine"

**Goal:** Demo-ready. Polished. Pitch rehearsed.

- [ ] **P1:** Landing page (hero, how it works, CTA)
- [ ] **P2:** Timing alerts (CRUD + UI)
- [ ] **P3:** Model validation + score calibration
- [ ] **P1:** Responsive design pass + Framer Motion animations
- [ ] **P2:** Seed demo data (realistic scenario for EUR→MAD)
- [ ] **P3:** Pre-compute timing scores for demo corridors
- [ ] **P1:** Pre-record backup demo video
- [ ] **P3:** Write pitch script + practice (5x run-throughs)
- [ ] **P2:** Error handling + edge cases + final integration testing

---

## Demo Script (3 minutes)

**0:00-0:20 - The Hook:**
"281 million people send money home every year. According to the World Bank, they lose $59 billion to fees... That ends today."

**0:20-0:40 - Intro:**
"FiberTransfer is Skyscanner for money transfers. Compare every provider. See every hidden fee. Know if today is a good day to send."

**0:40-1:30 - Live Demo (Compare):**
Type €500, EUR → MAD. Show results. Highlight Western Union's hidden markup vs. Wise. **Show Claude insight**: "Western Union advertises €4.90 in fees but hides €17.50 in a bad exchange rate. Total real cost: €22.40. Wise charges €3.50 with the real rate."

**1:30-2:00 - Market Timing Score:**
Show historical chart (1 year). "Our model analyzes 2 months of rate data. Today's timing score: 0.82 — this rate is better than 82% of recent days. A good day to send." Claude explains: "EUR/MAD has been trending up with low volatility. Today's rate is near the 2-month high."

**2:00-2:20 - Receipt Scanner:**
Scan old receipt with Gemini. "Gemini detected... you overpaid by €16.70." **Play ElevenLabs voice**: "You overpaid by sixteen euros seventy on this transfer. Through FiberTransfer, it would have cost three euros fifty."

**2:20-2:40 - The Startup Model:**
Explain affiliate routing + Stripe premium (timing alerts, detailed reports). Real data from ECB/World Bank.

**2:40-3:00 - Impact & Close:**
"FiberTransfer doesn't just save money - it means more arrives home. More food on the table. Because your family deserves every cent."

---

## Verification Checklist (Pre-Demo)

- [ ] Compare flow: EUR → MAD, €500 shows 8 providers ranked correctly.
- [ ] Live rates: Frankfurter/Open ER returns real rate.
- [ ] Hidden fees: Markup calculated correctly vs mid-market.
- [ ] Transparency: A-F scores display correctly.
- [ ] Claude: Market insight + fee breakdown in plain language.
- [ ] ML Timing Score: Score 0-1 displays with recommendation.
- [ ] Historical chart: 1-year rate history renders correctly.
- [ ] Gemini Scanner: Upload photo → amount/fees extracted.
- [ ] ElevenLabs: Voice briefing plays in browser.
- [ ] Stripe: Premium checkout + report payment intent both work.
- [ ] Responsive: Looks flawless on mobile viewport.
- [ ] Time check: Demo run-through strictly under 3 minutes.
