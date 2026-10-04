import SQLite from 'react-native-sqlite-storage';

SQLite.enablePromise(true);

// Mirrors ARCHITECTURE.md §7.1's `observations` table (MVP subset — no
// multi-farmer/auth tonight, but the sync-queue-ready shape is kept so the
// Supabase mirror in §7.2 can be wired up later without a schema change).
const CREATE_OBSERVATIONS = `
  CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    crop_id TEXT NOT NULL,
    photo_uri TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    predicted_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    top_classes_json TEXT NOT NULL,
    below_threshold INTEGER NOT NULL,
    sync_status TEXT NOT NULL DEFAULT 'pending',
    gps_lat REAL,
    gps_lon REAL
  );
`;

// SQLite has no "ADD COLUMN IF NOT EXISTS" — for installs that created the
// table before gps_lat/gps_lon existed, add them and swallow the
// "duplicate column" error on every later launch.
const MIGRATIONS = [
  'ALTER TABLE observations ADD COLUMN gps_lat REAL',
  'ALTER TABLE observations ADD COLUMN gps_lon REAL',
];

let dbPromise: Promise<SQLite.SQLiteDatabase> | null = null;

function getDb(): Promise<SQLite.SQLiteDatabase> {
  if (!dbPromise) {
    dbPromise = SQLite.openDatabase({ name: 'leafscout.db', location: 'default' }).then(async (db) => {
      await db.executeSql(CREATE_OBSERVATIONS);
      for (const migration of MIGRATIONS) {
        try {
          await db.executeSql(migration);
        } catch {
          // column already exists — fine, this is just a new-column migration for older installs
        }
      }
      return db;
    });
  }
  return dbPromise;
}

export interface ObservationRecord {
  id: string;
  cropId: string;
  photoUri: string;
  capturedAt: string;
  predictedClass: string;
  confidence: number;
  topClasses: Record<string, number>;
  belowThreshold: boolean;
  syncStatus: 'pending' | 'synced' | 'failed';
  gpsLat: number | null;
  gpsLon: number | null;
}

function rowToRecord(row: any): ObservationRecord {
  return {
    id: row.id,
    cropId: row.crop_id,
    photoUri: row.photo_uri,
    capturedAt: row.captured_at,
    predictedClass: row.predicted_class,
    confidence: row.confidence,
    topClasses: JSON.parse(row.top_classes_json),
    belowThreshold: row.below_threshold === 1,
    syncStatus: row.sync_status,
    gpsLat: row.gps_lat ?? null,
    gpsLon: row.gps_lon ?? null,
  };
}

export async function saveObservation(record: ObservationRecord): Promise<void> {
  const db = await getDb();
  await db.executeSql(
    `INSERT INTO observations
      (id, crop_id, photo_uri, captured_at, predicted_class, confidence, top_classes_json, below_threshold, sync_status, gps_lat, gps_lon)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      record.id,
      record.cropId,
      record.photoUri,
      record.capturedAt,
      record.predictedClass,
      record.confidence,
      JSON.stringify(record.topClasses),
      record.belowThreshold ? 1 : 0,
      record.syncStatus,
      record.gpsLat,
      record.gpsLon,
    ],
  );
}

export async function listObservations(limit = 50): Promise<ObservationRecord[]> {
  const db = await getDb();
  const [result] = await db.executeSql(
    `SELECT * FROM observations ORDER BY captured_at DESC LIMIT ?`,
    [limit],
  );
  const rows: ObservationRecord[] = [];
  for (let i = 0; i < result.rows.length; i++) {
    rows.push(rowToRecord(result.rows.item(i)));
  }
  return rows;
}

export async function pendingSyncCount(): Promise<number> {
  const db = await getDb();
  const [result] = await db.executeSql(
    `SELECT COUNT(*) as n FROM observations WHERE sync_status = 'pending'`,
  );
  return result.rows.item(0).n as number;
}

export async function listPendingObservations(): Promise<ObservationRecord[]> {
  const db = await getDb();
  const [result] = await db.executeSql(
    `SELECT * FROM observations WHERE sync_status = 'pending' ORDER BY captured_at ASC`,
  );
  const rows: ObservationRecord[] = [];
  for (let i = 0; i < result.rows.length; i++) {
    rows.push(rowToRecord(result.rows.item(i)));
  }
  return rows;
}

export async function markObservationsSynced(ids: string[]): Promise<void> {
  if (ids.length === 0) return;
  const db = await getDb();
  const placeholders = ids.map(() => '?').join(',');
  await db.executeSql(
    `UPDATE observations SET sync_status = 'synced' WHERE id IN (${placeholders})`,
    ids,
  );
}
