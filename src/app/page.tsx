"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { CompareForm } from "@/components/compareForm";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Search,
  ShieldCheck,
  TrendingUp,
  Globe,
  DollarSign,
  Users,
  BadgePercent,
  Camera,
  Mic,
} from "lucide-react";

/* ─── Data ─── */

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
      "We compare the real cost - not the advertised one. FX markups, flat fees, everything exposed.",
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
    value: 905,
    prefix: "$",
    suffix: "B",
    label: "Sent home globally",
    sublabel: "World Bank, 2024",
  },
  {
    icon: Users,
    value: 281,
    suffix: "M",
    label: "Migrants worldwide",
    sublabel: "IOM, 2020 est.",
  },
  {
    icon: BadgePercent,
    value: 6.49,
    suffix: "%",
    label: "Average transfer cost",
    sublabel: "World Bank RPW, 2024",
  },
  {
    icon: Globe,
    value: 8,
    label: "Providers compared",
    sublabel: "Real-time rates",
  },
];

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Hidden Fee Detector",
    description:
      "We calculate the real exchange rate markup providers hide. See your A-F transparency score instantly.",
    href: "/compare",
  },
  {
    icon: TrendingUp,
    title: "Send Now or Wait?",
    description:
      "ML predictions trained on 25 years of ECB data. Know if waiting a day could save you money.",
    href: "/predict",
  },
  {
    icon: Camera,
    title: "Receipt Scanner",
    description:
      "Scan an old transfer receipt with Gemini AI. We show exactly how much you overpaid.",
    href: "/scan",
  },
  {
    icon: Mic,
    title: "Voice Assistant",
    description:
      "Ask in plain language: \"Send 500 euros to Morocco.\" Get the best option read back to you.",
    href: "/voice",
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

/* ─── Animation variants ─── */

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } },
};

/* ─── Animated counter ─── */

function AnimatedNumber({
  value,
  prefix = "",
  suffix = "",
}: {
  value: number;
  prefix?: string;
  suffix?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState("0");
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          const isDecimal = value % 1 !== 0;
          const duration = 1200;
          const start = performance.now();

          const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = eased * value;
            setDisplay(isDecimal ? current.toFixed(2) : Math.round(current).toString());
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [value]);

  return (
    <span ref={ref}>
      {prefix}
      {display}
      {suffix}
    </span>
  );
}

/* ─── Page ─── */

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-50">
      <Navbar />

      {/* ───────── Hero ───────── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50/60 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-emerald-100/30 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-16 pb-10 sm:pt-24 sm:pb-16">
          <motion.div
            className="text-center max-w-2xl mx-auto mb-10 sm:mb-14"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
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
          </motion.div>

          <CompareForm />

          {/* Quick provider tags */}
          <motion.div
            className="mt-8 flex flex-wrap justify-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
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
          </motion.div>
        </div>
      </section>

      {/* ───────── Stats ───────── */}
      <section className="border-y bg-white">
        <div className="max-w-6xl mx-auto px-6 py-12 sm:py-16">
          <motion.div
            className="grid grid-cols-2 sm:grid-cols-4 gap-8"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
          >
            {STATS.map((s) => (
              <motion.div key={s.label} className="text-center" variants={fadeUp}>
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 mb-3">
                  <s.icon className="h-5 w-5" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-zinc-900">
                  <AnimatedNumber
                    value={s.value}
                    prefix={s.prefix}
                    suffix={s.suffix}
                  />
                </div>
                <div className="text-sm text-zinc-600 mt-1">{s.label}</div>
                <div className="text-xs text-zinc-400 mt-0.5">{s.sublabel}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ───────── How It Works ───────── */}
      <section className="max-w-6xl mx-auto px-6 py-16 sm:py-24">
        <motion.div
          className="text-center mb-12"
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-zinc-900">
            How it works
          </h2>
          <p className="text-zinc-500 mt-2">Three steps. Under 10 seconds.</p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 sm:grid-cols-3 gap-8"
          variants={stagger}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
        >
          {STEPS.map((step, i) => (
            <motion.div key={step.title} className="relative group" variants={fadeUp}>
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
              {i < STEPS.length - 1 && (
                <div className="hidden sm:flex absolute top-1/2 -right-5 -translate-y-1/2 text-zinc-300">
                  <ArrowRight className="h-5 w-5" />
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ───────── Features ───────── */}
      <section className="border-y bg-white">
        <div className="max-w-6xl mx-auto px-6 py-16 sm:py-24">
          <motion.div
            className="text-center mb-12"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-zinc-900">
              Built for transparency
            </h2>
            <p className="text-zinc-500 mt-2">
              Every tool you need to make the smartest transfer.
            </p>
          </motion.div>

          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 gap-6"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
          >
            {FEATURES.map((f) => (
              <motion.div key={f.title} variants={fadeUp}>
                <Link href={f.href} className="block group">
                  <div className="rounded-2xl border bg-zinc-50 p-6 h-full transition-all hover:shadow-md hover:border-emerald-200 hover:bg-white">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600">
                        <f.icon className="h-5 w-5" />
                      </div>
                      <h3 className="font-semibold text-zinc-900">{f.title}</h3>
                    </div>
                    <p className="text-sm text-zinc-500 leading-relaxed">
                      {f.description}
                    </p>
                    <div className="mt-4 flex items-center gap-1 text-sm text-emerald-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      Try it <ArrowRight className="h-3.5 w-3.5" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ───────── CTA ───────── */}
      <section className="bg-zinc-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20 text-center">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold">
              Your family deserves every cent
            </h2>
            <p className="mt-3 text-zinc-400 max-w-lg mx-auto">
              $905 billion was sent home globally in 2024. On average, 6.49%
              disappears in fees. FibreTransfer shows you how to keep more.
            </p>
            <div className="mt-8">
              <Button
                asChild
                size="lg"
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-8"
              >
                <Link href="/compare">
                  Compare Now <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ───────── Footer ───────── */}
      <footer className="border-t bg-white">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-400">
          <span>
            Fibre
            <span className="text-emerald-600 font-semibold">Transfer</span> -
            HackEurope 2026
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
