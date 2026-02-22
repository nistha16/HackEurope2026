# FibreTransfer - Build Plan

**Tagline:** "Stop overpaying to send money home."

## Context

**Event:** HackEurope 2026 - Monzo FinTech Track (€1,000)

**Bounties:**

* Best Stripe Integration (€3K)
* Best Use of ElevenLabs (AirPods)
* Best Use of Gemini (€50K credits)

**Team:** 3 full-stack generalists

**Duration:** 36 hours

**Judging Criteria:** Startup viability, real-world impact, technical depth, polished demo

---

## The Concept

FibreTransfer is the **"Skyscanner for international money transfers."**

### The Problem
Sending money abroad costs 6.49% on average in fees (World Bank RPW Q1 2025). On $905B in global remittances (2024), that's **$59B/year in fees** - with banks charging up to 14.55%. There are 20+ providers (Wise, Western Union, Revolut, Remitly, banks) each with different fees and rates. Nobody knows which is cheapest for THEIR specific transfer. If everyone used the cheapest option, the UN estimates families would save $20B+ annually.

### The Solution
A comparison marketplace. Enter amount + currencies → instantly compare ALL online transfer services → ML predicts if you should send now or wait → AI exposes hidden fees → click through to the best provider's website to send.

We are **NOT** a bank. We do **NOT** handle transfers. We compare, users click through, and we earn an affiliate commission.

---

## Startup Model (Credit Karma for Remittances)

**How Credit Karma makes $1.5B/year:** Free credit score → recommend financial products → affiliate commission.

**How FibreTransfer makes money:** Free comparison → route users to cheapest provider → affiliate commission.

| Revenue Source | Per Event | Market Potential |
|----------------|-----------|------------------|
| Affiliate commission (per routed transfer) | €5 - €50 | $700B+ annual remittances |
| Premium rate alerts ("notify me when EUR/MAD hits X") | €2.99 / month | 281M migrants worldwide |
| B2B API (banks embed comparison engine) | €0.10 - €0.50 / user / mo. | Every bank needs this |
| "Overpay Scanner" (scan old receipts, show savings) | Free (Acquisition tool) | Converts users instantly |

---

## Data Sources (Real, Not Mocked)

**Key advantage:** Using REAL data gives institutional credibility when presenting to judges.

| Source | Data Provided | Auth Required | Limits |
|--------|---------------|---------------|--------|
| Frankfurter API | Live + historical FX rates (1999-present) | None | Unlimited |
| World Bank RPW | Provider fees across 367 corridors (2011-2025) | None | Download once |
| Alpha Vantage | OHLC FX data for ML training | Free Key | 25 req/day |
| ECB SDMX | Institutional reference rates | None | Unlimited |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | Next.js 14 (App Router) | Full-stack web app |
| Styling | Tailwind CSS + shadcn/ui | Polished UI fast |
| Database | Supabase (Postgres + Auth) | Users, transfers, providers |
| ML Service | Python FastAPI | FX prediction model |
| Multimodal | Gemini API | Receipt scanning |
| Voice | ElevenLabs API | Voice-powered transfers |
| Payments | Stripe | Process transfer payments |
| Charts | Recharts | Rate prediction visualization |
| Deployment | Vercel + Railway | Frontend + ML service |

---

## ML Architecture

### Model 1: Exchange Rate Predictor ("Send Now or Wait?")

**The killer feature no comparison site has.**

**Input:** Historical daily FX rates (25 years from Frankfurter/ECB)

**Model:** Random Forest Regressor or Prophet (handles seasonality)

```python
# Feature Engineering
features = {
    'rate_1d_ago': float,        # Yesterday's rate
    'rate_7d_avg': float,        # 7-day moving average
    'rate_30d_avg': float,       # 30-day moving average
    'rate_7d_volatility': float, # 7-day standard deviation
    'rate_momentum': float,      # Rate change direction (7d)
    'day_of_week': int,          # Markets behave differently by day
    'day_of_month': int,         # Month-end effects
    'month': int,                # Seasonal patterns
    'rate_vs_30d_avg': float,    # Current rate relative to 30d avg
    'rate_vs_90d_avg': float,    # Current rate relative to 90d avg
}
```

