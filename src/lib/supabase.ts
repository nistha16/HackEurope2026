import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Browser client — uses anon key, respects RLS.
// Safe to use in client components. Singleton to avoid multiple instances.
let browserClient: ReturnType<typeof createClient> | null = null;

export function getSupabaseBrowserClient() {
  if (!browserClient) {
    browserClient = createClient(supabaseUrl, supabaseAnonKey);
  }
  return browserClient;
}

// Server client — uses service role key, bypasses RLS.
// Only use in API routes / server actions. Never expose to the browser.
// Key is read lazily so client components importing this file don't
// attempt to access SUPABASE_SERVICE_ROLE_KEY (undefined in browser).
export function getSupabaseServerClient() {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
  return createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  });
}
