# SendSmart

**Skyscanner for international money transfers.**

Compare every provider. See every hidden fee. Know exactly when to send.

> HackEurope 2026 — Monzo FinTech Track

## Quick Start

```bash
git clone https://github.com/nistha16/HackEurope2026.git
cd HackEurope2026
npm install
cp .env.example .env.local   # fill in your API keys
npm run dev                   # http://localhost:3000
```

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- **ML Service**: Python FastAPI (separate directory: `ml/`)
- **APIs**: Claude, Gemini, ElevenLabs, Stripe, Frankfurter (ECB rates)
- **Data**: World Bank Remittance Prices Worldwide (RPW)
