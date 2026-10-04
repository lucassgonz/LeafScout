// Manual Jest mock — native module, no Node binding. Always "denies" so
// getCurrentCoordinates() resolves to null, matching its documented
// best-effort behavior.
module.exports = {
  getCurrentPosition: jest.fn((_success, error) => error && error({ code: 1, message: 'mocked: denied' })),
  requestAuthorization: jest.fn(),
  setRNConfiguration: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
  stopObserving: jest.fn(),
};
