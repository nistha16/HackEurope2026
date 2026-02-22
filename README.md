# FibreTransfer

**Skyscanner for international money transfers.**

Compare every provider. See every hidden fee. Know exactly when to send.

> Built at HackEurope 2026 — Monzo FinTech Track

---

## What is FibreTransfer?

Migrants send over **$905 billion** home every year and lose an average of **6.49%** to fees — most of which are hidden in bad exchange rates. FibreTransfer fixes that.

Enter an amount, pick your currencies, and instantly see a ranked comparison of real providers (Wise, Revolut, Western Union, Remitly, PayPal, WorldRemit, XE) with:

- **Total real cost** including hidden FX markups
- **Transparency scores** (A to F) for each provider
- **ML-powered timing** that tells you if now is a good time to send or if you should wait
- **Paid detailed reports** with personalized recommendations

---

## Features

| Feature | Status |
|---------|--------|
| Provider comparison with hidden fee detection | Done |
| Live exchange rates (ECB + Open ER API) | Done |
| ML rate timing score (Logistic Regression + XGBoost) | Done |
| 1-year historical rate charts | Done |
| Stripe payments (subscriptions + one-time reports) | Done |
| Premium subscription page (€2.99/month) | Done |
| Detailed transfer report (€0.99) | Done |
| Login / user accounts (localStorage) | Done |
| Landing page with animations | Done |
| Voice assistant (ElevenLabs TTS API) | Backend only |
| Rate alerts | Backend only (in-memory) |
| Receipt scanner | Not implemented |
| Daily market briefings | Not implemented |

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Framer Motion, Recharts |
| Backend | Next.js API Routes (serverless) |
| ML Service | Python, FastAPI, scikit-learn, XGBoost |
| Payments | Stripe (checkout sessions + payment intents) |
| Data | Frankfurter API (ECB rates), Open ER API, World Bank RPW |
| Voice | ElevenLabs API (Rachel voice) |

---

## Project Structure

```
HackEurope2026/
├── src/
│   ├── app/                    # Next.js pages and API routes
│   │   ├── api/
│   │   │   ├── compare/        # POST — provider comparison
│   │   │   ├── predict/        # POST — ML timing prediction
│   │   │   ├── rates/          # GET  — exchange rate lookup
│   │   │   ├── report/generate/# POST — AI report generation
│   │   │   ├── stripe/payment/ # POST — Stripe payments
│   │   │   ├── voice/          # POST — text-to-speech
│   │   │   └── alerts/         # CRUD — rate alerts (in-memory)
│   │   ├── compare/            # comparison page
│   │   ├── predict/            # timing prediction page
│   │   ├── report/             # detailed report viewer
│   │   ├── subscribe/          # premium subscription page
│   │   ├── login/              # login page
│   │   └── subscription/       # success + cancel pages
│   ├── components/             # React components
│   ├── lib/                    # utilities (providers, stripe, auth, etc.)
│   ├── hooks/                  # React hooks (useAuth)
│   ├── data/                   # providers.json (7 real providers)
│   ├── types/                  # TypeScript interfaces
│   └── ml/                     # Python ML microservice
│       ├── main.py             # FastAPI server
│       ├── predictor.py        # ensemble model inference
│       ├── features.py         # 18 technical indicators
│       ├── train.py            # model training pipeline
│       ├── data/               # historical rate data + fetch script
│       ├── models/             # trained model (.joblib)
│       └── test/               # ML tests
├── .env.example                # environment variables template
└── package.json
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.10+ (for the ML service)
- A **Stripe** account (test mode is fine)

### 1. Clone and install

```bash
git clone https://github.com/nistha16/HackEurope2026.git
cd HackEurope2026
npm install
```

### 2. Set up environment variables

```bash
cp .env.example .env.local
```

Fill in your keys in `.env.local`:

```env
# Stripe (required for payments)
STRIPE_SECRET_KEY=sk_test_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_STRIPE_PRICE_ID=price_...      # your €2.99/month price ID

# ML Service (optional — fallback scoring works without it)
ML_SERVICE_URL=http://localhost:8000

# App
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# ElevenLabs (optional — only for voice feature)
ELEVENLABS_API_KEY=...
```

> The compare and predict features work without any API keys — they use free public exchange rate APIs.

### 3. Start the app

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 4. Start the ML service (optional)

```bash
cd src/ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 data/fetch_historical.py   # download 25 years of ECB data
python3 train.py                    # train the model
python3 main.py                     # starts FastAPI on port 8000
```

If the ML service is not running, the predict page uses a fallback percentile-based scoring system.

### 5. Run tests

```bash
# Frontend tests
npx vitest run

# ML tests (from src/ml/ with venv activated)
python3 test/test_main.py
```

### 6. Build for production

```bash
npm run build
npm start
```

---

## How It Works

### Provider Comparison

1. User enters amount + currency pair (e.g. €500 → MAD)
2. App fetches the live mid-market rate from the Frankfurter API (ECB data)
3. Each provider's fees are calculated: flat fee + percentage fee + FX markup
4. Providers are ranked by total real cost (cheapest first)
5. Hidden fees are flagged when a provider's FX markup exceeds 1%
6. Transparency scores (A–F) are assigned based on fee visibility

### ML Timing Score

The ML model answers: **"Is today a good day to send money?"**

- **Data**: 25 years of ECB exchange rates (1999–2024)
- **Features**: 18 technical indicators — RSI, MACD, moving average ratios, momentum, volatility, range position, plus temporal features (day of week, month)
- **Target**: Whether today's rate is in the top 30% of the next 10 trading days
- **Model**: Ensemble of Logistic Regression + XGBoost
- **Output**: A 0–100% timing score blended 40% model probability + 60% raw percentile
  - Score > 80%: **SEND NOW** (green)
  - Score 40–80%: **NEUTRAL** (gray)
  - Score < 40%: **WAIT** (amber)

### Payments (Stripe)

- **Subscription** (€2.99/month): Stripe Checkout → redirects to success/cancel page
- **One-time report** (€0.99): Stripe Checkout → generates detailed transfer analysis
- **Rate lock** (€1–2): Payment intent for locking an exchange rate

---

## Supported Currencies

EUR, USD, GBP, MAD, INR, PHP, NGN, PKR, BDT, MXN, EGP, TRY, BRL, CAD, AUD, JPY, CNY, KES, GHS, ZAR

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/compare` | POST | Compare providers for a currency pair + amount |
| `/api/predict` | POST | Get ML timing score for a currency pair |
| `/api/rates` | GET | Fetch live or historical exchange rates |
| `/api/report/generate` | POST | Generate a detailed transfer analysis |
| `/api/stripe/payment` | POST | Create Stripe payment/checkout session |
| `/api/voice` | POST | Convert text to speech (ElevenLabs) |
| `/api/alerts` | GET/POST/DELETE | Manage rate alerts |

---

## Data Sources

- [Frankfurter API](https://www.frankfurter.app/) — ECB reference rates (1999–present)
- [Open Exchange Rates API](https://open.er-api.com/) — 160+ currencies (real-time)
- [World Bank RPW](https://remittanceprices.worldbank.org/) — provider fee benchmarks

---

## Team

Built in 36 hours at HackEurope 2026.

---

## License

MIT
