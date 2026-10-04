// Manual Jest mock for the native SQLite module — see
// react-native-fast-tflite.js mock in this folder for why this exists.
// Keeps a real in-memory array so src/db/db.ts's logic (insert/list/count)
// is still meaningfully exercised, not just stubbed to no-ops.
const rows = [];

function makeResult() {
  return {
    rows: {
      length: rows.length,
      item: (i) => rows[rows.length - 1 - i], // DESC order, matches the real query
    },
  };
}

const mockDb = {
  executeSql: jest.fn(async (sql, params = []) => {
    if (sql.startsWith('INSERT')) {
      const [id, crop_id, photo_uri, captured_at, predicted_class, confidence, top_classes_json, below_threshold, sync_status, gps_lat, gps_lon] = params;
      rows.push({ id, crop_id, photo_uri, captured_at, predicted_class, confidence, top_classes_json, below_threshold, sync_status, gps_lat, gps_lon });
      return [makeResult()];
    }
    if (sql.startsWith('SELECT COUNT')) {
      const n = rows.filter((r) => r.sync_status === 'pending').length;
      return [{ rows: { item: () => ({ n }) } }];
    }
    return [makeResult()];
  }),
};

module.exports = {
  enablePromise: jest.fn(),
  openDatabase: jest.fn(async () => mockDb),
};
