export interface Provider {
  id: string;
  name: string;
  logo_url: string;
  fee_flat: number;
  fee_percent: number;
  fx_markup_percent: number;
  min_amount: number;
  max_amount: number;
  currencies: string[];
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

export interface MarketInsights {
  two_month_high: number;
  two_month_low: number;
  two_month_avg: number;
  one_year_trend: "UP" | "DOWN";
  volatility: "HIGH" | "MEDIUM" | "LOW";
}

export interface PredictionResponse {
  current_rate: number;
  timing_score: number;
  recommendation: "SEND_NOW" | "WAIT" | "NEUTRAL";
  reasoning: string;
  market_insights: MarketInsights;
  historical_rates: { date: string; rate: number }[];
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
  // Major
  { code: "EUR", name: "Euro", flag: "🇪🇺" },
  { code: "USD", name: "US Dollar", flag: "🇺🇸" },
  { code: "GBP", name: "British Pound", flag: "🇬🇧" },
  { code: "CAD", name: "Canadian Dollar", flag: "🇨🇦" },
  { code: "AUD", name: "Australian Dollar", flag: "🇦🇺" },
  { code: "NZD", name: "New Zealand Dollar", flag: "🇳🇿" },
  { code: "CHF", name: "Swiss Franc", flag: "🇨🇭" },
  { code: "JPY", name: "Japanese Yen", flag: "🇯🇵" },
  // Europe
  { code: "SEK", name: "Swedish Krona", flag: "🇸🇪" },
  { code: "NOK", name: "Norwegian Krone", flag: "🇳🇴" },
  { code: "DKK", name: "Danish Krone", flag: "🇩🇰" },
  { code: "PLN", name: "Polish Zloty", flag: "🇵🇱" },
  { code: "CZK", name: "Czech Koruna", flag: "🇨🇿" },
  { code: "HUF", name: "Hungarian Forint", flag: "🇭🇺" },
  { code: "RON", name: "Romanian Leu", flag: "🇷🇴" },
  { code: "BGN", name: "Bulgarian Lev", flag: "🇧🇬" },
  { code: "HRK", name: "Croatian Kuna", flag: "🇭🇷" },
  { code: "TRY", name: "Turkish Lira", flag: "🇹🇷" },
  { code: "RUB", name: "Russian Ruble", flag: "🇷🇺" },
  { code: "UAH", name: "Ukrainian Hryvnia", flag: "🇺🇦" },
  { code: "GEL", name: "Georgian Lari", flag: "🇬🇪" },
  // North Africa & Middle East
  { code: "MAD", name: "Moroccan Dirham", flag: "🇲🇦" },
  { code: "EGP", name: "Egyptian Pound", flag: "🇪🇬" },
  { code: "TND", name: "Tunisian Dinar", flag: "🇹🇳" },
  { code: "DZD", name: "Algerian Dinar", flag: "🇩🇿" },
  { code: "AED", name: "UAE Dirham", flag: "🇦🇪" },
  { code: "SAR", name: "Saudi Riyal", flag: "🇸🇦" },
  { code: "QAR", name: "Qatari Riyal", flag: "🇶🇦" },
  { code: "KWD", name: "Kuwaiti Dinar", flag: "🇰🇼" },
  { code: "BHD", name: "Bahraini Dinar", flag: "🇧🇭" },
  { code: "OMR", name: "Omani Rial", flag: "🇴🇲" },
  { code: "JOD", name: "Jordanian Dinar", flag: "🇯🇴" },
  { code: "ILS", name: "Israeli Shekel", flag: "🇮🇱" },
  { code: "LBP", name: "Lebanese Pound", flag: "🇱🇧" },
  // Sub-Saharan Africa
  { code: "NGN", name: "Nigerian Naira", flag: "🇳🇬" },
  { code: "KES", name: "Kenyan Shilling", flag: "🇰🇪" },
  { code: "GHS", name: "Ghanaian Cedi", flag: "🇬🇭" },
  { code: "ZAR", name: "South African Rand", flag: "🇿🇦" },
  { code: "TZS", name: "Tanzanian Shilling", flag: "🇹🇿" },
  { code: "UGX", name: "Ugandan Shilling", flag: "🇺🇬" },
  { code: "ETB", name: "Ethiopian Birr", flag: "🇪🇹" },
  { code: "XOF", name: "West African CFA Franc", flag: "🇸🇳" },
  { code: "XAF", name: "Central African CFA Franc", flag: "🇨🇲" },
  { code: "RWF", name: "Rwandan Franc", flag: "🇷🇼" },
  { code: "MZN", name: "Mozambican Metical", flag: "🇲🇿" },
  { code: "ZMW", name: "Zambian Kwacha", flag: "🇿🇲" },
  // South Asia
  { code: "INR", name: "Indian Rupee", flag: "🇮🇳" },
  { code: "PKR", name: "Pakistani Rupee", flag: "🇵🇰" },
  { code: "BDT", name: "Bangladeshi Taka", flag: "🇧🇩" },
  { code: "LKR", name: "Sri Lankan Rupee", flag: "🇱🇰" },
  { code: "NPR", name: "Nepalese Rupee", flag: "🇳🇵" },
  // East & Southeast Asia
  { code: "CNY", name: "Chinese Yuan", flag: "🇨🇳" },
  { code: "HKD", name: "Hong Kong Dollar", flag: "🇭🇰" },
  { code: "SGD", name: "Singapore Dollar", flag: "🇸🇬" },
  { code: "KRW", name: "South Korean Won", flag: "🇰🇷" },
  { code: "TWD", name: "Taiwan Dollar", flag: "🇹🇼" },
  { code: "THB", name: "Thai Baht", flag: "🇹🇭" },
  { code: "PHP", name: "Philippine Peso", flag: "🇵🇭" },
  { code: "IDR", name: "Indonesian Rupiah", flag: "🇮🇩" },
  { code: "MYR", name: "Malaysian Ringgit", flag: "🇲🇾" },
  { code: "VND", name: "Vietnamese Dong", flag: "🇻🇳" },
  { code: "MMK", name: "Myanmar Kyat", flag: "🇲🇲" },
  // Americas
  { code: "MXN", name: "Mexican Peso", flag: "🇲🇽" },
  { code: "BRL", name: "Brazilian Real", flag: "🇧🇷" },
  { code: "ARS", name: "Argentine Peso", flag: "🇦🇷" },
  { code: "CLP", name: "Chilean Peso", flag: "🇨🇱" },
  { code: "COP", name: "Colombian Peso", flag: "🇨🇴" },
  { code: "PEN", name: "Peruvian Sol", flag: "🇵🇪" },
  { code: "DOP", name: "Dominican Peso", flag: "🇩🇴" },
  { code: "GTQ", name: "Guatemalan Quetzal", flag: "🇬🇹" },
  { code: "HNL", name: "Honduran Lempira", flag: "🇭🇳" },
  { code: "JMD", name: "Jamaican Dollar", flag: "🇯🇲" },
  { code: "TTD", name: "Trinidad Dollar", flag: "🇹🇹" },
  { code: "UYU", name: "Uruguayan Peso", flag: "🇺🇾" },
  // Oceania
  { code: "FJD", name: "Fijian Dollar", flag: "🇫🇯" },
];
