import { listPendingObservations, markObservationsSynced, type ObservationRecord } from '../../db/db';
import { supabase } from '../supabaseClient';
import { syncPendingObservations } from '../syncObservations';

jest.mock('../../db/db');
jest.mock('../supabaseClient', () => ({
  supabase: { from: jest.fn() },
}));

const mockedListPending = listPendingObservations as jest.MockedFunction<typeof listPendingObservations>;
const mockedMarkSynced = markObservationsSynced as jest.MockedFunction<typeof markObservationsSynced>;

function makeObservation(id: string): ObservationRecord {
  return {
    id,
    cropId: 'coffee',
    photoUri: 'file://leaf.jpg',
    capturedAt: '2026-10-04T00:00:00.000Z',
    predictedClass: 'rust',
    confidence: 0.8,
    topClasses: { rust: 0.8, healthy: 0.2 },
    belowThreshold: false,
    syncStatus: 'pending',
  };
}

describe('syncPendingObservations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('is a no-op when nothing is pending locally', async () => {
    mockedListPending.mockResolvedValue([]);

    const result = await syncPendingObservations();

    expect(result).toEqual({ attempted: 0, synced: 0 });
    expect(supabase.from).not.toHaveBeenCalled();
    expect(mockedMarkSynced).not.toHaveBeenCalled();
  });

  it('upserts every pending observation and marks them synced on success', async () => {
    mockedListPending.mockResolvedValue([makeObservation('a'), makeObservation('b')]);
    const upsert = jest.fn().mockResolvedValue({ error: null });
    (supabase.from as jest.Mock).mockReturnValue({ upsert });

    const result = await syncPendingObservations();

    expect(supabase.from).toHaveBeenCalledWith('observations');
    expect(upsert).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ id: 'a', crop_id: 'coffee', predicted_class: 'rust' }),
        expect.objectContaining({ id: 'b' }),
      ]),
      { onConflict: 'id' },
    );
    expect(mockedMarkSynced).toHaveBeenCalledWith(['a', 'b']);
    expect(result).toEqual({ attempted: 2, synced: 2 });
  });

  it('does not mark anything synced when the upsert fails (offline, RLS, etc.)', async () => {
    mockedListPending.mockResolvedValue([makeObservation('a')]);
    const upsert = jest.fn().mockResolvedValue({ error: { message: 'network request failed' } });
    (supabase.from as jest.Mock).mockReturnValue({ upsert });

    const result = await syncPendingObservations();

    expect(mockedMarkSynced).not.toHaveBeenCalled();
    expect(result.synced).toBe(0);
    expect(result.attempted).toBe(1);
    expect(result.error).toContain('network request failed');
  });

  it('never throws, even if the local DB read itself fails', async () => {
    mockedListPending.mockRejectedValue(new Error('disk full'));

    const result = await syncPendingObservations();

    expect(result.synced).toBe(0);
    expect(result.error).toContain('disk full');
  });
});
