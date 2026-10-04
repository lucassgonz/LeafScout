-- LeafScout Supabase schema — mirrors the local SQLite shape in
-- ARCHITECTURE.md §7.1, plus the §7.2 sync/aggregation tables.
-- NOT applied yet (no DB password was shared) — paste this into
-- Supabase Studio > SQL Editor > New query > Run. One-time, ~10 seconds.
-- Not required for the offline core loop or for recording the demo video.

create table if not exists crops (
  id text primary key,
  name_en text not null
);

insert into crops (id, name_en) values
  ('coffee', 'Coffee (Arabica)'),
  ('cassava', 'Cassava'),
  ('bean', 'Common bean')
on conflict (id) do nothing;

create table if not exists farmers (
  id uuid primary key default gen_random_uuid(),
  phone_hash text,
  language_pref text not null default 'en',
  primary_crop_id text references crops(id),
  coop_id text,
  created_at timestamptz not null default now()
);

create table if not exists disease_classes (
  id text not null,
  crop_id text not null references crops(id),
  name_en text not null,
  name_local text,
  description_en text,
  recommended_action text,
  audio_clip_asset text,
  primary key (crop_id, id)
);

create table if not exists observations (
  id uuid primary key default gen_random_uuid(),
  farmer_id uuid references farmers(id),
  crop_id text not null references crops(id),
  photo_storage_path text,
  captured_at timestamptz not null,
  gps_lat double precision,
  gps_lon double precision,
  model_version text not null,
  predicted_class text not null,
  confidence double precision not null,
  top3_json jsonb,
  below_threshold boolean not null default false,
  human_confirmed_class text,
  synced_at timestamptz not null default now()
);

create table if not exists model_registry (
  version text primary key,
  backbone text not null,
  crop_id text not null references crops(id),
  head_type text not null,
  tflite_asset_hash text not null,
  head_weights_asset_hash text,
  trained_on_dataset text not null,
  accuracy_5fold_mean double precision,
  accuracy_5fold_by_source_json jsonb,
  plantdoc_spotcheck_accuracy double precision,
  created_at timestamptz not null default now()
);

create table if not exists outbreak_aggregates (
  id uuid primary key default gen_random_uuid(),
  coop_id text not null,
  crop_id text not null references crops(id),
  disease_id text not null,
  week_start date not null,
  observation_count integer not null,
  avg_confidence double precision,
  unique (coop_id, crop_id, disease_id, week_start)
);

-- Row Level Security: enable before putting real farmer data in this
-- project. Left off for now since nothing is wired up to write here yet —
-- turn this on as the very first step when you do connect the sync job.
-- alter table observations enable row level security;
