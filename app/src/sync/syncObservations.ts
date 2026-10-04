import { listPendingObservations, markObservationsSynced } from '../db/db';
import { supabase } from './supabaseClient';

// The shared TFLite backbone + per-crop SVM heads version currently bundled
// in the app — matches model_registry.version for this build (see
// model/artifacts/model_registry.json and supabase/schema.sql). Bump this
// string whenever you re-copy freshly retrained artifacts into assets/model/.
export const MODEL_VERSION = 'v1-2026-10-04';

export interface SyncResult {
  attempted: number;
  synced: number;
  error?: string;
}

/**
 * Best-effort, offline-first sync: reads every locally pending observation
 * and upserts it to Supabase. Never throws — a flaky/absent connection is
 * the expected common case (see ARCHITECTURE.md §3), not an error to
 * surface to the farmer. Call this after each save and optimistically on
 * app foreground; it's cheap and a no-op when there's nothing pending.
 *
 * Photos are NOT uploaded here — only observation metadata. Photo upload to
 * Supabase Storage needs an explicit consent + good-connection gate per
 * ARCHITECTURE.md §7.2 ("never force a large upload over a 3G bundle") and
 * is intentionally out of scope for this pass.
 */
export async function syncPendingObservations(): Promise<SyncResult> {
  let pending: Awaited<ReturnType<typeof listPendingObservations>>;
  try {
    pending = await listPendingObservations();
  } catch (err) {
    return { attempted: 0, synced: 0, error: `local read failed: ${String(err)}` };
  }

  if (pending.length === 0) {
    return { attempted: 0, synced: 0 };
  }

  const rows = pending.map((obs) => ({
    id: obs.id,
    crop_id: obs.cropId,
    captured_at: obs.capturedAt,
    model_version: MODEL_VERSION,
    predicted_class: obs.predictedClass,
    confidence: obs.confidence,
    top3_json: obs.topClasses,
    below_threshold: obs.belowThreshold,
    gps_lat: obs.gpsLat,
    gps_lon: obs.gpsLon,
  }));

  const { error } = await supabase.from('observations').upsert(rows, { onConflict: 'id' });
  if (error) {
    // Expected and common: offline, DNS failure, RLS denial if the schema
    // ever changes underneath the app. Swallow it — the data is safe
    // locally and will retry next time this is called.
    return { attempted: pending.length, synced: 0, error: error.message };
  }

  await markObservationsSynced(pending.map((obs) => obs.id));
  return { attempted: pending.length, synced: pending.length };
}
