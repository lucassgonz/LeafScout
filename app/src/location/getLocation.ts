import Geolocation from '@react-native-community/geolocation';

export interface Coordinates {
  lat: number;
  lon: number;
}

/**
 * Best-effort current position — GPS is optional everywhere in this app
 * (see ARCHITECTURE.md §7.1: "nullable, GPS may be off/unavailable"). Never
 * throws and never blocks the diagnosis flow waiting on a slow GPS fix:
 * resolves to `null` on denial, timeout, or any error.
 */
export async function getCurrentCoordinates(timeoutMs = 8000): Promise<Coordinates | null> {
  return new Promise((resolve) => {
    try {
      Geolocation.getCurrentPosition(
        (position) => {
          resolve({ lat: position.coords.latitude, lon: position.coords.longitude });
        },
        () => resolve(null), // permission denied, location off, or any platform error
        { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 60_000 },
      );
    } catch {
      resolve(null); // a native module throwing synchronously is still "no location available"
    }
  });
}