**Expected JSON Output:**

```json
{
  "current_rate": 10.85,
  "predicted_rate_24h": 10.92,
  "predicted_rate_72h": 10.88,
  "confidence": 0.78,
  "recommendation": "WAIT",
  "potential_savings": "€6.40 on a €500 transfer",
  "reasoning": "EUR/MAD has been trending up for 5 days. Historical patterns suggest a 1.2% improvement within 24 hours."
}
```

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
        "transparency_score": "A" if markup < 0.5 else "B" if markup < 1.5 else "C" if markup < 3 else "F"
    }
```

---

## API Integrations & Bounty Strategies

### Gemini - The Receipt Scanner

Scan a previous money transfer receipt → Gemini extracts: amount sent, amount received, fees charged, exchange rate used, provider name, date.

**Why this wins "Best Use of Gemini":** Multimodal understanding of financial documents. It's not just OCR; it's contextual extraction and comparison against real-time market data to calculate lost money.

### ElevenLabs - Voice-Powered Transfers

Natural language voice interface for accessibility.

**Example conversation:**
- **User:** "Send 500 euros to my mom in Morocco"
- **Coach (ElevenLabs):** "Best option: Wise. Fee: €3.50. Your mom receives 5,387 dirhams. Arrives in 2 hours. But - our model predicts the rate will improve by 0.8% tomorrow. Wait 24 hours and she'll receive 43 more dirhams. Want to send now or set an alert?"

**Why this wins "Best Use of ElevenLabs":** Transforms a complex comparison into a simple conversation, aiding users who find financial apps intimidating.

### Stripe - Premium + Rate Lock

**Premium Subscription (€2.99/mo via Stripe Billing):** Unlimited comparisons, rate alerts, 30-day predictions, receipt scanner.

**"Lock This Rate" Service (Stripe Payments):** Pay €1-2 to "lock" a great rate for 24 hours. If it drops, the user is protected.

**Why this wins "Best Stripe Integration":** Powers two central revenue streams (recurring + transactional). It's core to the business model, not bolted on.

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
/predict                       → Rate prediction chart + "Send Now or Wait?"
/scan                          → Receipt scanner (Gemini)
/voice                         → Voice transfer assistant
/api/compare                   → Comparison engine endpoint
/api/predict                   → ML prediction endpoint
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
│   │   ├── voice/route.ts                # ElevenLabs TTS
│   │   └── stripe/payment/route.ts       # Stripe payment
├── components/
│   ├── CompareForm.tsx                   # Currency + amount input
│   ├── ProviderRanking.tsx               # Ranked list of providers
│   ├── RatePredictionChart.tsx           # Prediction graph (Recharts)
│   ├── ReceiptScanner.tsx                # Camera + Gemini
│   └── TransparencyScore.tsx             # A/B/C/F rating badge
├── lib/
│   └── supabase.ts, gemini.ts, stripe.ts
└── data/
    └── providers.json                    # Seeded from World Bank data

ml/
├── main.py                               # FastAPI server
├── predictor.py                          # FX rate prediction model
└── data/fetch_historical.py              # Download from Frankfurter
```

---

## Agile Workflow & Sprints

### Roles

- **Person 1 (P1):** Frontend Lead (React, Tailwind, Recharts, UI/UX, Animations)
- **Person 2 (P2):** Backend Lead (Next.js APIs, Supabase, Stripe, Gemini, Engine)
- **Person 3 (P3):** ML & AI Lead (Python, FastAPI, ElevenLabs, Pitch)

### Sprint 1: Foundation (Hours 0-12) - "Make it work"

**Goal:** Core comparison engine working end-to-end.

