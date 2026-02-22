# FiberTransfer

**Skyscanner for international money transfers.**

Compare every provider. See every hidden fee. Know if today is a good day to send.

> HackEurope 2026 — Monzo FinTech Track

## Quick Start

```bash
git clone https://github.com/nistha16/HackEurope2026.git
cd HackEurope2026
npm install
cp .env.example .env.local   # fill in your API keys
npm run dev                   # http://localhost:3000
```

## What It Does

1. **Compare** — Enter amount + currencies, instantly see 8 providers ranked by total real cost (including hidden FX markup)
2. **Timing Score** — ML model scores today's rate from 0 to 1 based on the last 2 months of data. 0.82 means today is better than 82% of recent days.
3. **Market Insights** — 1 year of historical rate data with trends, volatility, and Claude-powered plain-language analysis
4. **Receipt Scanner** — Scan an old transfer receipt with Gemini, see exactly how much you overpaid
5. **Voice Briefing** — ElevenLabs reads your market summary and comparison results aloud

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- **ML Service**: Python FastAPI (separate directory: `ml/`)
- **APIs**: Claude (market insights), Gemini (receipt scanning), ElevenLabs (voice), Stripe (payments)
- **FX Data**: Frankfurter API (ECB rates) + Open Exchange Rates (non-ECB fallback)
- **Data**: World Bank Remittance Prices Worldwide (RPW)

## API Integrations

| API | Role |
| --- | ---- |
| **Claude** | Interprets timing scores and fee structures in plain language. Multi-step financial reasoning. |
| **Gemini** | Scans transfer receipts — extracts amounts, fees, rates. Calculates overpayment. |
| **ElevenLabs** | Voice briefings: reads timing score, best provider, and savings aloud. |
| **Stripe** | Premium subscriptions (€2.99/mo for timing alerts) + one-time detailed report payments (€0.99). |

## Testing

```bash
npx vitest run    # 12 tests covering comparison engine
```
