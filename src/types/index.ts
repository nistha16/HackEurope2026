export interface Provider {
  id: string;
  name: string;
  logo_url: string;
  fee_flat: number;
  fee_percent: number;
  fx_markup_percent: number;
  speed_hours: number;
  min_amount: number;
  max_amount: number;
  source_currencies: string[];
  target_currencies: string[];
  transparency_score: "A" | "B" | "C" | "D" | "F";
  website_url: string;
}

export interface ComparisonResult {
  provider: Provider;
  send_amount: number;
  flat_fee: number;
  percent_fee: number;
  fx_markup_cost: number;
  total_fee: number;
  exchange_rate: number;
  provider_rate: number;
  recipient_gets: number;
  hidden_cost: number;
  total_real_cost: number;
  transparency_score: "A" | "B" | "C" | "D" | "F";
}

export interface ComparisonRequest {
  source_currency: string;
  target_currency: string;
  amount: number;
}

export interface ComparisonResponse {
  results: ComparisonResult[];
  mid_market_rate: number;
  source_currency: string;
  target_currency: string;
  amount: number;
  best_provider: string;
  potential_savings: number;
  timestamp: string;
}

export interface PredictionResponse {
  current_rate: number;
  predicted_rate_24h: number;
  predicted_rate_72h: number;
  confidence: number;
  recommendation: "SEND_NOW" | "WAIT" | "NEUTRAL";
  potential_savings: string;
  reasoning: string;
  historical_rates: { date: string; rate: number }[];
  predicted_rates: { date: string; rate: number }[];
}

export interface ReceiptScanResult {
  provider_name: string;
  amount_sent: number;
  currency_sent: string;
  amount_received: number;
  currency_received: string;
  fee_paid: number;
  rate_used: number;
  date: string;
  overpay_amount: number;
  best_alternative_cost: number;
  best_alternative_provider: string;
}

export interface RateAlert {
  id: string;
  source_currency: string;
  target_currency: string;
  target_rate: number;
  is_active: boolean;
  created_at: string;
}

export interface CurrencyOption {
  code: string;
  name: string;
  flag: string;
}

export const CURRENCIES: CurrencyOption[] = [
  { code: "EUR", name: "Euro", flag: "🇪🇺" },
  { code: "USD", name: "US Dollar", flag: "🇺🇸" },
  { code: "GBP", name: "British Pound", flag: "🇬🇧" },
  { code: "MAD", name: "Moroccan Dirham", flag: "🇲🇦" },
  { code: "INR", name: "Indian Rupee", flag: "🇮🇳" },
  { code: "PHP", name: "Philippine Peso", flag: "🇵🇭" },
  { code: "NGN", name: "Nigerian Naira", flag: "🇳🇬" },
  { code: "PKR", name: "Pakistani Rupee", flag: "🇵🇰" },
  { code: "BDT", name: "Bangladeshi Taka", flag: "🇧🇩" },
  { code: "MXN", name: "Mexican Peso", flag: "🇲🇽" },
  { code: "EGP", name: "Egyptian Pound", flag: "🇪🇬" },
  { code: "TRY", name: "Turkish Lira", flag: "🇹🇷" },
  { code: "BRL", name: "Brazilian Real", flag: "🇧🇷" },
  { code: "CAD", name: "Canadian Dollar", flag: "🇨🇦" },
  { code: "AUD", name: "Australian Dollar", flag: "🇦🇺" },
  { code: "JPY", name: "Japanese Yen", flag: "🇯🇵" },
  { code: "CNY", name: "Chinese Yuan", flag: "🇨🇳" },
  { code: "KES", name: "Kenyan Shilling", flag: "🇰🇪" },
  { code: "GHS", name: "Ghanaian Cedi", flag: "🇬🇭" },
  { code: "ZAR", name: "South African Rand", flag: "🇿🇦" },
];
