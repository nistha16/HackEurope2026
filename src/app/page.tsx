import { CompareForm } from "@/components/compareForm";
import {
  ArrowRight,
  Search,
  ShieldCheck,
  TrendingUp,
  Globe,
  DollarSign,
  Users,
  BadgePercent,
} from "lucide-react";

const STEPS = [
  {
    icon: Search,
    title: "Enter your transfer",
    description:
      "Choose currencies and amount. We support 20+ currencies across 6 continents.",
  },
  {
    icon: ShieldCheck,
    title: "See every hidden fee",
    description:
      "We compare the real cost — not the advertised one. FX markups, flat fees, everything exposed.",
  },
  {
    icon: TrendingUp,
    title: "Send at the right time",
    description:
      "Our ML model trained on 25 years of ECB data tells you if waiting a day could save you money.",
  },
];

const STATS = [
  {
    icon: DollarSign,
    value: "$59B",
    label: "Lost to fees yearly",
    sublabel: "World Bank, 2024",
  },
  {
    icon: Users,
    value: "281M",
    label: "Migrants worldwide",
    sublabel: "UN Migration Report",
  },
  {
    icon: BadgePercent,
    value: "6.49%",
    label: "Average transfer cost",
    sublabel: "vs 3% UN target",
  },
  {
    icon: Globe,
    value: "8",
    label: "Providers compared",
    sublabel: "Real-time rates",
  },
];

const PROVIDERS = [
  { name: "Wise", score: "A" },
  { name: "Revolut", score: "A" },
  { name: "XE", score: "B" },
  { name: "Remitly", score: "B" },
  { name: "WorldRemit", score: "B" },
  { name: "Western Union", score: "D" },
  { name: "PayPal", score: "F" },
  { name: "Your Bank", score: "F" },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-50">
      {/* ───────── Nav ───────── */}
      <nav className="w-full border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-14">
          <span className="text-lg font-bold tracking-tight">
            Send<span className="text-emerald-600">Smart</span>
          </span>
          <div className="flex items-center gap-4 text-sm">
            <a
              href="/compare"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Compare
            </a>
            <a
              href="/predict"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Predict
            </a>
            <a
              href="/scan"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Scan Receipt
            </a>
          </div>
        </div>
      </nav>

      {/* ───────── Hero ───────── */}
      <section className="relative overflow-hidden">
        {/* Subtle gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50/60 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-emerald-100/30 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-16 pb-10 sm:pt-24 sm:pb-16">
          <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-14">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-100 text-emerald-700 px-3 py-1 text-xs font-medium mb-5">
              <Globe className="h-3.5 w-3.5" />
              Powered by World Bank &amp; ECB data
            </div>

            <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-zinc-900 leading-tight">
              Stop overpaying to{" "}
              <span className="text-emerald-600">send money home</span>
            </h1>

            <p className="mt-4 text-base sm:text-lg text-zinc-500 max-w-xl mx-auto leading-relaxed">
              Compare every transfer provider in seconds. See the fees they
              hide. Know exactly when to send.
            </p>
          </div>

          {/* The form */}
          <CompareForm />

          {/* Quick provider tags */}
          <div className="mt-8 flex flex-wrap justify-center gap-2">
            {PROVIDERS.map((p) => (
              <span
                key={p.name}
                className="inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-1 text-xs text-zinc-500"
              >
                {p.name}
                <span
                  className={`font-bold ${
                    p.score === "A"
                      ? "text-emerald-600"
                      : p.score === "B"
                        ? "text-blue-600"
                        : p.score === "D"
                          ? "text-orange-500"
                          : "text-red-500"
                  }`}
                >
                  {p.score}
                </span>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ───────── Stats ───────── */}
      <section className="border-y bg-white">
        <div className="max-w-6xl mx-auto px-6 py-12 sm:py-16">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
            {STATS.map((s) => (
              <div key={s.label} className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 mb-3">
                  <s.icon className="h-5 w-5" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-zinc-900">
                  {s.value}
                </div>
                <div className="text-sm text-zinc-600 mt-1">{s.label}</div>
                <div className="text-xs text-zinc-400 mt-0.5">
                  {s.sublabel}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ───────── How It Works ───────── */}
      <section className="max-w-6xl mx-auto px-6 py-16 sm:py-24">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-zinc-900">
            How it works
          </h2>
          <p className="text-zinc-500 mt-2">Three steps. Under 10 seconds.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {STEPS.map((step, i) => (
            <div key={step.title} className="relative group">
              <div className="rounded-2xl border bg-white p-6 h-full transition-shadow hover:shadow-md">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 font-bold text-sm">
                    {i + 1}
                  </div>
                  <step.icon className="h-5 w-5 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-zinc-900 text-lg mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-zinc-500 leading-relaxed">
                  {step.description}
                </p>
              </div>
              {/* Arrow connector (hidden on mobile, hidden on last) */}
              {i < STEPS.length - 1 && (
                <div className="hidden sm:flex absolute top-1/2 -right-5 -translate-y-1/2 text-zinc-300">
                  <ArrowRight className="h-5 w-5" />
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ───────── CTA ───────── */}
      <section className="bg-zinc-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold">
            Your family deserves every cent
          </h2>
          <p className="mt-3 text-zinc-400 max-w-lg mx-auto">
            281 million people send money home every year. On average, 6.49%
            disappears in fees. SendSmart shows you how to keep more.
          </p>
          <a
            href="/compare"
            className="inline-flex items-center gap-2 mt-8 bg-emerald-600 hover:bg-emerald-500 transition-colors text-white font-medium rounded-full px-6 py-3 text-sm"
          >
            Compare now
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </section>

      {/* ───────── Footer ───────── */}
      <footer className="border-t bg-white">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-400">
          <span>
            Send<span className="text-emerald-600 font-semibold">Smart</span>{" "}
            &mdash; HackEurope 2026
          </span>
          <span>
            Data from{" "}
            <span className="text-zinc-600">European Central Bank</span> &amp;{" "}
            <span className="text-zinc-600">World Bank RPW</span>
          </span>
        </div>
      </footer>
    </main>
  );
}
