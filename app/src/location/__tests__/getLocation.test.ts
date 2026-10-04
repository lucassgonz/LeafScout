import Geolocation from '@react-native-community/geolocation';
import { getCurrentCoordinates } from '../getLocation';

describe('getCurrentCoordinates', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('resolves to coordinates on success', async () => {
    jest.spyOn(Geolocation, 'getCurrentPosition').mockImplementation((success: any) => {
      success({ coords: { latitude: -15.78, longitude: -47.93 } });
    });

    const coords = await getCurrentCoordinates();
    expect(coords).toEqual({ lat: -15.78, lon: -47.93 });
  });

  it('resolves to null when the platform reports an error (denied, GPS off, etc.)', async () => {
    jest.spyOn(Geolocation, 'getCurrentPosition').mockImplementation((_success: any, error: any) => {
      error({ code: 1, message: 'denied' });
    });

    const coords = await getCurrentCoordinates();
    expect(coords).toBeNull();
  });

  it('resolves to null (not a rejected promise) if the native call throws synchronously', async () => {
    jest.spyOn(Geolocation, 'getCurrentPosition').mockImplementation(() => {
      throw new Error('native crash');
    });

    await expect(getCurrentCoordinates()).resolves.toBeNull();
  });
});