- [ ] **P1:** Init Next.js + Tailwind + shadcn/ui + deploy Vercel
- [ ] **P2:** Setup Supabase (tables, auth) + env vars
- [ ] **P3:** Setup Python FastAPI + deploy Railway
- [ ] **P1:** Build CompareForm component
- [ ] **P2:** Integrate Frankfurter API (live rates + historical fetch)
- [ ] **P3:** Fetch 25yr historical FX data + cache as CSV
- [ ] **P2:** Build comparison engine logic + seed World Bank provider data
- [ ] **P1:** Build ProviderRanking + ProviderCard components
- [ ] **P3:** Feature engineering + train FX prediction model
- [ ] **P2:** Build hidden fee detection logic
- [ ] **P1:** Connect frontend compare form → backend comparison API

### Sprint 2: Intelligence Layer (Hours 12-24) - "Make it smart"

**Goal:** ML predictions + AI explanations + prize integrations working.

- [ ] **P3:** Prediction API endpoint (currency pair → send now/wait)
- [ ] **P1:** Build RatePredictionChart (Recharts) + SendOrWait card
- [ ] **P2:** Stripe Billing: premium subscription flow
- [ ] **P2:** Stripe Payments: "Lock This Rate" flow
- [ ] **P2:** Gemini receipt scanner API endpoint
- [ ] **P1:** Receipt scanner UI (camera capture + results)
- [ ] **P3:** ElevenLabs voice comparison TTS endpoint
- [ ] **P1:** VoiceAssistant component + audio player

### Sprint 3: Polish & Demo (Hours 24-36) - "Make it shine"

**Goal:** Demo-ready. Polished. Pitch rehearsed.

- [ ] **P1:** Landing page (hero, how it works, CTA)
- [ ] **P2:** Rate alerts (CRUD + UI)
- [ ] **P3:** Model validation + confidence tuning
- [ ] **P1:** Responsive design pass + Framer Motion animations
- [ ] **P2:** Seed demo data (realistic scenario for EUR→MAD)
- [ ] **P3:** Pre-compute predictions for demo corridors
- [ ] **P1:** Pre-record backup demo video
- [ ] **P3:** Write pitch script + practice (5x run-throughs)
- [ ] **P2:** Error handling + edge cases + final integration testing

---

## Demo Script (3 minutes)

**0:00-0:20 - The Hook:**  
"281 million people send money home every year. According to the World Bank, they lose $59 billion to fees... That ends today."

**0:20-0:40 - Intro:**  
"FibreTransfer is Skyscanner for money transfers. Compare every provider. See every hidden fee. Know exactly when to send."

**0:40-1:30 - Live Demo (Compare):**  
Type €500, EUR → MAD. Show results. Highlight Western Union's hidden markup vs. Wise.

**1:30-2:00 - ML Prediction:**  
Show prediction chart. "Our ML model trained on 25 years of ECB data predicts... Wait until tomorrow → your mom receives 43 more dirhams."

**2:00-2:20 - Receipt Scanner:**  
Scan old receipt with Gemini. "Gemini detected... you lost €12.30 in exchange rate markup." **Play ElevenLabs Audio**.

**2:20-2:40 - The Startup Model:**  
Explain affiliate routing + Stripe rate locks. Real data from ECB/World Bank.

**2:40-3:00 - Impact & Close:**  
"FibreTransfer doesn't just save money - it means more arrives home. More food on the table. Because your family deserves every cent."

---

## Verification Checklist (Pre-Demo)

- [ ] Compare flow: EUR → MAD, €500 shows 6 providers ranked correctly.
- [ ] Live rates: Frankfurter returns real rate.
- [ ] Hidden fees: Markup calculated correctly vs mid-market.
- [ ] Transparency: A-F scores display correctly.
- [ ] ML Prediction: "Send Now/Wait" displays.
- [ ] Gemini Scanner: Upload photo → amount/fees extracted.
- [ ] ElevenLabs: Audio plays in browser.
- [ ] Stripe: Payment intent creates successfully.
- [ ] Responsive: Looks flawless on mobile viewport.
- [ ] Time check: Demo run-through strictly under 3 minutes.