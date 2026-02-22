"use client";

import * as React from "react";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import type { ReceiptScanResult } from "@/types";
import {
  Upload,
  Camera,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  X,
} from "lucide-react";

/* ─── Result card ─── */

function ScanResultCard({ result }: { result: ReceiptScanResult }) {
  const hasSavings = result.overpay_amount > 0;

  return (
    <div className="space-y-4">
      {/* Overpay banner */}
      {hasSavings ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-amber-800">
              You overpaid by{" "}
              <span className="text-lg">
                {result.currency_sent} {result.overpay_amount.toFixed(2)}
              </span>
            </p>
            <p className="text-sm text-amber-700 mt-1">
              The cheapest option was{" "}
              <span className="font-medium">{result.best_alternative_provider}</span>{" "}
              (total cost: {result.currency_sent}{" "}
              {result.best_alternative_cost.toFixed(2)}).
            </p>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
          <p className="font-semibold text-emerald-800">
            Good news — you got a competitive deal!
          </p>
        </div>
      )}

      {/* Details */}
      <div className="rounded-2xl border bg-white p-5 sm:p-6 space-y-4">
        <h3 className="font-semibold text-zinc-900">Receipt Details</h3>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-zinc-400">Provider</p>
            <p className="font-medium text-zinc-900">{result.provider_name}</p>
          </div>
          <div>
            <p className="text-zinc-400">Date</p>
            <p className="font-medium text-zinc-900">{result.date}</p>
          </div>
          <div>
            <p className="text-zinc-400">Amount Sent</p>
            <p className="font-medium text-zinc-900">
              {result.currency_sent} {result.amount_sent.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-zinc-400">Amount Received</p>
            <p className="font-medium text-zinc-900">
              {result.currency_received}{" "}
              {result.amount_received.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-zinc-400">Fee Paid</p>
            <p className="font-medium text-zinc-900">
              {result.currency_sent} {result.fee_paid.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-zinc-400">Exchange Rate</p>
            <p className="font-medium text-zinc-900">
              {result.rate_used.toFixed(4)}
            </p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center">
        <Button
          asChild
          className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl px-6"
        >
          <a href="/compare">
            Compare providers now <ArrowRight className="ml-2 h-4 w-4" />
          </a>
        </Button>
      </div>
    </div>
  );
}

/* ─── Main page ─── */

export default function ScanPage() {
  const [preview, setPreview] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ReceiptScanResult | null>(null);
  const fileRef = React.useRef<HTMLInputElement>(null);

  function handleFile(file: File) {
    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file (JPEG, PNG, etc.)");
      return;
    }
    if (file.size > 7.5 * 1024 * 1024) {
      setError("Image too large. Maximum size is 7.5 MB.");
      return;
    }

    setError(null);
    setResult(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      setPreview(dataUrl);
    };
    reader.readAsDataURL(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function clearImage() {
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleScan() {
    if (!preview) return;
    setLoading(true);
    setError(null);
    try {
      // Extract base64 from data URL (remove "data:image/...;base64," prefix)
      const base64 = preview.split(",")[1];
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: base64 }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || `Request failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      <Navbar />

      <div className="max-w-2xl mx-auto px-4 py-10 sm:py-14 space-y-8">
        {/* Header */}
        <div className="text-center space-y-1">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900">
            Receipt Scanner
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Upload an old transfer receipt — Gemini AI extracts the details and
            shows how much you overpaid.
          </p>
        </div>

        {/* Upload area */}
        {!preview ? (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className="rounded-2xl border-2 border-dashed border-zinc-300 bg-white hover:border-emerald-400 hover:bg-emerald-50/30 transition-colors cursor-pointer p-10 text-center space-y-3"
          >
            <div className="mx-auto w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Upload className="h-6 w-6" />
            </div>
            <p className="font-medium text-zinc-700">
              Drop your receipt here, or click to browse
            </p>
            <p className="text-xs text-zinc-400">
              Supports JPEG, PNG — max 7.5 MB
            </p>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleInputChange}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Preview */}
            <div className="relative rounded-2xl border bg-white overflow-hidden">
              <button
                onClick={clearImage}
                className="absolute top-3 right-3 p-1.5 rounded-full bg-white/80 hover:bg-white border shadow-sm"
              >
                <X className="h-4 w-4 text-zinc-600" />
              </button>
              <img
                src={preview}
                alt="Receipt preview"
                className="w-full max-h-96 object-contain bg-zinc-100"
              />
            </div>

            {/* Scan button */}
            {!result && (
              <Button
                onClick={handleScan}
                disabled={loading}
                className="w-full h-12 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Scanning with Gemini...
                  </>
                ) : (
                  <>
                    <Camera className="mr-2 h-4 w-4" />
                    Scan Receipt
                  </>
                )}
              </Button>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Results */}
        {result && <ScanResultCard result={result} />}
      </div>
    </main>
  );
}
