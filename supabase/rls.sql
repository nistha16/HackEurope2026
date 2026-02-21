-- Run this in Supabase Dashboard → SQL Editor AFTER schema.sql

-- Enable RLS on all user-owned tables
alter table profiles enable row level security;
alter table comparisons enable row level security;
alter table rate_alerts enable row level security;
alter table scanned_receipts enable row level security;

-- profiles: users can only read/update their own profile
create policy "profiles: select own" on profiles
  for select using (auth.uid() = id);

create policy "profiles: insert own" on profiles
  for insert with check (auth.uid() = id);

create policy "profiles: update own" on profiles
  for update using (auth.uid() = id);

-- comparisons: users can only read/write their own
create policy "comparisons: select own" on comparisons
  for select using (auth.uid() = user_id);

create policy "comparisons: insert own" on comparisons
  for insert with check (auth.uid() = user_id);

-- rate_alerts: users can only CRUD their own alerts
create policy "rate_alerts: select own" on rate_alerts
  for select using (auth.uid() = user_id);

create policy "rate_alerts: insert own" on rate_alerts
  for insert with check (auth.uid() = user_id);

create policy "rate_alerts: update own" on rate_alerts
  for update using (auth.uid() = user_id);

create policy "rate_alerts: delete own" on rate_alerts
  for delete using (auth.uid() = user_id);

-- scanned_receipts: users can only read/write their own
create policy "scanned_receipts: select own" on scanned_receipts
  for select using (auth.uid() = user_id);

create policy "scanned_receipts: insert own" on scanned_receipts
  for insert with check (auth.uid() = user_id);

-- providers table is public read (no RLS needed — it's reference data)
