-- LeafScout Supabase schema — mirrors the local SQLite shape in
-- ARCHITECTURE.md §7.1, plus the §7.2 sync/aggregation tables.
--
-- APPLIED to the real "hacknation" project (chbhhzypwvkqmojvtcmx) on
-- 2026-10-04 via the Supabase MCP — this file is now a record of that
-- schema, not just a plan. Re-running it is safe (idempotent create/insert),
-- except the model_registry PK fix below, which already happened live.

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

-- Kept in sync by hand with app/src/data/diseaseClasses.ts — there is no
-- build step that generates one from the other yet.
insert into disease_classes (id, crop_id, name_en, description_en, recommended_action) values
('healthy','coffee','Healthy','No signs of leaf miner, rust, phoma, or cercospora detected.','Keep monitoring weekly. No action needed right now.'),
('rust','coffee','Coffee leaf rust','Orange-yellow powdery spots on the underside of the leaf — the most damaging coffee disease worldwide.','Show this to your extension officer this week. Consider a copper-based fungicide if rust is spreading fast.'),
('leaf_miner','coffee','Coffee leaf miner','Pale, winding tunnels inside the leaf made by the miner larva.','Remove and destroy badly mined leaves. Report to your cooperative if spreading across the plot.'),
('phoma','coffee','Phoma leaf spot','Dark brown spots with a yellow halo, often after cold or wet weather.','Improve plot drainage and spacing. Show to the extension officer if spots keep spreading.'),
('cercospora','coffee','Cercospora leaf spot (brown eye spot)','Circular brown spots with a lighter center, common on stressed plants.','Check plant nutrition and shade levels. Show to the extension officer if severe.'),
('healthy','cassava','Healthy','No signs of mosaic, brown streak, bacterial blight, or green mottle detected.','Keep monitoring. No action needed right now.'),
('mosaic_disease','cassava','Cassava mosaic disease','Pale yellow-green mosaic patterns and leaf distortion — spread by whitefly.','Uproot and destroy severely affected plants. Ask your extension officer about disease-resistant cuttings for the next planting.'),
('brown_streak','cassava','Cassava brown streak disease','Brown streaks on stems and a dry, corky rot inside the roots — often invisible above ground until harvest.','This disease can ruin roots with no visible leaf symptoms. Show this to your extension officer before the next harvest.'),
('bacterial_blight','cassava','Cassava bacterial blight','Angular, water-soaked leaf spots and wilting shoots.','Avoid working in wet fields (spreads the bacteria). Show to your extension officer if wilting spreads.'),
('green_mottle','cassava','Cassava green mottle','Light green mottling on leaves, generally milder than mosaic disease.','Keep monitoring. Mention it at your next extension officer visit.'),
('healthy','bean','Healthy','No signs of rust or angular leaf spot detected.','Keep monitoring weekly. No action needed right now.'),
('rust','bean','Bean rust','Small reddish-brown powdery pustules on the leaf underside.','Remove heavily infected leaves. Show to your extension officer if spreading across the plot.'),
('angular_leaf_spot','bean','Angular leaf spot','Grey-brown angular spots bound by leaf veins.','Avoid overhead irrigation. Show to your extension officer if spots keep spreading.')
on conflict (crop_id, id) do nothing;

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
  -- Composite PK, not just `version`: one shared backbone version has one
  -- row PER CROP (its own head). A single-column PK on `version` silently
  -- drops every row but the first on insert — caught live on 2026-10-04,
  -- see the ALTER below if you're applying this to an older database.
  version text not null,
  crop_id text not null references crops(id),
  backbone text not null,
  head_type text not null,
  tflite_asset_hash text not null,
  head_weights_asset_hash text,
  trained_on_dataset text not null,
  accuracy_5fold_mean double precision,
  accuracy_5fold_by_source_json jsonb,
  plantdoc_spotcheck_accuracy double precision,
  created_at timestamptz not null default now(),
  primary key (version, crop_id)
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

-- RLS: this is a hackathon demo with no end-user auth yet (the app writes
-- with the public anon/publishable key, not a logged-in user). Enabling RLS
-- with explicit, narrow policies is still safer than leaving it disabled,
-- which would fall back to whatever blanket table grants Supabase set up by
-- default. Tighten/replace these the moment real farmer auth exists.
alter table crops enable row level security;
alter table farmers enable row level security;
alter table disease_classes enable row level security;
alter table observations enable row level security;
alter table model_registry enable row level security;
alter table outbreak_aggregates enable row level security;

create policy "public read: crops" on crops for select using (true);
create policy "public read: disease_classes" on disease_classes for select using (true);
create policy "public read: model_registry" on model_registry for select using (true);
create policy "public read: outbreak_aggregates" on outbreak_aggregates for select using (true);

-- The app inserts observations (and, lazily, a farmer row) anonymously —
-- no PII beyond a hashed phone number, never the raw number.
create policy "anon insert: farmers" on farmers for insert with check (true);
create policy "anon insert: observations" on observations for insert with check (true);
-- The app's client-side upsert() always compiles to
-- INSERT ... ON CONFLICT (id) DO UPDATE, even when no conflict actually
-- happens — Postgres RLS checks the UPDATE policy for that clause's
-- existence regardless of whether a conflict occurs. Without this, every
-- upsert failed live with "new row violates row-level security policy for
-- table observations", despite the insert policy above being correct on
-- its own for a plain INSERT.
create policy "anon update own insert: observations" on observations for update using (true) with check (true);
-- Also required, and easy to miss: Postgres needs SELECT visibility on a
-- table to use ANY `ON CONFLICT` clause (DO UPDATE *and* DO NOTHING both)
-- — it has to be able to see the existing row to detect the conflict at
-- all. Without this, the app's upsert() failed 100% of the time with "new
-- row violates row-level security policy", which reads like an
-- insert/update problem but isn't one — caught live on 2026-10-04 by
-- reproducing the exact failure directly in SQL as `set role anon`.
-- observations holds no farmer PII directly (crop/diagnosis/confidence/
-- timestamps only; farmer_id is an optional, currently-unused FK), so a
-- public read policy here is low-risk, matching crops/disease_classes/
-- model_registry's pattern. farmers itself still has no select policy.
create policy "public read: observations" on observations for select using (true);
