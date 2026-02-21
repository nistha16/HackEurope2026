-- Run this in Supabase Dashboard → SQL Editor

create table profiles (
  id uuid primary key references auth.users,
  full_name text,
  email text,
  stripe_customer_id text,
  preferred_corridors jsonb default '[]',
  created_at timestamptz default now()
);

create table providers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  logo_url text,
  fee_flat decimal(10,2) default 0,
  fee_percent decimal(5,3) default 0,
  fx_markup_percent decimal(5,3) default 0,
  speed_hours int,
  min_amount decimal(10,2),
  max_amount decimal(10,2),
  supported_corridors jsonb,
  transparency_score text,
  website_url text
);

create table comparisons (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users,
  source_currency text not null,
  target_currency text not null,
  amount decimal(10,2) not null,
  results jsonb not null,
  best_provider text,
  potential_savings decimal(10,2),
  created_at timestamptz default now()
);

create table rate_alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  source_currency text not null,
  target_currency text not null,
  target_rate decimal(10,6),
  is_active boolean default true,
  created_at timestamptz default now()
);

create table scanned_receipts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users,
  provider_name text,
  amount_sent decimal(10,2),
  amount_received decimal(10,2),
  fee_paid decimal(10,2),
  rate_used decimal(10,6),
  overpay_amount decimal(10,2),
  created_at timestamptz default now()
);
