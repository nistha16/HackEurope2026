import * as React from "react";
import Link from "next/link";
import { XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SubscriptionCancelPage() {
  return (
    <main className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center space-y-5">
        <div className="flex justify-center">
          <XCircle className="h-14 w-14 text-zinc-400" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Subscription cancelled
        </h1>
        <p className="text-muted-foreground text-sm">
          No charge was made. You can subscribe any time to unlock timing
          alerts, historical charts, and receipt scanning.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
            <Link href="/subscribe">Try again</Link>
          </Button>
          <Button asChild variant="outline" className="rounded-xl">
            <Link href="/compare">Back to Compare</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
