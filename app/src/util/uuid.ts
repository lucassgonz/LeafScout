// Minimal UUID v4 generator — no crypto.randomUUID dependency (not
// guaranteed available in Hermes), no extra native/polyfill package.
// Not cryptographically strong (Math.random-backed); fine for a local
// observation id that only needs to be unique enough to upsert on, not
// secret or collision-proof against an adversary.
export function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
