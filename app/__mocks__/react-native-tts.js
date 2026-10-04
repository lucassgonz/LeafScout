// Manual Jest mock — native module (AVSpeechSynthesizer/Android TTS), no
// Node binding.
module.exports = {
  setDefaultLanguage: jest.fn(async () => 'success'),
  setDefaultRate: jest.fn(async () => 'success'),
  speak: jest.fn(() => 0),
  stop: jest.fn(async () => true),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};
