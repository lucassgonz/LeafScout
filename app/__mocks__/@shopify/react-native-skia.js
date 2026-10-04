// Manual Jest mock — Skia is a native C++ module with no Node/Jest binding.
// Only the surface src/ml/imagePreprocess.ts actually touches is stubbed.
module.exports = {
  ColorType: { RGBA_8888: 4 },
  AlphaType: { Unpremul: 3 },
  Skia: {
    Data: { fromURI: jest.fn(async () => ({})) },
    Image: { MakeImageFromEncoded: jest.fn(() => null) },
    Surface: { MakeOffscreen: jest.fn(() => null) },
    Paint: jest.fn(() => ({})),
    XYWHRect: jest.fn((x, y, width, height) => ({ x, y, width, height })),
  },
};
